# Run with Python 3
# Copyright 2024 Omnissa, LLC.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Parsers module. Part of the Doctor documentation tool.
No standalone capability.
"""
# Exit if run other than as a module.
if __name__ == '__main__':
    print(__doc__)
    raise SystemExit(1)

# Standard library imports, in alphabetic order.
#
# Regular expressions module.
# https://docs.python.org/3/library/re.html
import re
#
# Local imports
#
# Module with classes for storing comment line analysis.
from doctor.comment_line import (
    SourceLine, CommentLine, CommentLineType, dump_match)

class SlashStarsParser:
    '''\
Parser for /** style documentation comments.
    '''
    # Constant regular expressions get compiled here. Compilation will happen
    # only once, when this script is run. It's a kind of static class-level
    # value. If it were in the __init__ instead then it would happen every time
    # the class was instantiated.
    #
    # Comment continuation, which is a little complex. Following syntax elements
    # are used:
    #
    # -   Python r'...' for raw strings that don't get backslash expansion.
    # -   (?P<name>...) for named capture groups.
    # -   (?:...) for non-capture groups.
    # -   Python string continuation with comments in between the strings.
    #
    _commentContinue = re.compile(
        # Indent. Uses a space, not \s, which is OK because expandtabs will
        # have been called on the string before matching.
        r'^(?P<indent> *)'
        # Group for matching one of a number of expressions.
        # The group isn't captured, which is specified by ?:
        r'(?:'
            # Symbol then end of line.
            r'(?P<symbolEOL>\*)$'
            r'|'
            # Symbol, Margin. Margin can only be a single space.
            r'(?P<symbolMargin>\*)(?P<margin> )'
            r'|'
            # Symbol then look ahead to a character that isn't slash.
            # Look-ahead is specified by ?=
            r'(?P<symbolNonSlash>\*)(?=[^/])'
            r'|'
            # End of line. An empty group gets assigned, which can be
            # checked as an indicator.
            r'(?P<EOL>)$'
            r'|'
            # Look ahead to a character that isn't an asterisk.
            r'(?P<nonSymbol>)(?=[^* ])'
        r')'
    )
    #
    # Comment start.
    _commentStart = re.compile(
        r'^(?P<indent>\s*)(?P<symbol>/\*\*)(?P<margin> ?)'
        r'(?:$|(?=[^/]))')
    # Second line in the above prevents matching /**/
    #
    # Comment finish, which must be used with the .search() method, not the
    # .match() method.
    _commentFinish = re.compile(
        r'(?P<indent>^[ \t]*)?(?P<symbol>\*/)')

    # Regular expression properties are provided for readability and so that
    # they can be tested.
    @property
    def commentStart(self):
        return self._commentStart
    @property
    def commentContinue(self):
        return self._commentContinue
    @property
    def commentFinish(self):
        return self._commentFinish
    
    @classmethod
    def read(cls, iterator, verbose=False):
        reader = cls()
        
        sourceLine = None
        inComment = False
        lineAnalysis = None
        while True:
            if sourceLine is None:
                try:
                    sourceLine = iterator.__next__()
                except StopIteration:
                    break

                if verbose:
                    print(sourceLine)

            if not inComment:
                match = reader.commentStart.search(sourceLine.line)
                if match is None:
                    if sourceLine.line != '':
                        yield sourceLine
                    sourceLine = None
                else:
                    lineAnalysis = CommentLine(sourceLine.lineNumber, match)
                    lineAnalysis.lineType = CommentLineType.START
                    # .text gets filled in below, even if the comment is a
                    # stupid empty one.
                    
                    # At time of writing, .start() is always zero here because
                    # the comment start is everything from the start of the
                    # line. That's needed so that the indentation can be set.
                    # Just in case, this code would yield the part before the
                    # comment start.
                    if match.start() > 0:
                        yield SourceLine(sourceLine.lineNumber
                                         , sourceLine.line[:match.start()])

                    sourceLine.line = sourceLine.line[match.end():]
                    if verbose:
                        print('commentStart {}\n    {}'.format(
                            dump_match(match), lineAnalysis))
                    inComment = True
            
            finishAnalysis = None
            finishLine = None
            if inComment:
                match = reader.commentFinish.search(sourceLine.line)
                if match is not None:
                    finishLine = SourceLine(
                        sourceLine.lineNumber, sourceLine.line[match.end():])
                    sourceLine.line = sourceLine.line[:match.start()]
                    finishAnalysis = CommentLine(sourceLine.lineNumber, match)
                    finishAnalysis.lineType = CommentLineType.FINISH
                    if verbose:
                        print('commentFinish {}\n    {}'.format(
                            dump_match(match), finishAnalysis))
                
                if lineAnalysis is None:
                    match = (
                        None if sourceLine.line == ""
                        else reader.commentContinue.search(sourceLine.line))
                    if match is None:
                        if finishAnalysis is None:
                            raise RuntimeError(" ".join((
                                "Line didn't match start, finish, nor"
                                " continue.", str(sourceLine))))
                    else:
                        lineAnalysis = CommentLine(sourceLine.lineNumber, match)
                        lineAnalysis.lineType = CommentLineType.CONTINUE
                        lineAnalysis.textEOL = sourceLine.line[match.end():]
                        sourceLine = None
                        if verbose:
                            print('commentContinue {}\n    {}'.format(
                            dump_match(match), lineAnalysis))
                else:
                    lineAnalysis.textEOL = sourceLine.line
                    sourceLine = None
                    if verbose:
                        print('with text\n    {}'.format(lineAnalysis))

            if lineAnalysis is not None:
                yield lineAnalysis
                lineAnalysis = None

            if finishAnalysis is not None:
                inComment = False
                yield finishAnalysis
                if verbose:
                    print('Finish analysis', sourceLine, finishLine)
                sourceLine = finishLine
