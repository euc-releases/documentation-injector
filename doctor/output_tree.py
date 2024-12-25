# Run with Python 3
# Copyright 2024 Omnissa, LLC.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Output tree subroutines. Part of the Doctor documentation tool.
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
# ElementTree utility methods.
from doctor.markdown_tree import ET_copy_attr
# Regular expression utility method.
from doctor.mistree import matched_groups

# Internal utility methods

def _output(text, attributes=None, tag='output'):
    element = (
        ET.Element(tag) if attributes is None else
        ET.Element(tag, attributes))
    if text is not None:
        element.text = text
    return element

def _layout_transition(lastLayout, element):
    # Insert a newline if the child type changes from span to block. Block
    # layout items have no `layout` attribute.
    layout = element.get('layout')
    if lastLayout == 'span' and layout is None:
        return layout, _output(None, {'newlines': str(1)})
    if layout == 'marker':
        # Ignore markers for the purposes of detecting layout transition.
        return lastLayout, None
    return layout, None

def _text_outputs(element):
    if element.text is None:
        return
    if element.get('verbatim') is None:
        # Collapse any adjacent whitespace into a single space. This will
        # catch \r\n or \n or "  ".
        yield _output(re.sub(r'\s+', ' ', element.text))
    else:
        return_ = _output(element.text)
        ET_copy_attr(element, return_, 'verbatim')
        yield return_

class OutputTree:
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

    def __init__(self, indentWidth=4, maxWidth=80):
        self._indentWidth = indentWidth
        self._maxWidth = maxWidth

    def markdown_outputs(
        self, iterator, tagMarkdown='markdown', tagOutputs='outputs'
    ):
        for element in iterator:
            markdown = element.find(f'./{tagMarkdown}')
            if markdown is not None:
                outputs = ET.Element(tagOutputs)
                outputs.extend(tuple(self._markdown_outputs(markdown)))
                element.append(outputs)
            yield element

    def _markdown_outputs(self, element):
        wrap = element.get('wrap')
        if wrap is not None:
            yield _output(wrap)

        headerLevel = element.get('level')
        if headerLevel is not None:
            for _ in range(int(headerLevel)):
                yield _output('#')
            yield _output(' ')

        indent = element.get('verbatim') == 'block'
        for output in _text_outputs(element):
            if indent:
                output.set('indentFixed', str(self._indentWidth))
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
                yield _output(
                    f'{listIndicator:<{self._indentWidth}}'
                    , {'indent': str(self._indentWidth)}
                )

            lastLayout, transition = _layout_transition(lastLayout, child)
            if transition is not None:
                yield transition

            # Recursive call.
            for output in self._markdown_outputs(child):
                yield output

            if ordered is not None:
                yield _output(None, {'indent': str(0 - self._indentWidth)})

            if index < lastIndex:
                newlinesStr = child.get('newlines')
                if newlinesStr is not None:
                    yield _output(None, {'newlines': newlinesStr})

        if wrap is not None:
            yield _output(wrap)
    
    def indent_outputs(self, iterator, tagOutputs='outputs'):
        for element in iterator:
            found = element.find(f'./{tagOutputs}')
            if found is not None:
                outputs = tuple(_indent_outputs(found))
                found[:] = outputs
            yield element
    
    def write_lines(self, iterator, writer, tagOutputs='outputs'):
        for element in iterator:
            found = element.find(f'./{tagOutputs}')
            if found is None:
                writer.write(element.text)
            else:
                # Next line will modify the outputs in element.
                for output in self._comment_outputs(element, found):
                    writer.write(output)
            yield element

    def _comment_outputs(self, commentElement, iterator, tagOutputs='outputs'):
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

        outputs = []
        for index, output in enumerate(iterator):
            hanging = self._at_command_hanging(output, swift)
            outputs.append(output)

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
                    width=self._maxWidth,
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
        
        found = commentElement.find(f'./{tagOutputs}')
        found[:] = outputs

        if prefix is not None:
            yield prefix

        yield "\n"
        yield " " * indentContinue
        yield '*/'
    
    def _at_command_hanging(self, element, swift):
        hangingStr = element.get('hanging')
        if hangingStr is None:
            return None
        hanging = int(hangingStr)
        match = self.atCommand.match(element.text[hanging:])
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


def _indent_outputs(iterator):
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
