# Run with Python 3
# Copyright 2019 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Generate Element Tree representation of documentation comments in code. Part of
the Doctor documentation tool.
No standalone capability.
"""
# Exit if run other than as a module.
if __name__ == '__main__':
    print(__doc__)
    raise SystemExit(1)

# Standard library imports, in alphabetic order.
#
# Module for OO path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path
#
# Regular expressions module.
# https://docs.python.org/3/library/re.html
import re
#
# Module for manipulation of the import path and other system access.
# https://docs.python.org/3/library/sys.html
import sys
#
# Text wrapping module.
# https://docs.python.org/3/library/textwrap.html
import textwrap
#
# Module for XML handling.
# https://docs.python.org/3.5/library/xml.etree.elementtree.html#module-xml.etree.ElementTree
import xml.etree.ElementTree as ET
#
# Local imports
#
# Class with a static method for getting capture groups from a regular
# expression match.
from doctor.parser import SlashStarsParser
#
# Mistune parser into ET and utility methods.
from doctor.mistree import TreeParser, matched_groups
from doctor.markdown_tree import (
    ET_string, ET_index, ET_grandparent, ET_copy_attr)

# Convenience functions.
def ET_text(element):
    return "" if element.text is None else element.text
def ET_tail(element):
    return "" if element.tail is None else element.tail
def ET_text_len(element):
    return 0 if element.text is None else len(element.text)
def ET_tail_len(element):
    return 0 if element.tail is None else len(element.tail)

class CommentTree:
    # Constant regular expressions get compiled here. Compilation will happen
    # only once, when this script is run. It's a kind of static class-level
    # value. If it were in the __init__ instead then it would happen every time
    # the class was instantiated.
    #
    # Pattern at-commands. Following syntax elements are used:
    #
    # -   Python r'...' for raw strings that don't get backslash expansion.
    # -   (?P<name>...) for named capture groups.
    # -   Not ^ to anchor because these are called with .match() so it's
    #     implicit.
    # -   Not \s but a space character, because expandtabs will have been called
    #     on the string long before matching. A \s could match some end-of-line
    #     characters, which isn't wanted.
    atCommand = re.compile(
        # Group for matching one of a number of expressions, after an @ sign.
        # The group isn't captured, which is specified by ?:
        r'@(?:'
            # At-commands that are dropped for Swift.
            r'(?P<commandDrop>(?:brief|description|details)) +'
            r'|'
            # At-command for the return value, which gets slightly special
            # handling.
            r'(?P<commandReturn>return)s? +'
            r'|'
            # At-command that is the same in Swift except for an initial
            # capital.
            r'(?P<commandCapitalise>version) +'
            r'|'
            # At-command for parameters, which are followed by a parameter name.
            # Matches param and parameter, but only captures param.
            r'(?P<commandParameter>param)(?:eter)? +(?P<name>\w+) *'
            r'|'
            # At-commands that are ignored, only at-file at the moment.
            r'(?P<commandIgnore>file) +'
        r')'
    )

    #
    # End of line, which must be used with the .search() method, not the .match
    # method. It seems a bit much to use an RE just to match end-of-line. There
    # didn't seem to be anything built in that would match and preserve either
    # CR-LF or NL.
    _commentEOL = re.compile(r'[\r\n]*$')

    # Regular expression properties are provided for readability and so that
    # they can be tested.
    @property
    def commentEOL(self):
        return self._commentEOL

    @classmethod
    def to_xml(cls, pathArguments, docGetter, tabSize=4, maxWidth=80):
        for argument in pathArguments:
            pathSource = Path(argument)
            pathXML = pathSource.with_suffix('.xml')
            with pathSource.open('r') as file:
                iterator = cls.line_elements(file, pathSource)
                iterator = cls.line_expand_tabs(iterator, tabSize)
                iterator = cls.line_star_slash(iterator)
                iterator = cls.comment_blocks(iterator, docGetter)

                fileElement = cls.file_element(pathSource, iterator)

            # Create an ElementTree object so that the XML can be written.
            document = ET.ElementTree(fileElement)

            pathMarkdownXML = pathXML.with_name(''.join((
                pathXML.stem, '_md', pathXML.suffix)))
            print(f'Writing "{str(pathMarkdownXML)}".')
            with pathMarkdownXML.open('w') as file:
                document.write(file, encoding="unicode")

            pathOutput = pathSource.with_name(
                ''.join((pathSource.stem, '_beta', pathSource.suffix)))
            print(f'Writing "{str(pathOutput)}".')
            with pathOutput.open('w') as file:
                cls._output(fileElement, file, maxWidth)

            pathOutputXML = pathXML.with_name(''.join((
                pathXML.stem, '_output', pathXML.suffix)))
            print(f'Writing "{str(pathOutputXML)}".')
            with pathOutputXML.open('w') as file:
                document.write(file, encoding="unicode")
            
        # Shell return convention. Diagnostic option treated as error.
        return 1
    
    @classmethod
    def read_lines(cls, path, tabSize=4):
        with path.open('r') as file:
            iterator = cls.line_elements(file, path)
            iterator = cls.line_expand_tabs(iterator, tabSize)
            iterator = cls.line_star_slash(iterator)
            for lineElement in iterator:
                yield lineElement

    @classmethod
    def file_element(cls, path, iterator, tag='file'):
        element = ET.Element(tag, {'path': str(path)})
        for lineElement in iterator:
            # print(ET.tostring(lineElement))
            # print(lineElement.get('extract'))
            element.append(lineElement)
        return element

    @classmethod
    def line_elements(cls, iterator, source=None, tag='line'):
        lineNumber = 0
        attributes = {}
        if source is not None:
            attributes['source'] = str(source)
        for line in iterator:
            lineNumber += 1
            attributes['number'] = str(lineNumber)
            lineElement = ET.Element(tag, attributes)
            lineElement.text = line
            yield lineElement

    @classmethod
    def line_expand_tabs(cls, iterator, tabSize):
        for element in iterator:
            expanded = element.text.expandtabs(tabSize)
            if expanded != element.text:
                element.set('expandedTabSize', str(tabSize))
                element.text = expanded
            yield element
    
    @classmethod
    def line_star_slash(cls, iterator):
        lineElement = None
        inComment = False
        analysisElement = None
        while True:
            if lineElement is None:
                try:
                    lineElement = iterator.__next__()
                except StopIteration:
                    break

            if not inComment:
                analysisElement = cls._match_start(lineElement)

                if analysisElement is None:
                    # The parser wasn't in a comment, and this line isn't the
                    # start of a comment. Yield the line, which could be the
                    # tail after a previous end comment, and read the next line.
                    if lineElement.text == '':
                        raise AssertionError(
                            f'Empty text in {ET_string(lineElement)}.')
                    yield lineElement
                    lineElement = None
                    continue

                # The parser wasn't in a comment but has identified the start of
                # a comment.
                if lineElement.text != '':
                    # At time of writing, lineElement.text is always empty
                    # here because the comment start is everything from the
                    # start of the line. That's needed so that the
                    # indentation can be set. Just in case, this code would
                    # yield the part before the comment start.
                    prefixElement = ET.Element(lineElement.tag, {
                        'number': lineElement.get('number')})
                    prefixElement.text = lineElement.text
                    yield prefixElement

                # Feed the tail from after the <margin> back in for further
                # analysis in this iteration. This is to support comments that
                # start and end on the same line, like this:
                #
                #     /** comment */
                #
                # If the iteration doesn't find an end comment, the tail will be
                # put back into the start comment later in this iteration.
                lineElement.text = analysisElement[2].tail
                analysisElement[2].tail = None
                inComment = True

            finishElement = None
            if inComment:
                finishElement = cls._match_finish(lineElement)
                # If the previous analyse call found an end comment:
                #
                # -   The text before it will be in the line element.
                # -   The text after it will be in the finish element, in the
                #     tail of its last child. That text gets recovered at the
                #     bottom of the loop.

                if analysisElement is None:
                    # The parser gets here if it's in a comment and this line
                    # wasn't the start of the comment. Analyse this line as a
                    # continue comment.
                    if lineElement.text != "":
                        analysisElement = cls._match_continue(lineElement)
                    
                    if analysisElement is None:
                        # The line isn't a continuation. That's OK if it's an
                        # end comment, but shouldn't happen otherwise.
                        if finishElement is None:
                            raise AssertionError(
                                "Failed to match line:"
                                f' {ET_string(lineElement)}.')
                    else:
                        if lineElement.text != '':
                            raise AssertionError(
                                'Text not empty.'
                                f' line: {ET_string(lineElement)}'
                                f' continue: {ET_string(analysisElement)}.')
                        cls._analyse_child_tail(analysisElement)
                else:
                    # The parser gets here if it's in a comment and this line
                    # was the start of the comment. Any end comment on this line
                    # will have been separated already. Put back whatever is
                    # left onto the tail of the start comment <margin>.
                    cls._set_tail(analysisElement[2], lineElement.text)
                    lineElement.text = ""
                    cls._analyse_child_tail(analysisElement)

            if analysisElement is not None:
                yield analysisElement
                analysisElement = None

            if finishElement is not None:
                inComment = False
                if lineElement.text != "":
                    raise AssertionError(
                        'Unused line at finish'
                        f' line: {ET_string(lineElement)}'
                        f' finish: {ET_string(finishElement)}.')
                lineElement.text = finishElement[-1].tail
                finishElement[-1].tail = None
                yield finishElement

            if lineElement.text == "":
                # Set lineElement to None to trigger reading from the iterator
                # at the top of the loop.
                lineElement = None


    @classmethod
    def _set_tail(cls, element, tail):
        if element.tail is None:
            element.tail = tail
        else:
            raise AssertionError(
                f'Overwriting tail {ET_string(element)} with "{tail}".')

    # Next methods access class properties with underscore names, which is a bit
    # naughty. ToDo: Fix it by maybe moving the REs into this file.
    @classmethod
    def _match_start(cls, element):
        return cls._analyse_line(
            element, SlashStarsParser._commentStart, 'start')
    @classmethod
    def _match_continue(cls, element):
        return cls._analyse_line(
            element, SlashStarsParser._commentContinue, 'continue')
    @classmethod
    def _match_finish(cls, element):
        return cls._analyse_line(
            element, SlashStarsParser._commentFinish, 'finish')

    @classmethod
    def _analyse_line(cls, element, regularExpression, commentPart):
        match = regularExpression.search(element.text)
        if match is None:
            return None
        
        matchedGroups = matched_groups(match)
        transcript = [f'groups:{",".join(matchedGroups)}']

        analysedElement = ET.Element(element.tag)
        analysedElement.extend((
            ET.Element(tag) for tag in ('indent', 'symbol', 'margin')))

        tailElement = None
        texts = []
        cursor = 0
        for name in matchedGroups:
            start, end = match.span(name)
            transcript.append(f'{name}:{start},{end}')

            if name == 'indent':
                spanIndex = 0
            elif name.startswith('symbol'):
                spanIndex = 1
            elif name == 'margin':
                spanIndex = 2
            else:
                # No elements for other capture groups. Don't advance the cursor
                # nor change the tail element.
                continue
            
            if start < cursor:
                raise AssertionError()

            # Append the text preceding this group to the end of either of the
            # following.
            #
            # -   Texts that will be joined to become the element text.
            # -   Tail of the last child element.
            prefix = match.string[cursor:start]
            if tailElement is None:
                texts.append(prefix)
            else:
                cls._set_tail(tailElement, prefix)
            tailElement = analysedElement[spanIndex]
            if end > start:
                tailElement.text = match.string[start:end]
            cursor = end

        element.text = ''.join(texts)
        analysedElement.set('transcript', ' '.join(transcript))
        ET_copy_attr(element, analysedElement, ('number', 'source'))
        analysedElement.set('part', commentPart)

        # Put the remaining unmatched text into the tail of the margin. Note
        # that this isn't the same as tailElement, which will be the last child
        # set from a capture group.
        cls._set_tail(analysedElement[2], match.string[cursor:])
        analysedElement[2].set('extract', 'tail')

        return analysedElement
    
    @classmethod
    def _analyse_child_tail(cls, parent):
        match = cls._commentEOL.search(parent[-1].tail)
        if match is None:
            raise AssertionError(
                f'Comment EOL pattern failed to match "{ET_string(parent)}"')
        
        parent[-1].tail = match.string[:match.start()]
        eolElement = ET.Element('eol')
        eolElement.text = match.string[match.start():]
        eolElement.set('extract', 'text')
        parent.append(eolElement)

    @classmethod
    def comment_blocks(
        cls, iterator #, docGetter
        , attribute='part', tagBlock='comment', tagLines='lines'
    ):
        # Corresponds to CommentBlock.read()
        commentElement = None
        for element in iterator:
            endComment = commentElement is not None
            commentPart = element.get(attribute)
            if commentPart is not None:
                if commentElement is None:
                    commentElement = ET.Element(tagBlock, {
                        'lineFirst': element.get('number')
                    })
                    ET_copy_attr(element, commentElement, 'source')
                    linesElement = ET.Element(tagLines)
                    commentElement.append(linesElement)

                linesElement.append(element)
                endComment = commentPart == "finish"
                element = None
            
            if endComment:
                # yield cls._shuffle_comment(commentElement, docGetter)
                yield commentElement
                commentElement = None
            
            if element is not None:
                yield element
    
        if commentElement is not None:
            yield commentElement
            # yield cls._shuffle_comment(commentElement, docGetter)
    
    @classmethod
    def manipulate_comment_lines(cls, iterator, tagLines='lines'):
        for element in iterator:
            linesElement = element.find(tagLines)
            if linesElement is not None:
                cls._shuffle_comment(element, linesElement)
            yield element
    
    @classmethod
    def _shuffle_comment(cls, commentElement, linesElement): #, docGetter):
        # Find the first <indent>, which will be the one in the start.
        indent = linesElement.find(".//indent")
        if indent is None:
            raise AssertionError(
                f'No <indent> in comment: {ET_string(commentElement)}.')
        indentStart = ET_text_len(indent)

        # Check if all the comment lines have a symbol, by looking for a child
        # with a blank symbol. This XPath also matches if the text is None.
        allHaveSymbol = linesElement.find(".//symbol[.='']") is None

        if not allHaveSymbol:
            cls._shuffle_lines(linesElement, indentStart)

        allIndentedOK, indentContinue = cls._analyse_indentation(
            linesElement, allHaveSymbol, indentStart)

        commentElement.set('indentStart', str(indentStart))
        commentElement.set('allHaveSymbol', str(allHaveSymbol))
        commentElement.set('allIndentedOK', str(allIndentedOK))
        if indentContinue is not None:
            commentElement.set('indentContinue', str(indentContinue))
        
        lineLast = commentElement.get('lineFirst')
        for found in linesElement.findall(".//*[@number]"):
            lineLast = found.get('number')
        commentElement.set('lineLast', lineLast)
        
        # cls._insert_extraction(element, docGetter)

        # return element

    @classmethod
    def _shuffle_lines(cls, element, indentStart):
        # Not all lines have *, so assume any apart from the start and finish
        # that do shouldn't and shuffle it into the margin tail, which is
        # actually the text of the comment. This supports, for example, Markdown
        # lists indicated by *, but without comment leaders.
        for line in element.findall("./*[@part='continue']"):
            # First child of line will be the indent element.
            indentLen = ET_text_len(line[0])
            indentLossNeg = (indentStart + 1) - indentLen

            # Second child of line will be the symbol.
            # Third child of line will be the margin.
            shuffles = (
                "" if indentLossNeg >= 0 else line[0].text[indentLossNeg:],
                ET_text(line[1]), ET_text(line[2]), ET_tail(line[2])
            )

            line[2].tail = ''.join(shuffles)
            line.set('shuffles', str(shuffles))

            if indentLossNeg < 0:
                line[0].text = line[0].text[:indentLossNeg]
            line[1].text = None
            line[2].text = None

    @classmethod
    def _analyse_indentation(cls, element, allHaveSymbol, indentStart):
        # Lines that are blank or only spaces are allowed in symbol-less
        # comment blocks. Otherwise, everything must be indented the same as the
        # start, or one more than that.
        indentContinue = None
        for line in element.findall("./*[@part='continue']"):
            # Ignore blank and space-only lines in leaderless comment lines.
            if not allHaveSymbol and ET_text_len(line[1]) == 0:
                spaceOnly = True
                for character in ET_tail(line[2]):
                    if character != ' ':
                        spaceOnly = False
                        break
                if spaceOnly:
                    line.set('spaceOnly', 'continue')
                    continue
            
            if indentContinue is None:
                # First qualifying line; set the correct indent from it.
                if (
                    ET_text_len(line[0]) == indentStart
                    or ET_text_len(line[0]) == indentStart + 1
                ):
                    indentContinue = ET_text_len(line[0])
                    continue
                else:
                    # This first continuation line isn't aligned with the start,
                    # so the block isn't indented correctly.
                    return False, indentContinue
            
            if ET_text_len(line[0]) != indentContinue:
                return False, indentContinue

        return True, indentContinue

    @classmethod
    def extract(cls, iterator, attribute='extract', tag='extract'):
        for element in iterator:
            extraction = None
            for found in element.findall(f".//*[@{attribute}]"):
                if extraction is None:
                    extraction = []
                # The `extract` attribute value will be either "text" or "tail".
                value = getattr(found, found.get(attribute))
                if value is not None:
                    extraction.append(value)
            if extraction is not None:
                extractElement = ET.Element(tag)
                extractElement.text = ''.join(extraction)
                element.append(extractElement)

            yield element

    @staticmethod
    def write_replacement(commentElement, file, path, fragment):
        file.writelines(tuple(CommentTree._replacement_components(
            commentElement, path, fragment
        )))

    @staticmethod
    def _replacement_components(commentElement, path, fragment):
        yield ET_text(commentElement.find(".//*[@part='start']/indent"))
        yield ET_text(commentElement.find(".//*[@part='start']/symbol"))
        yield ET_text(commentElement.find(".//*[@part='start']/margin"))
        yield "[doc://"
        yield path
        yield "#"
        yield fragment
        yield "]"
        yield ET_text(commentElement.find(".//*[@part='start']/eol"))
        yield ET_text(commentElement.find(".//*[@part='finish']/indent"))
        yield ET_text(commentElement.find(".//*[@part='finish']/symbol"))
        # The finish never has an eol.

    @classmethod
    def _insert_extraction(cls, element, docGetter, name='extract'):
        extracts = tuple(cls._extraction(element))
        extractElement = ET.Element(name)
        
        extractElement.text = ''.join(extracts)
        element.insert(0, extractElement)

        # Following puts the extraction into an attribute instead of a node.
        # That's probably were it should be but it's more difficult to read in
        # development.
        # element.set(name, ''.join(extracts))

        treeParser = TreeParser()
        markdownElement = treeParser(extractElement.text)
        ET_copy_attr(element, markdownElement)
        for docURI in markdownElement.findall(".//doc_uri"):
            ET_copy_attr(element, docURI, 'source')
        element.insert(0, markdownElement)

        cls._resolve_doc_uri(markdownElement, docGetter)
        cls._lift_singles(markdownElement)
        cls._lift_trees(markdownElement, False)
        cls._set_newlines(markdownElement)
        cls._resolve_splitters(markdownElement)
        cls._join_texts(markdownElement)
        cls._strip_leading_newlines(markdownElement)

        return extracts
    
    @classmethod
    def _extraction(cls, element):
        for extractor in element.findall(".//*[@extract]"):
            # The `extract` attribute value will be either "text" or "tail".
            extract = getattr(extractor, extractor.get('extract'))
            if extract is not None:
                yield extract

    @classmethod
    def _resolve_doc_uri(cls, markdownOuter, docGetter):
        while True:
            count = 0
            for docOuter in markdownOuter.findall(
                f".//doc_uri[@resolved='{False}']"
            ):
                # Next line will:
                #
                # -   Resolve one level of the doc: uri, i.e. without recursion.
                # -   Set the resolution text into the `content` attribute.
                # -   Set a count of the lines in the resolution text into the
                #     `contentLines` attribute. The line count is needed later.
                source = docGetter.resolve(docOuter)
                #
                # Next lines will parse the resolution text into an element
                # tree, and then put the tree under the doc_uri element. The
                # `source` attributes of any doc_uri elements in the resolution
                # are set to the path of the original file from which the cache
                # was loaded.
                treeParser = TreeParser()
                markdownInner = treeParser(docOuter.get('content'))
                for docInner in markdownInner.findall(".//doc_uri"):
                    docInner.set('source', source)
                docOuter.extend(markdownInner[:])

                count += 1
                docOuter.set('resolved', str(True))
            if count == 0:
                break

    @classmethod
    def _lift_singles(cls, element):
        # If there was exactly one line in the resolution, then destructure the
        # markdown parser's return value, i.e. remove the paragraph layer.
        for found in element.findall(".//doc_uri[@contentLines='1']"):
            if len(found) == 1:
                if found[0].tag == 'paragraph':
                    # Destructure by boosting the children.
                    paragraph = found[0]
                    found.remove(paragraph)
                    found.extend(paragraph[:])
                else:
                    raise NotImplementedError(
                        "Single content line isn't paragraph"
                        f' {ET_string(found)}.')
            elif len(found) != 0:
                raise NotImplementedError(
                    'Single content line but multiple child elements'
                    f' {ET_string(found)}.')

    @classmethod
    def _lift_trees(cls, element, leaveMarkers):
        # insertIndex = None
        # insertParent = None
        # def insert_here(insertion):
        #     insertParent.insert(insertIndex, insertion)
        #     insertIndex += 1

        while True:
            grandparent, parent, docElement = ET_grandparent(element, 'doc_uri')
            if grandparent is None:
                break
            parentIndex = ET_index(grandparent, parent)
            docIndex = ET_index(parent, docElement)
            
            # Create doc markers.
            if leaveMarkers:
                docStart = ET.Element('doc')
                ET_copy_attr(docElement, docStart, ('source', 'uri'))
                startText = ET_string(docStart)
                if startText.endswith(' />'):
                    startText = ''.join((startText[:-3], startText[-1]))
                else:
                    raise AssertionError(
                        'Wrong ending on doc start marker.\nExpected: " />"'
                        f'\nActual: "{startText}".')
                docStart.text = startText
                docStart.set('layout', 'marker')
                docEnd = ET.Element('doc', {'layout': 'marker'})
                ET_copy_attr(docElement, docEnd, ('source', 'uri'))
                docEnd.text = '</doc>'
            else:
                docStart = None
                docEnd = None

            # Remove the doc_uri from its parent. It won't be released yet
            # because the docElement variable retains a reference to it.
            del parent[docIndex]

            insertIndex = docIndex
            insertParent = parent
            for child in docElement:
                if (
                    insertParent is parent
                    and not cls._can_contain(parent, child)
                ):
                    insertParent = grandparent
                    insertIndex = parentIndex + 1
                
                if docStart is not None:
                    insertParent.insert(insertIndex, docStart)
                    insertIndex += 1
                    docStart = None
                insertParent.insert(insertIndex, child)
                insertIndex += 1

            # If the doc_uri had no child elements, the start marker won't have
            # been inserted.
            if docStart is not None:
                insertParent.insert(insertIndex, docStart)
                insertIndex += 1
                docStart = None

            if docEnd is not None:
                insertParent.insert(insertIndex, docEnd)
                insertIndex += 1
                # insert_here(docEnd)

            # If insertion moved to the grandparent, then any remaining
            # children to the right of the doc_uri should be moved to a new
            # parent. The new parent should have the same tag as the original 
            # parent and be after the docEnd marker.
            if insertParent is grandparent and len(parent) > docIndex:
                tailParent = ET.Element(parent.tag)
                ET_copy_attr(parent, tailParent)
                tailParent.extend(parent[docIndex:])
                del parent[docIndex:]
                insertParent.insert(insertIndex, tailParent)
                insertIndex += 1
                # insert_here(tailParent)

            # Remove the parent if the doc_uri was its only child and has been
            # boosted to the grandparent so the parent is now empty.
            if docIndex == 0 and len(parent) == 0:
                del grandparent[parentIndex]

        found = element.find(".//paragraph//paragraph")
        if found is not None:
            raise AssertionError(
                f'Nested paragraph: {ET_string(found)}'
                f'\nunder:{ET_string(element)}')

    @classmethod
    def _can_contain(cls, parentElement, childElement):
        # The renderer sets an attribute layout:span on all span elements.
        layout = childElement.get('layout')
        if layout == 'span' or layout == 'marker':
            return True

        parent = parentElement.tag
        if parent == 'paragraph' or parent == 'header':
            # Paragraphs and headers cannot contain any block type.
            return False

        child = childElement.tag
        if parent == 'list_item':
            if child == 'paragraph' or child == 'list':
                return True
            if child == parent:
                return False

        if parent == 'list':
            return child == 'list_item'

        raise NotImplementedError(
            f"Don't know if {parent} can or cannot contain {child}.")
    
    @classmethod
    def _set_newlines(cls, element):
        detector = 'setNewlines'
        outcome = 'newlines'
        for found in element.findall(f'.//*[@{detector}]'):
            # Find an immediate child with tag equal to the value of the
            # detector.
            found.set(outcome, str(
                1 if found.find(f'./{found.get(detector)}') is None else 2
            ))

    @classmethod
    def _resolve_splitters(cls, markdownElement):
        while True:
            grandparent, parent, splitter = ET_grandparent(
                markdownElement, f'*[@splitter="{str(True)}"]')
            if grandparent is None:
                break
            splitter.set('splitter', str(False))

            parentIndex = ET_index(grandparent, parent)
            splitterIndex = ET_index(parent, splitter)
            parent.set('split', f'{splitterIndex} {ET_string(splitter)}')
            if splitterIndex > 0:
                parent.set(
                    'split',
                    f'{splitterIndex} {ET_string(parent[splitterIndex - 1])}')
                splitParent = ET.Element(parent.tag)
                splitParent.extend(parent[splitterIndex:])
                splitParent.set('split', 'new')
                ET_copy_attr(parent, splitParent, 'newlines')
                del parent[splitterIndex:]
                grandparent.insert(parentIndex + 1, splitParent)

    @classmethod
    def _join_texts(cls, markdownElement):
        # Join together adjacent `text` elements. This has the side effect of
        # discarding attributes of the second and subsequent elements. They'd
        # only have diagnostic transcript so it isn't too bad.

        # The XPath finds parent elements of text elements.
        for found in markdownElement.findall('.//text/..'):
            consolidated = None
            removals = []
            # Go through the list start to finish. Any element that should be
            # consolidated with the previous element is added to the removals
            # list. Removals are processed after, to avoid modifying the list in
            # the middle of the enumeration.
            for index, child in enumerate(found):
                if child.tag == 'text':
                    if consolidated is None:
                        consolidated = child
                    else:
                        # The removals list will be highest first.
                        removals.insert(0, index)
                        consolidated.text += child.text
                else:
                    consolidated = None
            if len(removals) > 0:
                # found.set('consolidated', str(removals))
                found.set('consolidated', str([
                    [removal, found[removal].text] for removal in removals]))
                for index in removals:
                    del found[index]

    @classmethod
    def _strip_leading_newlines(cls, element):
        # This is a carryover from the ad hoc Doctor.
        #
        # It's possible to get a leading line break, in some cases in which a
        # doc: substitution was made. Remove these here.
        for paragraph in element.findall('.//paragraph/text/..'):
            found = paragraph.find('./text')
            if found is None or found.text is None:
                continue
            stripped = found.text.lstrip("\r\n")
            if stripped != found.text:
                found.set('stripped', str(len(found.text) - len(stripped)))
                found.text = stripped

    @classmethod
    def _output(cls, elementIterator, writer, maxWidth):
        for element in elementIterator:
            if element.tag == 'line':
                writer.write(element.text)
                continue

            markdown = element.find('./markdown')
            if markdown is None:
                raise AssertionError(f'No <markdown> in "{ET_string(child)}"')
            iterator = cls._markdown_prints(markdown)
            iterator = cls._indent_prints(iterator)

            iterator = cls._comment_outputs(element, iterator, maxWidth)

            for line in iterator:
                writer.write(line)
            
    @classmethod
    def _comment_outputs(cls, commentElement, iterator, maxWidth):
        source = commentElement.get('source')
        if source is None:
            AssertionError(
                "Comment doesn't have source attribute"
                f' {ET_string(commentElement)}')
        swift = Path(source).suffix.lower() == '.swift'
        indentStart = int(commentElement.get('indentStart'))

        indentContinue = indentStart + 1
        lineStart = ''.join((
            " " * indentContinue,
            "" if swift else "* "
        ))

        prefix = ''.join((" " * indentStart, "/**", "\n" if swift else " "))
        if swift:
            yield prefix
            prefix = None

        prints = ET.Element('prints')
        commentElement.insert(0, prints)
        for index, output in enumerate(iterator):
            hanging = cls._at_command_hanging(output, swift)
            prints.append(output)

            if prefix is None:
                prefix = lineStart
            
            if hanging is None:
                # Verbatim lines, like in a code block.
                yield prefix
                yield output.text
            else:
                subsequent = ''.join((prefix, " " * hanging))
                lines = textwrap.wrap(
                    ''.join((prefix, output.text)),
                    width=maxWidth,
                    # initial_indent=prefix
                    subsequent_indent=subsequent,
                    drop_whitespace=True
                )
                if len(lines) == 0:
                    # If the input text is empty, wrap() throws away everything.
                    lines = [""]
                for index, line in enumerate(lines):
                    if index > 0:
                        yield "\n"
                    # yield f"{index:>2} {len(line):>2} {len(subsequent):>2}"
                    if len(line) < len(subsequent):
                        yield subsequent
                    else:
                        yield line

            # yield f'{hangingText}!{logicalLine}'
            if output.get('bareLine') is None:
                yield "\n"
            prefix = None

        if prefix is not None:
            yield prefix

        yield "\n"
        yield " " * indentContinue
        yield '*/'
    
    @classmethod
    def _at_command_hanging(cls, element, swift):
        hangingStr = element.get('hanging')
        if hangingStr is None:
            return None
        hanging = int(hangingStr)
        match = cls.atCommand.match(element.text[hanging:])
        if match is None:
            if element.text.startswith("@"):
                warning = ET.Element('warning')
                warning.text = 'Warning: Apparent unrecognised at-command'
                element.insert(0, warning)
            return hanging

        if match.start() != 0:
            raise AssertionError(
                "At-command doesn't start at zero" f'\n{ET_string(element)}')

        # lineAfter = line[match.end():]
        prefix = None

        matchedGroups = matched_groups(match)
        element.set('atGroups', matchedGroups)
        group = matchedGroups[0]
        if not group.startswith('command'):
            raise AssertionError(
                "Group name doesn't start with " f'"command": "{group}"'
                f'\n{ET_string(element)}')
        value = match.group(group)
        lowered = f"@{value.lower()} "

        # Xcode will highlight either keyword Returns or Parameter, if there is
        # exactly one space between the hyphen and the keyword.
        if group == 'commandParameter':
            prefix = "".join((
                "- Parameter " if swift else lowered,
                match.group('name'),
                ":" if swift else "",
                " "
            ))
        elif group == 'commandDrop':
            prefix = "" if swift else lowered
        elif group == 'commandCapitalise':
            prefix = (
                f"- {value.capitalize()}: " if swift else lowered)
        elif group == 'commandReturn':
            # The returns at-command has special handling. The RE captures
            # either @return or @returns as just return. The code here changes
            # it to a consistent Returns, for Swift, or @return otherwise.
            prefix = "- Returns: " if swift else lowered
        elif group == 'commandIgnore':
            return hanging

        if prefix is None:
            raise AssertionError(
                f'Matched at-command "{group}" not handled'
                f'\n{ET_string(element)}')
        element.set('atPrefix', prefix)
        
        element.text = ''.join((
            element.text[:hanging], prefix, match.string[match.end():]
        ))

        return hanging + len(prefix)

    @classmethod
    def _markdown_prints(cls, element, indentWidth=4):
        wrap = element.get('wrap')
        if wrap is not None:
            yield cls._print(wrap)

        headerLevel = element.get('level')
        if headerLevel is not None:
            for _ in range(int(headerLevel)):
                yield cls._print('#')
            yield cls._print(' ')

        indent = element.get('verbatim') == 'block'
        for output in cls._text_prints(element):
            if indent:
                output.set('indentFixed', str(indentWidth))
            yield output

        lastIndex = len(element) - 1
        while lastIndex >= 0 and element[lastIndex].tag == 'doc':
            lastIndex -= 1

        lastLayout = None
        ordered = element.get('ordered')
        if ordered is not None:
            ordered = ordered.lower() == str(True).lower()
        
        for index, child in enumerate(element):
            if ordered is not None:
                listIndicator = (
                    f'{index + 1 if ordered else ""}{"." if ordered else "-"}')
                yield cls._print(
                    f'{listIndicator:<{indentWidth}}'
                    , {'indent': str(indentWidth)}
                )

            lastLayout, transition = cls._layout_transition(lastLayout, child)
            if transition is not None:
                yield transition

            # Recursive call.
            for output in cls._markdown_prints(child, indentWidth):
                yield output

            if ordered is not None:
                yield cls._print(None, {'indent': str(0 - indentWidth)})

            if index < lastIndex:
                newlinesStr = child.get('newlines')
                if newlinesStr is not None:
                    yield cls._print(None, {'newlines': newlinesStr})

        if wrap is not None:
            yield cls._print(wrap)
    
    @classmethod
    def _layout_transition(cls, lastLayout, element):
        # Insert a newline if the child type changes from span to block. Block
        # layout items have no `layout` attribute.
        layout = element.get('layout')
        if lastLayout == 'span' and layout is None:
            return layout, cls._print(None, {'newlines': str(1)})
        if layout == 'marker':
            # Ignore markers for the purposes of detecting layout transition.
            return lastLayout, None
        return layout, None

    @classmethod
    def _text_prints(cls, element):
        if element.text is None:
            return
        if element.get('verbatim') is None:
            # Collapse any adjacent whitespace into a single space. This will
            # catch \r\n or \n or "  ".
            yield cls._print(re.sub(r'\s+', ' ', element.text))
        else:
            return_ = cls._print(element.text)
            ET_copy_attr(element, return_, 'verbatim')
            yield return_

    @classmethod
    def _print(cls, text, attributes=None, tag='print'):
        element = (
            ET.Element(tag) if attributes is None else
            ET.Element(tag, attributes))
        if text is not None:
            element.text = text
        return element

    @classmethod
    def _indent_prints(cls, iterator):
        # Buffer up print commands and output logical lines.
        indent = 0
        hanging = 0
        lineTexts = []
        tag = None
        attributes = None
        for element in iterator:
            if tag is None:
                tag = element.tag
            
            diagnostic = False

            indentChange = element.get('indent')
            if indentChange is not None:
                diagnostic = True
                indent += int(indentChange)
                if indent > hanging:
                    hanging = indent

            splitMessage = element.get('split')
            if splitMessage is not None:
                if attributes is None:
                    attributes = {}
                attributes['split'] = splitMessage

            if element.text is None:
                diagnostic = True
            else:
                if element.get('verbatim') is None:
                    lineTexts.append(element.text)
                else:
                    if len(lineTexts) > 0:
                        raise AssertionError(
                            "Verbatim print but buffer isn't empty"
                            f'\n{lineTexts}\n{ET_string(element)}'
                        )
                    indentFixedAttribute = element.get('indentFixed')
                    indentFixed = (
                        "" if indentFixedAttribute is None
                        else " " * int(indentFixedAttribute))
                    for line in (
                        textwrap.indent(element.text, indentFixed)
                        .splitlines(True)
                    ):
                        # The bareLine must be set because splitLines(True)
                        # retains the eol characters.
                        indentPrint = ET.Element(tag, {'bareLine': str(True)})
                        ET_copy_attr(element, indentPrint, 'verbatim')
                        indentPrint.text = line
                        yield indentPrint
            
            newlinesStr = element.get('newlines')
            if newlinesStr is not None:
                diagnostic = True
                for _ in range(int(newlinesStr)):
                    if attributes is None:
                        attributes = {}
                    attributes['hanging'] = str(hanging)
                    indentPrint = ET.Element(tag, attributes)
                    attributes = None
                    indentPrint.text = ''.join(lineTexts)
                    # If the next line is indented, this line has hanging
                    # indent.
                    yield indentPrint
                    del lineTexts[:]
                    if indent > 0:
                        lineTexts.append(" " * indent)
                    hanging = indent
            
            if diagnostic and False:
                lineTexts.append(ET_string(element))

        if tag is not None and len(lineTexts) > 0:
            indentPrint = ET.Element(tag, {
                'hanging': str(hanging),
                'bareLine': str(True)
            })
            indentPrint.text = ''.join(lineTexts)
            yield indentPrint
            del lineTexts[:]

