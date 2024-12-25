# Run with Python 3
# Copyright 2024 Omnissa, LLC.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Markdown with doc:// URI resolution. Part of the Doctor documentation tool.
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
# Module for XML handling.
# https://docs.python.org/3.5/library/xml.etree.elementtree.html#module-xml.etree.ElementTree
import xml.etree.ElementTree as ET
#
# Local imports
#
# Markdown parser module.
# https://github.com/lepture/mistune/tree/v1
import mistune
# Sorry, you have to ensure that your local copy of the mistune repository has
# been added to sys.path before importing the doctor package. There is a
# subroutine to do that in the main.py script.

def split_elements(text, firstTag, regularExpression, tags, tailing=False):
    elements = [ET.Element(firstTag)]
    match = regularExpression.search(text)
    matchedGroups = matched_groups(match)
    transcript = []
    if match is not None:
        transcript.append(f"text:'{text}'")
        transcript.append(f'groups:{",".join(matchedGroups)}')

    texts = []
    # Local subroutine to append text to the end of either of the following.
    #
    # -   Texts that will be joined to become the text of the first element.
    # -   Tail of the current last element.
    def set_tail(tail):
        if len(elements) == 1:
            texts.append(tail)
        else:
            if tailing:
                if elements[-1].tail is None:
                    elements[-1].tail = tail
                else:
                    raise AssertionError(
                        f'Overwriting tail {ET.tostring(elements[-1])}'
                        f' with "{tail}".')
            else:
                elements.append(ET.Element(firstTag))
                elements[-1].text = tail

    cursor = 0
    for name in matchedGroups:
        start, end = match.span(name)
        transcript.append(f'{name}:{start},{end}')

        tag = None
        for namePrefix in tags:
            if name.startswith(namePrefix):
                tag = namePrefix
                break
        if tag is None:
            # No elements for other capture groups. Don't advance the cursor
            # nor add an element.
            continue
        
        if start < cursor:
            raise AssertionError()

        # Consume the text before the start of the current group.
        set_tail(text[cursor:start])

        # Add an element for the text in the current group.
        elements.append(ET.Element(tag))
        if end > start:
            elements[-1].text = text[start:end]
        cursor = end

    for element in elements:
        element.set('layout', 'span')

    # Process any remaining unmatched text.
    if len(elements) <= 1:
        # No match. Add the remaining text to the tail.
        set_tail(text[cursor:])
    else:
        # At least one match. Check the remaining text for more matches.
        elements.extend(split_elements(
            text[cursor:], firstTag, regularExpression, tags, tailing))

    elementText = ''.join(texts)
    if elementText == "":
        del elements[0]
    else:
        elements[0].text = elementText
    if len(transcript) > 0:
        elements[0].set('transcript', ' '.join(transcript))
    
    return elements

def matched_groups(match):
    '''\
    Returns a list of the names of all named capture groups that matched
    anything, in order of their start position.
    '''
    if match is None:
        return []
    #
    # Create a list of the names. This is a Python list comprehension with a
    # filtering if condition.
    matchedGroups = [
        key for key, value in match.groupdict().items()
        if value is not None]
    #
    # Sort by position in the matched string.
    def group_start(groupName):
        return match.start(groupName)
    matchedGroups.sort(key=group_start)
    return matchedGroups

class TreeRenderer(mistune.Renderer):
    # _nsPrefix = ""
    # Empty for now but could be changed like "markdown:".

    patternAtCommand = re.compile(
        r'(?P<at_command>@(?:'
            r'returns?' # "return" or "returns".
            r'|'        # Alternate matches separated by pipe character.
            r'param'
            r'|'
            r'brief'
            r'|'
            r'description'
            r'|'
            r'details'
            r'|'
            r'version'
        r'))'
    )

    def _rend(self, tag, children=None, attributes=None, text=None):
        element = (
            ET.Element(tag) if attributes is None else
            ET.Element(tag, attributes))
        element.text = text
        if children is not None:
            element.extend(children)
        return [element]

    #
    # Custom items.
    #
    def doc_uri(self, match):
        matchedGroups = matched_groups(match)
        return self._rend('doc_uri', None, {
            'transcript': f'groups:{",".join(matchedGroups)}',
            'uri': match.group(matchedGroups[0]),
            'resolved': str(False)
        })
    
    # def at_command(self, match):
    #     return self._rend('at_command', None, None, match.groups[1])
    #
    # Block item overrides.
    #
    # Same order as here: https://github.com/lepture/mistune/tree/v1#block-level
    # Note that this is a link to the mistune v1 source.
    def block_code(self, code, language=None):
        return self._rend('block_code', None, {'verbatim': 'block'}, code)

    def block_quote(self, text):
        raise NotImplementedError()
    def block_html(self, html):
        raise NotImplementedError()

    def header(self, text, level, raw=None):
        return self._rend('header', text, {
            'level': str(level), 'newlines': str(1)
        })
    
    def hrule(self):
        raise NotImplementedError()

    def list(self, body, ordered=True):
        return self._rend('list', body, {
            'ordered': str(ordered), 'newlines': str(2)
        })

    def list_item(self, text):
        return self._rend('list_item', text, {'setNewlines': "paragraph"})

    def paragraph(self, text):
        return self._rend('paragraph', text, {'newlines': str(2)})

        # resolved = DocResolver.resolve_all_doc_uri(BlockType.PARAGRAPH, text)
        # outputs = [output
        #            for output in DocResolver.process_at_commands(resolved)]
        # if self.verbose:
        #     def json_dump(iterator, indent=4):
        #         return json.dumps(tuple(
        #             item.asTuple() for item in iterator), indent=4)
        #     print('DocRenderer paragraph(,\n{})\nresolved{}\noutputs{}'.format(
        #         text, json_dump(resolved), json_dump(outputs)))
        # return outputs

    def table(self, header, body):
        raise NotImplementedError()
    def table_row(self, content):
        raise NotImplementedError()
    def table_cell(self, content, **flags):
        raise NotImplementedError()
    
    #
    # Span item overrides.
    #
    # Same order as here: https://github.com/lepture/mistune/tree/v1#span-level
    # Note that this is a link to the mistune v1 source.
    def autolink(self, link, is_email=False):
        raise NotImplementedError()
        # if self.verbose:
        #     print('DocRenderer autolink(,{},{})'.format(link, is_email))
        # return [MarkdownItem(None, SpanType.AUTOLINK, link)]
    def codespan(self, text):
        textElements = self._rend(
            'text', None, {'layout': 'span'}, text)
            # 'verbatim': 'span', 
        return self._rend(
            'codespan', textElements, {'wrap': r'`', 'layout':"span"})
    def double_emphasis(self, text):
        return self._rend(
            'double_emphasis', text, {'wrap': "**", 'layout':"span"})
    def emphasis(self, text):
        return self._rend('emphasis', text, {'wrap': "*", 'layout':"span"})
    def image(self, src, title, alt_text):
        raise NotImplementedError()
    def linebreak(self):
        raise NotImplementedError()
    def newline(self):
        # return self._rend('newline')
        # Previous line would perserve the newline, which might in turn enable
        # perfect reconstruction of the input. Perfect reconstruction isn't
        # possible at time of writing, in some cases. For example, this list:
        #
        #     -   Just a list.
        #
        #         Nothing to see.
        #     -   Middle of the list.
        #
        # The Doctor adds a blank link after 'Nothing to see', which seems
        # tidier and more consistent. So these newline occurrences aren't
        # preserved for now.
        return []
    def link(link, title, content):
        raise NotImplementedError()
    def strikethrough(self, text):
        raise NotImplementedError()

    def text(self, text):
        # The best place to identify at-commands, like @param, seems to be here,
        # in the text. Otherwise, a grammar change might be necessary.
        # This approach didn't seem to work for doc_uri. It seemed that Mistune
        # would split a URL that included a backslash. For that reason, doc_uri
        # has its own lexical rule and regular expression.
        return split_elements(
            text, 'text', self.patternAtCommand, ['at_command'])

    def inline_html(self, text):
        raise NotImplementedError()
        # if self.verbose:
        #     print('DocRenderer inline_html(,\n{})'.format(text))
        # return [MarkdownItem(None, SpanType.INLINE_HTML, text)]

    #
    # Other overrides.
    #
    def placeholder(self):
        return []

class DocInlineGrammar(mistune.InlineGrammar):
    def __init__(self):
        super().__init__()
        # Mistune uses `match` not `search`, so it only consumes at the start.
        # It might be possible to fix it. Might. For now, doc: URIs can only be
        # at the start of a lexical doodad, or enclosed in brackets.
        #
        # Mistune splits https URLs into separate text lexical items for some
        # reason. Following line modifies the grammar to split doc: and http:
        # URLs as well. This seems to be necessary in order to make the doc_uri
        # work in the lexer, below, at least the docBare group. Maybe the
        # docBrackets group works anyway because Mistune already treats square
        # brackets as a separate lexical item. In other words, Mistune separates
        # text at square brackets anyway, because Markdown uses square brackets,
        # there's no need to modify the grammar to make doc: in brackets
        # recognisable.
        pattern = self.text.pattern.replace('https?', '(?:http|https|doc)')
        self.text = re.compile(pattern)

class DocInlineLexer(mistune.InlineLexer):
    def enable_doc_uri(self):
        # add rules. Regular expressions here use the Python `r` raw string
        # syntax.
        self.rules.doc_uri = re.compile(
            r'(?:'
            r'(?P<docBare>doc://\S*)'
            r'|'
            r'(\[)(\s*)(?P<docBrackets>doc://[^\]\s]*)(\s*)(\])'
            r')'
        )
        self.default_rules.insert(1, 'doc_uri')

    def output_doc_uri(self, match):
        return self.renderer.doc_uri(match)

class TreeParser:
    def __init__(self):
        self._renderer = TreeRenderer()
        inlineLexer = DocInlineLexer(self._renderer)
        inlineLexer.enable_doc_uri()
        self._markdown = mistune.Markdown(
            renderer=self._renderer
            , rules=DocInlineGrammar()
            , inline=inlineLexer
        )
    
    def __call__(self, text, tag='markdown'):
        element = ET.Element(tag)
        element.extend(self._markdown(text))

        for atCommand in element.findall('.//at_command'):
            atCommand.set('splitter', str(True))
            atCommand.tag = 'text'

        return element
    
    def read(self, iterator, tagExtract='extract', tagMarkdown='markdown'):
        for element in iterator:
            extract = element.find(tagExtract)
            if extract is not None:
                markdownElement = self(extract.text, tag=tagMarkdown) 
                # ET_copy_attr(element, markdownElement)
                for found in markdownElement.findall(".//doc_uri"):
                    found.set('source', element.get('source'))
                element.append(markdownElement)
            yield element
