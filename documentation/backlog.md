Backlog
=======
This page has the work backlog for the Documentation Injector project aka the
Doctor. For an introduction to the project see the [parent directory](/../)
readme file.

-   Add a unit test for the 'Warning: Apparent unrecognised at-command' message.

    See the test/test_add_mistune_path.py file for code that captures output and
    tests it.

-   Check exact line width and add tests for that.

-   Add support for proper Swift docco comment syntax having been followed in
    the input. Currently, they get parsed as unordered lists. Correct handling
    could be to modify the indentation, from 4 to 2, by means of a custom flag
    in the MarkdownItem for a list.

-   Maybe add an option to suppress docco content in some input documentation
    source. This would be to support removal of internal documentation from
    public builds.

-   See about improving the extraction by using SourceKitten to get class and
    method names.

-   Review Exception generation and handling.
    
    Maybe change some exceptions to Assertion, if they are internal to the
    Doctor. Add others to the default_main handling.

-   The load vs input distinction could be simplified: Assume all .md files
    discovered are to be pre-loaded; assume all .h files are to be overwritten.

-   JUnit output.

    [https://llg.cubic.org/docs/junit/](https://llg.cubic.org/docs/junit/)

-   In getter.py file:

    -   Count how many times each documentation fragment is used. Report on any
        that are used zero times.
        
-   Maybe support absolute paths, like:

        doc://absolute/path/to/file.md#reference.in.file
    
    Absolute paths could be unsafe though.

-   Maybe support fragment-less URI:
    
        doc://macro-name
    
    Not sure what it should mean though.

-   Recognise files other than .h files. Might need a command line switch, or
    just add all the known extensions by default.

-   Add the rest of the Markdown span types and block types, to the enum and to
    the renderer. Right now they are stubbed out to raise NotImplementedError.
    
    Notes on how to do that:
    
    -   In the markdown.py file, add an auto constant to the BlockType or
        SpanType enumeration.
    -   In the doc_markdown.py file, replace the NotImplemented raising stub
        with code to create the Markdown items from the text.
    -   In the markdown.py file, add an implementation for the new item type to
        the output method.

-   Maybe modify autolink to recognise doc: URIs.

Legal
=====
Copyright 2019 VMware, Inc.  
SPDX-License-Identifier: BSD-2-Clause
