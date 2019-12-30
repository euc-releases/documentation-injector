Documentation Injector
======================
This repository contains the code for a tool for inserting Markdown text into
documentation comments in source code. The tool is referred to as the Doctor,
which is an abbreviation for DOCumentation injecTOR.

The tool can be used to insert Markdown text from a cross-platform repository
into the documentation comments in platform-specific source code files. This
facilitates:

-   Separating the documentation writing and code writing tasks so that they can
    be done by different people.

-   Having common descriptions for the same functions on different platforms,
    known as single-sourcing.
    
Markdown is an open format that is emerging as dominant for documentation
comments in code. For example, it is already supported by GitHub and GitLab, and
by Xcode for Swift.

The Doctor is written in Python. It makes use of an Open Source Markdown parser,
mistune, which was also written in Python.

Links:

-   Markdown home page, on the Daring Fireball website:  
    [https://daringfireball.net/projects/markdown/](https://daringfireball.net/projects/markdown/)
-   Mistune on GitHub:  
    [https://github.com/lepture/mistune/tree/v1](https://github.com/lepture/mistune/tree/v1)

Installation
============
To run the Doctor, you will need the following.

-   Python version 3.

    Installers for Python can be downloaded from the Python website. Computers
    running macOS or other Unix operating systems may come with Python, but
    often only version 2.
    
    See [https://www.python.org/](https://www.python.org/)

-   The Mistune Markdown parser v1.

    Mistune can be downloaded or cloned from its GitHub repository, see above.
    Doctor requires v1 Mistune. Doctor will be updated to v2 in due course but
    Mistune v2 isn't released at time of writing.
    

-   The code in this repository,
    [https://github.com/vmware/documentation-injector](https://github.com/vmware/documentation-injector)

Check your installation by running the tool as follows.

    cd /path/where/you/cloned/documentation-injector
    python3 -m doctor -m /path/where/you/downloaded/mistune

This should print an error message like the following.

    usage: doctor [-h] [--ad-hoc] [-m MISTUNE] [-e] [-x EXTRACT_DIR] [-k] [-o]
                [-w WIDTH] [-d] [-j] [-l [LOAD [LOAD ...]]]
                [-i INPUTS [INPUTS ...]]
    doctor: error: At least one input must be specified.

Usage
=====
The main use of the Doctor is to:

-   Take a set of *code source* files as input.
-   Take also a set of *documentation source* files as another input.
-   Inject documentation from the documentation source into the code source.
-   Overwrite the code source files with edited versions that include the
    injected documentation.

The code source files contain markers that specify which documentation source to
inject and where. The markers use a Universal Resource Identifier (URI)
convention.

On the Doctor command line, input code source files are specified by one or more
`-i` switches.
-   `-i filename.h` specifies processing a single file.
-   `-i directory` specifies processing all code source files in a directory,
    and in any sub-directories.

Documentation Marker Examples
-----------------------------
The following three file snippets illustrate the documentation marker URI
syntax.

Example code source input, `data/source.h` file:

    /** doc://./docco.md#Sample
     */
    void methodA();
     
    /** doc://#Sample
     *
     * ## Header for a special paragraph [doc://./docco.md#product-name]
     * This is the special para.
     */
    void methodB();

    /** doc://../data/docco.md#Sample-List
     */
    void methodC();

Example documentation source file input, `docco.md` in the same directory as the
source file:

    Text before the first heading is freeeee

    # Sample
    This is some sample.
    
    This is the end of it.
    # 
    Text after an empty heading is also free
    
    # product-name
    turbo-encabulator
    # Sample-List
    Indirect inclusion below.

    doc://./docco.md#Sample

    -   doc://./docco.md#Sample
    
    Indirect inclusion in a context above.

Example source file as overwritten:

    /** This is some sample.
     * 
     * This is the end of it.
     */
    void methodA();
     
    /** This is some sample.
     * 
     * This is the end of it.
     *
     * ## Header for a special paragraph turbo-encabulator
     * This is the special para.
     */
    void methodB();

    /** Indirect inclusion below.
     *
     * This is some sample.
     * 
     * This is the end of it.
     *
     * -   This is some sample.
     *     
     *     This is the end of it.
     *
     * Indirect inclusion in a context above.
     */
    void methodC();

For details of processing and the marker URI convention, see the
[documentation/reference.md](documentation/reference.md) file.

Other Features
--------------
The Doctor also has the following other features.

-   **Wrap documentation comments** in the output to a maximum number of
    columns specified by the `-w` command line switch.

-   Treat **at-commands** as exceptions to Markdown line continuation handling,
    in .h files, or convert them to Swift documentation, in Swift files.

    At-commands, such as @return and @param, are used in Doxygen and other
    systems to mark documentation for return values, parameters, and some other
    details of a programming interface.
    
    Swift documentation syntax doesn't use at-commands. Instead it is based on
    Markdown list format.

-   **Dry run**, in which the output is generated but then discarded, and the
    source files aren't overwritten. This is the default behaviour. Overwriting
    is activated by the `-o` command line switch.

-   **Extract mode**, in which the documentation comments in the code source are
    extracted. A new documentation source file with a `.md` extension is
    generated for each code source file. The documentation comments are replaced
    by documentation markers that refer to the new file.
    
    Extract mode is intended as a one-off preparation stage for moving source
    into a Doctor regime. It is activated by the `-e` command line switch.

-   Analytical and diagnostic output, as follows.
    -   **Job-level statistics**, printed in JavaScript Object Notation (JSON)
        format. Example:
        
            {
                "totalFiles": 20,
                "overwrites": 2,
                "edited": 2,
                "extensionCounts": {
                    "": 1,
                    "md": 3,
                    "py": 6,
                    "pyc": 8,
                    "h": 2
                }
            }
        
        These are printed at the end of each invocation.

    -   **File-level statistics**, also printed in JSON format. Example:
    
            {"path": "test/data/source.h", "extension": ".h", "overwrote": true, "extract": false, "lineTypes": {"SourceLine": 61, "CommentBlock": 23}}
            {"path": "test/data/docco.md", "extension": ".md", "overwrote": false, "extract": false, "lineTypes": null}

        File-level statistics are activated by the `-j` command line switch.

    -   Delta aka **diff analysis** of code source files. Example:
    
            *** data/source.h
            --- Edited by the Doctor.
            ***************
            *** 4,6 ****
              
            ! /** doc://./docco.md#Sample
               */
            --- 4,8 ----
              
            ! /** This is some sample.
            !  * 
            !  * This is the end of it.
               */
        
        Diff analysis is activated by the `-d` command line switch.
    
    Analytical and diagnostic output is still generated in a dry run.

For a list of all command line options, run the Doctor with the `-h` command
line switch.

Tests
=====
The tools has a test suite, in the [test](test) sub-directory.

Contributing
============
The Doctor project team welcomes contributions from the community. Before you
start working with doctor, please read our [Developer Certificate of
Origin](https://cla.vmware.com/dco). All contributions to this repository must
be signed as described on that page. Your signature certifies that you wrote the
patch or have the right to pass it on as an open-source patch. For more detailed
information, refer to the [contributing.md](contributing.md) file.

Check the [documentation/backlog.md](documentation/backlog.md) file for a list
of work to be done.

License
=======
The Documentation Injector, Doctor, is:  
Copyright 2019 VMware, Inc.  
And licensed under a two-clause BSD license.  
SPDX-License-Identifier: BSD-2-Clause
