Documentation Injector Reference
================================
This page has detailed reference notes on the Documentation Injector project aka
the Doctor. For an introduction to the project see the [parent directory](/../)
readme file.

Definitions
===========
The following terms are used with the following meanings on this page.

-   Code source.

    For example, .h files that are part of the source code to a project.

-   Documentation comment.

    Comments in a source code file that are there to document its programming
    interface. See the Documentation Comment Syntax notes, below.
    
-   Documentation source.

    Content that is to be injected by the tool, from another file, into the
    documentation comments in a code source file. The tool supports Markdown
    format for documentation source. See the Documentation Source Syntax notes,
    below.

-   Documentation marker.

    Placeholders in code source that identify documentation source to be
    injected. See the Documentation Marker Syntax notes, below.

Syntax Reference
================
Documentation Comment Syntax
----------------------------
Documentation comments can be identified by following a syntax within the
comment syntax of the programming language of the code. There are a number of
syntaxes for documentation comments. The following example illustrates the
syntax supported by the tool.

    /** Documentation comment introduced by second asterisk.
     * 
     * Comment continues with optional leader asterisks.
     * 
     * Documentation ends at the end of the comment.
     */

This syntax is already used, formally or by convention, in programming languages
such as C, C++, Objective-C, Swift, and Kotlin. It is recognised by a number of
code editor and integrated development environment (IDE) products such as Apple
Xcode, and by documentation generation tools such as Doxygen.

For notes on how the tool parses comment lines, see the
[commentparsing.md](commentparsing.md) file.

Documentation Marker Syntax
---------------------------
Documentation marker syntax is based on the Universal Resource Identifier (URI)
standard. A documentation marker URI:

-   Must have the `doc` schema, i.e. begin `doc://`.
-   Can have a path, optionally.
-   Must have a fragment, i.e. a part after a hash character.

Markers can be recognised in either of the following contexts.

-   The marker is in square brackets.
-   The marker is at the start of a line.

Markers will be recognised directly in a code source file in a documentation
comment, or indirectly in any included documentation source.

The URI parts have the following semantics.

-   The path specifies the documentation source *file* that contains the text to
    insert. It can be relative to the location of the file that contains the
    marker.
-   The fragment specifies the documentation source *section* name, within the
    documentation source file, that contains the text to insert.

Some examples:

-   `doc://./docco.md#Sample`
    
    File is docco.md in the same directory as the file that contains the
    marker.  
    Section name is Sample.

-   `doc://../doccodoc.md#Introduction`

    File is doccodoc.md in the parent directory relative to the file that
    contains the marker.  
    Section name is Intoduction.
    
-   `[doc://#marker-fragment]`

    File isn't specified. See the Processing Overview, below, for how this is
    interpretted.  
    Section name is "marker-fragment".

See also:

-   The examples in the parent [../README.md]([../README.md) file, under the
    Documentation Marker Examples heading.
-   Document Source Syntax, below, for details of named section definition.
-   Processing Overview, below, for details of how markers without paths are
    resolved.
-   Wikipedia page for URI:
    [https://en.wikipedia.org/wiki/Uniform_Resource_Identifier](https://en.wikipedia.org/wiki/Uniform_Resource_Identifier)

Documentation Source Syntax
---------------------------
Documentation source files use Markdown syntax. Named sections within a
documentation source file are parsed out as follows.

-   Lines that begin with a hash character followed by a non-hash character, are
    *section name* lines.
    -   The section name is the text following the leading hash, trimmed of any
        whitespace characters at the start and end.
    -   URI fragments can contain spaces and tab characters but this requires
        URL encoding. Best practice would be not to use those characters in
        section names.
-   Lines that begin with a hash character, then have zero or more whitespace
    characters, then end, are *section end* lines. Section end lines are
    optional.
-   The *section content* is read as follows.
    -   Named section content starts after the section name line with the
        corresponding name.
    -   Section content ends at the next section name line, or at a section end
        line, whichever comes first.
    -   The end-of-line on the last section line isn't included in the section
        content. This enables definition of short named sections.
-   Files can contain notes and comments that aren't part of any named section:
    -   In the lines before the first section name line.
    -   In the lines immediately following a section end line.

By example:

    This is a sample documentation source file. Lines before the first section
    name can be used for notes.

    # NameOne
    This is the first line of the NameOne section.
    
    ## This is a heading within the section
    The heading isn't a section name line.
    
    This is a Markdown level-one heading
    ====================================
    
    This is the last line of NameOne.
    # 
    Lines after a section end can also be used for notes.
    
    # infix
     fixed *emphatic* in 
    #
    The above line has a space at the start and another at the end. Those are
    included in the section content.
    
    The next section has the content "turbo-encabulator" with no end-of-line.
    
    # product-name
    turbo-encabulator
    #
    
    Next couple of fragments show some edge cases.
    
    -   `empty` has zero lines of section content.
    -   `emptyline` has one line with an empty string in it.
    
    # empty
    # emptyline
    
    #

Processing Overview
===================
Processing of code source input proceeds as follows.

1.  Input code source locations are read from the command line, where they are
    specified as individual files or as directories.

2.  Each code source file is parsed into a sequence of source lines and comment
    lines. Source lines will be copied to the output unmodified.

3.  Each documentation marker in a comment line is resolved.
    
    Documentation markers may have a path that specifies a documentation source
    file, and must have a fragment that specifies a documentation source
    section. See also the Documentation Marker Syntax section, above.
    
4.  When a marker that specifies a file is encountered, the file is first parsed
    and all the named sections it contains are loaded into a cache. See also the
    Documentation Source Syntax, above.
    
    The resolution of the marker is then to replace it with the contents of the
    section named in its fragment.

5.  When a marker that doesn't specify a file is encountered, the cache is
    checked for a named section that matches the fragment.
    
    The resolution of the marker is then to replace it with the contents of the
    named section from the cache.

6.  If the replacement content for a marker itself includes more markers, those
    are also resolved as above, recursively.

Note:

-   The cache persists for the whole run.
-   Documentation source files can be loaded into the cache before the above
    processing. This can be done with the `-l` command line switch.

Legal
=====
Copyright 2019 VMware, Inc.  
SPDX-License-Identifier: BSD-2-Clause
