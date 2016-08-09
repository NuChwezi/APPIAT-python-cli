# APPIAT-python-cli

This is the python cli-app generator branch for the APPIAT Project started by the Nu Chwezi. It is an Appiat built using python, and which also spit out python apps usable on the command line.

-----

#The APPIAT Concept:

APPIAT is an attempt to build a special compiler that can make [data-capturing] apps from basic descriptions of the target output data of those apps - such as with samples of potential output data.

What we are proposing here, is a type of compiler, that can take in what other programs would have used as "input data", and then work backwards, to generate the kind of program that could produce such *kind* of data - not necessarily programs that would spit out the same exact instance of data as what was used to define the generated program, but which programs can offer a method of outputing the same kind/structure of data - possibly preserving data types, field semantics and the syntax of the data. Oh definitely, for more advanced scenarios (like where the input sample is to be kept small, yet particular constraints on the structure need be enforced, we could directly jump to the use of such existing open standards as JSON Schema as the input for our compiler. 

Read more about the ambitious dreams behind this and similar projects, over at NuScribes: https://nuscribes.com/scribes_app/book/40/read/?#chapter-498
