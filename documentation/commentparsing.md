Comment Parsing
===============
This page has detailed notes on comment parsing in the Documentation Injector
tool aka the Doctor. For an introduction to the tool see the
[parent directory](/../) readme file. Some terms used on this page are defined
in the [reference.md](reference.md) file.

The tool parses comment lines into the following parts, from left to right:

-   Indentation space, `indent`.
-   Comment symbol, `symbol`.
-   Margin space, `margin`.
-   Text, `text`.
-   Line end, `eol`.

The tool also tracks the line numbers in the original input file.

A single physical line could consist of multiple logical lines. Here is an
example that is a single physical line:

    /** One-liner. */

The above parses into two logical lines, as follows.

    [
        {
            "lineNumber": 1,
            "indent": "", "symbol": "/**", "margin": " ",
            "text": "One-liner. ",
            "eol": ""
        }, {
            "lineNumber": 1,
            "indent": "", "symbol": "*/", "margin": "",
            "text": "",
            "eol": ""
        }
    ]

Inside the tool Python code, the `indent` and `margin` attributes are
represented as numbers, i.e. a count of spaces instead of a string.

A more usual comment could be as follows.

    /** This is inset like if it was for a method or something.
     *
     * The Markdown could be tidier, or extracted to a docco source file,
     * if it passed the 80 column limit.
     */

It parses to the following.

    [
        {
            "lineNumber": 1,
            "indent", 0, "symbol", "/**", "margin", 1,
            "text", "This is inset like if it was for a method or something.",
            "eol", "\n"
        }, {
            "lineNumber": 2,
            "indent", 1, "symbol", "*", "margin", 0,
            "text", "",
            "eol", "\n"
        }, {
            "lineNumber": 3,
            "indent", 1, "symbol", "*", "margin", 1,
            "text", "The Markdown could be tidier, or extracted to a docco source file,",
            "eol", "\n"
        }, {
            "lineNumber": 4,
            "indent", 1, "symbol", "*", "margin", 1,
            "text", "if it passed the 80 column limit.",
            "eol", "\n"
        }, {
            "lineNumber": 5,
            "indent": 1, "symbol": "*/", "margin": 0,
            "text": "",
            "eol": ""
        }
    ]

Note that the end-comment has an empty line end. This is because the comment
ends at the closing symbol, "*/".

Another style of comment could be as follows.

    /**
     Leaderless.
 
     No leaders in the comment
 
     *   Starred list, item one.

     *   Item two.
 
     That's all.
    */

The above parses to the following.

    [
        {
            "lineNumber": 1,
            "indent", 0, "symbol", "/**", "margin", 0,
            "text", "",
            "eol", "\n"
        }, {
            "lineNumber": 2,
            "indent", 1, "symbol", "", "margin", 0,
            "text", "Leaderless.",
            "eol", "\n"
        }, {
            "lineNumber": 3,
            "indent", 0, "symbol", "", "margin", 0,
            "text", "",
            "eol", "\n"
        }, {
            "lineNumber": 4,
            "indent", 1, "symbol", "", "margin", 0,
            "text", "No leaders in the comment",
            "eol", "\n"
        }, {
            "lineNumber": 5,
            "indent", 0, "symbol", "", "margin", 0,
            "text", "",
            "eol", "\n"
        }, {
            "lineNumber": 6,
            "indent", 1, "symbol", "", "margin", 0,
            "text", "*   Starred list, item one.",
            "eol", "\n"
        }, {
            "lineNumber": 7,
            "indent", 0, "symbol", "", "margin", 0,
            "text", "",
            "eol", "\n"
        }, {
            "lineNumber": 8,
            "indent", 1, "symbol", "", "margin", 0,
            "text", "*   Item two.",
            "eol", "\n"
        }, {
            "lineNumber": 9,
            "indent", 0, "symbol", "", "margin", 0,
            "text", "",
            "eol", "\n"
        }, {
            "lineNumber": 10,
            "indent", 1, "symbol", "", "margin", 0,
            "text", "That's all.",
            "eol", "\n"
        }, {
            "lineNumber": 11,
            "indent": 1, "symbol": "*/", "margin": 0,
            "text": "",
            "eol": ""
        }
    ]

Legal
=====
Copyright 2019 VMware, Inc.  
SPDX-License-Identifier: BSD-2-Clause
