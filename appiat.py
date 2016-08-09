#!/usr/bin/env python
import fileinput
import argparse

###
# just some basic background preparations before the actual cooking starts...
###
parser = argparse.ArgumentParser(description="Given input data as file arguments or as input piped from another program,\
        try to generate a program that can capture such kinds of data and persist them...")
group = parser.add_mutually_exclusive_group()
group.add_argument("-q", "--quiet", action="store_true")
args, unknown_args = parser.parse_known_args()

BE_SILENT = args.quiet

#****
# Some utils...
#****

def debug(msg, title):
    print "%(d)s\n%(t)s\n%(d)s\n%(m)s" % { 't': title or DEBUG, 'm': msg, 'd': "*"*9 }

#---------------------------------
# 1: Take the input data
#---------------------------------

def get_data_input(input_files):
    data_input = ""
    for line in fileinput.input(input_files):
        data_input += line
    if not BE_SILENT:
        debug(data_input, "#1: INPUT DATA")
    return data_input

#------------------------------------------------
# 2: Check for what form of data structure it is.
#------------------------------------------------

class DATA_STRUCTURE_KIND:
    JSON_DICT = "JSON_DICT"
    JSON_ARRAY = "JSON_ARRAY"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    BOOL = "BOOL"
    UNKNOWN = "UNKNOWN"

    JSON_TYPES = {
            'dict': JSON_DICT,
            'list': JSON_ARRAY,
            'int': INTEGER,
            'float': FLOAT,
            'unicode': STRING,
            'bool': BOOL
        }

    REVERSE_JSON_TYPES = dict([(JSON_TYPES[k],k) for k in JSON_TYPES.keys()])

def learn_data_structure(input):
    # let's try to infer the type using the json parser...
    try:
        import json
        parsed = json.loads(input)
        dtype = type(parsed).__name__
        if not BE_SILENT:
            debug(dtype, "#2: DETECTED DATA STRUCTURE TYPE")
        return parsed, DATA_STRUCTURE_KIND.JSON_TYPES[dtype]
    except:
        # anything else is unknown/unsupported as of now...
        if not BE_SILENT:
            debug(input, "#2: Learning Data-Structure: Invalid or unsupported data structure")
        return input, DATA_STRUCTURE_KIND.UNKNOWN



#------------------------------------------------
# 3: Extract or infer all meta-data about the kind of data storable in the given data-structure
#------------------------------------------------
def learn_fields_in_structure(data, dtype):
    if dtype == DATA_STRUCTURE_KIND.UNKNOWN:
        if not BE_SILENT:
            debug(data, "#3: Learning Fields: Invalid or unsupported data structure")
        return None
    else:
        if dtype == DATA_STRUCTURE_KIND.JSON_DICT:
            # fine, let's infer the fields and their types...
            fields =  dict([(k,DATA_STRUCTURE_KIND.JSON_TYPES[type(data[k]).__name__]) for k in data.keys()])
            if not BE_SILENT:
                debug(fields, "#3: Learning Fields: Detected the following meta data...")

            return fields
        else:
            if not BE_SILENT:
                debug(dtype, "#3: Learning Fields: This type is currently not supported at this stage... ")
            return None


#------------------------------------------------
# 4: Generate or obtain a skeleton program into which the instructions for prompting and persisting the given type of data can be injected.
#------------------------------------------------
class OUTPUT_LANGUAGES:
    PYTHON = "python"

    APP_EXTENSIONS = {
            PYTHON: 'py'
            }

def get_skeleton_program(lang):
    skel_prog = {
            "LANGUAGE": lang,
            "SHEBANG": "#!/usr/bin/env %s" % lang,
            "OUTPUT_DATA_STRUCT_NAME": '__OUT__',
            "PROMPTS": [],
            "ENCODING": [],
            "PERSISTENCE": [],
            "IS_PERSISTING_SET": False,
            }
    if not BE_SILENT:
        debug(skel_prog, "#4: Generate Skel Prog: %s has been chosen as the skeleton programming language" % lang)
    return skel_prog


#------------------------------------------------
# 5: Based on the learned data structure and the meta-data from it, generate and inject instructions into the skeleton program,
# which instructions are for prompting from the user inputs corresponding to fields in the data structure.
#------------------------------------------------
def inject_data_prompts_into_skel(skel_prog, fields):
    if skel_prog["LANGUAGE"] == OUTPUT_LANGUAGES.PYTHON:
        # basically, for each field, we present to the user the prompt with the field name, and store the captured input in a similar named field
        skel_prog["PROMPTS"].extend(['%(f)s = raw_input("%(f)s: ")' % {'f': f} for f in fields.keys()])
        if not BE_SILENT:
            debug(skel_prog, "#5: Inject Data Prompting Commands: Prompts for data have been injected into the skeleton program...")
        return skel_prog
    else:
        if not BE_SILENT:
            debug(skel_prog["LANGUAGE"], "#5: Inject Data Prompting Commands: This language is currently not supported")
        return None


#------------------------------------------------
# 6. Generate and inject instructions for transforming the captured user inputs into a data-structure of kind similar to what was detected,
# using what is known of the fields and the meta-data about them
#------------------------------------------------
def inject_data_encoding_commands(skel_prog, dtype, fields):
    if skel_prog["LANGUAGE"] == OUTPUT_LANGUAGES.PYTHON:
        if dtype == DATA_STRUCTURE_KIND.JSON_DICT:
            # since this is a dictionary, we can just declare an empty one, and then inject commands to write each field to the dict,
            # with the corresponding field name, but ensuring to coerce the field data to the correct type while doing this....
            skel_prog["ENCODING"].append("%(dname)s = {}" % { 'dname': skel_prog["OUTPUT_DATA_STRUCT_NAME"]})
            skel_prog["ENCODING"].extend(['%(dname)s["%(field)s"] = %(type)s(%(field)s)' %
                {'field': f, 'type': DATA_STRUCTURE_KIND.REVERSE_JSON_TYPES[fields[f]], 'dname': skel_prog["OUTPUT_DATA_STRUCT_NAME"]} for f in fields.keys()])
            if not BE_SILENT:
                debug(skel_prog, "#6: Inject Data Encoding Commands: Data encoding commands have been injected into the skeleton program...")
            return skel_prog
        else:
            if not BE_SILENT:
                debug(dtype, "#6: Inject Data Encoding Commands : This data type is currently not supported")
            return None
    else:
        if not BE_SILENT:
            debug(skel_prog["LANGUAGE"], "#6: Inject Data Encoding Commands: This language is currently not supported")
        return None

#------------------------------------------------
# 7. if the skeleton program doesn't already contain instructions for persisting or outputing the encoded data, then add this too.
#------------------------------------------------
def inject_data_persisting_commands(skel_prog, dtype):
    if skel_prog["IS_PERSISTING_SET"]:
        return skel_prog

    if skel_prog["LANGUAGE"] == OUTPUT_LANGUAGES.PYTHON:
        if dtype == DATA_STRUCTURE_KIND.JSON_DICT:
            # in an update, we could have the invocation of APPIAT tell us what the preffered persistence form is : file, db, http, email, another program, stdout, etc
            # but for now, we shall just output the encoded data to stdout... user can still route it to whatever end-point they desire...
            skel_prog["PERSISTENCE"].append("import json")
            skel_prog["PERSISTENCE"].append("print json.dumps(%(dname)s)" % { 'dname': skel_prog["OUTPUT_DATA_STRUCT_NAME"]})
            if not BE_SILENT:
                debug(skel_prog, "#7: Inject Data Persistence Commands: Data persistence commands have been added to the skeleton program...")
            return skel_prog
        else:
            if not BE_SILENT:
                debug(dtype, "#7: Inject Data Persistence Commands : This data type is currently not supported")
            return None
    else:
        if not BE_SILENT:
            debug(skel_prog["LANGUAGE"], "#7: Inject Data Persistence Commands: This language is currently not supported")
        return None


#------------------------------------------------
# 8. Take the generated program, and output it somewhere it can then be used.
#------------------------------------------------
def write_final_program(skel_prog, prog_name='data_app'):
    prog_source = [skel_prog["SHEBANG"]]
    prog_source.extend([l for l in skel_prog["PROMPTS"]])
    prog_source.extend([l for l in skel_prog["ENCODING"]])
    prog_source.extend([l for l in skel_prog["PERSISTENCE"]])
    out_source = "\n".join(prog_source) # beware of the line-endings on some diff platforms...
    out_prog_file_name = "%s.%s" % (prog_name, OUTPUT_LANGUAGES.APP_EXTENSIONS[skel_prog["LANGUAGE"]])
    with open(out_prog_file_name, 'w') as f:
        f.write(out_source)
    if not BE_SILENT:
        debug(out_source, "#8: Generated source code has been written to: %s" % out_prog_file_name)
    return out_prog_file_name


#------------------------------------------------
# 9 [optional] make this generated program executable or ready for use by the end user.
#------------------------------------------------
def make_program_executable(path):
    import os
    import stat
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)
    if not BE_SILENT:
        debug(path, "#9: App is now executable for all users that can read the file...")


#***************************************
# APPIAT in action...
#***************************************

data_input = get_data_input(unknown_args)
parsed_data, data_type = learn_data_structure(data_input)
if data_type != DATA_STRUCTURE_KIND.UNKNOWN:
    fields = learn_fields_in_structure(parsed_data, data_type)
    skeleton_program = get_skeleton_program(OUTPUT_LANGUAGES.PYTHON)
    skeleton_program = inject_data_prompts_into_skel(skeleton_program, fields)
    skeleton_program = inject_data_encoding_commands(skeleton_program, data_type, fields)
    skeleton_program = inject_data_persisting_commands(skeleton_program, data_type)
    app_file_name = write_final_program(skeleton_program)
    make_program_executable(app_file_name)
else:
    debug(data_type, "Unable to proceed, due to this unknown data type...")
