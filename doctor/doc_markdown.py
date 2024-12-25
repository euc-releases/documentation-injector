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

#
# Standard library imports, in alphabetic order.
#
# JSON module. Only used for verbose diagnostic output.
# https://docs.python.org/3/library/json.html
import json
#
# File path module.
# https://docs.python.org/3/library/os.path.html
import os.path
#
# Regular expressions module.
# https://docs.python.org/3/library/re.html
import re
#
# Module for manipulation of the import path.
# https://docs.python.org/3/library/sys.html#sys.path
import sys
#
# Local imports
#
# Module with Comment Block, to which this module adds Markdown items.
from doctor.comment_block import CommentBlock
#
# Module with a handy RE access utility.
from doctor.comment_line import CommentLine
#
# Module for Markdown semantic items.
from doctor.markdown import BlockType, SpanType, MarkdownItem
#
# Markdown parser module.
# https://github.com/lepture/mistune
import mistune
# Sorry, you have to ensure that your local copy of the mistune repository has
# been added to sys.path before importing the doctor package. There is a
# subroutine to do that in the doctor.py script.

# The DocResolver is in its own class to keep the mistune.Renderer subclass
# tidy. It only has class constants and class methods.
class DocResolver:
    blockContain = {
        BlockType.PARAGRAPH.name: {
            'can': tuple(SpanType),
            'cannot': tuple(BlockType)
        },
        BlockType.HEADER.name: {
            'can': tuple(SpanType),
            'cannot': tuple(BlockType)
        },
        BlockType.LIST_ITEM.name: {
            'can': tuple(SpanType) + (BlockType.LIST, BlockType.PARAGRAPH),
            'cannot': (BlockType.LIST_ITEM,)
        }
    }
    
    # Constant regular expressions get compiled here. See CommentLine class for
    # short discussion.
    #
    # Following syntax elements are used:
    #
    # -   Python r'...' for raw strings that don't get backslash expansion.
    # -   (?:...) for non-capture group.
    # -   \s matches end-of-line characters, because they are whitespace.
    #     \s+ requires at least one, which means that it doesn't match at the
    #     very start of a string, which is what's wanted here.
    # -   Caret in a capture group doesn't capture the newline characters, and
    #     dollar doesn't either if they precede the pattern.
    # -   Python string continuation, some having comments in between.
    #
    # Next pattern is used to split a text with embedded at commands.
    atPattern = re.compile(
        r'\s+(^@(?:'
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
        r'))', re.MULTILINE)

    @classmethod
    def can_contain(cls, blockType, markdownItem):
        try:
            if markdownItem.type in cls.blockContain[blockType.name]['can']:
                return True
            if markdownItem.type in cls.blockContain[blockType.name]['cannot']:
                return False
        except Exception as exception:
            raise exception.__class__(
                'Block contain configuration incomplete for {} and {}.'.format(
                    blockType.name, markdownItem.type.name)) from exception
        
        raise AssertionError(
            "Don't know if {} can or cannot contain {}.".format(
                blockType.name, markdownItem))

    @classmethod
    def resolve_all_doc_uri(cls, blockType, text, custom=None):
        output = []
        outputTail = None
        for child in text:
            if child.blockType is BlockType.DOC_URI:
                for grandchild in child.contents:
                    if cls.can_contain(blockType, grandchild):
                        if outputTail is None:
                            outputTail = []
                        outputTail.append(grandchild)
                    else:
                        if outputTail is not None:
                            output.append(MarkdownItem(
                                blockType, None, outputTail, custom))
                            outputTail = None
                        output.append(grandchild)
            else:
                if outputTail is None:
                    outputTail = []
                outputTail.append(child)
                
        if outputTail is not None:
            output.append(MarkdownItem(blockType, None, outputTail, custom))
        
        return output
    
    @classmethod
    def process_at_commands(cls, iterator):
        """\
        Take an iterator of paragraphs and split each to ensure that any
        at-commands are at the start of a paragraph. Also:
        
        -   Join adjacent texts, to prevent wrong handling of parameter names
            with embedded _ characters later.
        -   Strip leading whitespace from every line after the first in each
            paragraph.
        """
        # Splitting is necessary if there is an embedded newline-at in a text
        # item that is a direct child of the paragraph.

        for paragraph in iterator:
            
            # Don't attempt to resolve at commands in code blocks.
            if paragraph.blockType is BlockType.BLOCK_CODE:
                yield paragraph
                continue
            # Unresolved at this time is that non-paragraphs sometimes come
            # through here, like lists also come through here. It seems to be OK
            # though, because those could have at commands that need to be
            # resolved.

            # Start a list of Markdown items that will become child items in the
            # yielded paragraphs.
            contents = []

            for span in cls.consolidate_texts(paragraph.contents):
                if span.spanType is not SpanType.TEXT:
                    contents.append(span)
                    continue

                if not isinstance(span.contents, str):
                    raise AssertionError(
                        "Text in paragraph contents aren't str.")
                
                # The following returns a list with an odd number of items,
                # because the pattern has a capture group.
                splits = re.split(cls.atPattern, "".join(tuple(
                    # Strip any leading whitespace from lines after the first.
                    (line if lineIndex <= 0 else line.lstrip())
                    for lineIndex, line in enumerate(
                        span.contents.splitlines(True))
                )))

                # Following lines are handy to check what's coming out of the re
                # split.
                # for index, split in enumerate(splits):
                #     print('{:>02d} "{}"'.format(index, split))

                # Note that splits never has an even number of items. If splits
                # has one item, this loop runs zero times.
                for splitIndex in range(0, len(splits) - 2, 2):
                    if not(splits[splitIndex] == "" and splitIndex == 0):
                        contents.append(MarkdownItem(
                            None, SpanType.TEXT
                            , splits[splitIndex] if splitIndex <= 0
                            else ''.join(splits[splitIndex - 1: splitIndex + 1])
                        ))
                    yield MarkdownItem(
                        paragraph.blockType, None, contents, paragraph.custom)
                    contents = []
                
                # Sweep up the items that weren't processed by the loop, either
                # one or two items.
                contents.append(MarkdownItem(
                    None, SpanType.TEXT, ''.join(splits[-2:])))
                
            yield MarkdownItem(
                paragraph.blockType, None, contents, paragraph.custom)
    
    @classmethod
    def consolidate_texts(cls, iterator):
        pending = None
        contents = None
        
        for span in iterator:
            if not isinstance(span, MarkdownItem):
                raise AssertionError("Item in text consolidation isn't"
                                     " MarkdownItem: {}".format(type(span)))
            
            if span.spanType is SpanType.TEXT:
                if contents is None and pending is None:
                    pending = span
                else:
                    if contents is None:
                        contents = []
                    if pending is not None:
                        contents.append(pending.contents)
                        pending = None
                    contents.append(span.contents)
            else:
                if pending is not None:
                    yield pending
                    pending = None
                if contents is not None:
                    yield MarkdownItem(None, SpanType.TEXT, ''.join(contents))
                    contents = None
                yield span
        
        if pending is not None:
            yield pending
            pending = None
        if contents is not None:
            yield MarkdownItem(None, SpanType.TEXT, ''.join(contents))
            contents = None

class DocRenderer(mistune.Renderer):
    
    docPath = None
    
    def __init__(self, docGetter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verbose = False
        self.docGetter = docGetter
    
    def doc_uri(self, groups):
        name, uri = CommentLine.group_startswith(groups, 'doc')
        if self.verbose:
            print('DocRenderer doc_uri', groups, name)
        
        contentLines = self.docGetter.get_content(uri, self.docPath)
        content = ''.join(contentLines)
        if content == "":
            return []

        markdownItems = MarkdownParser(self.docGetter).get_markdown_items(
            self.docPath, content)

        # If len(contentLines) is 1 then destructure the markdown() return
        # value, i.e. remove the paragraph layer.
        if len(contentLines) == 1:
            if markdownItems[0].type is BlockType.PARAGRAPH:
                markdownItems = markdownItems[0].contents
            else:
                raise NotImplementedError()

        return [MarkdownItem(BlockType.DOC_URI, None ,markdownItems)]

    #
    # Block item overrides.
    #
    # Same order as here: https://github.com/lepture/mistune#block-level
    def block_code(self, code, language=None):
        if self.verbose:
            print('DocRenderer block_code(,{},{})'.format(code, language))
        return [MarkdownItem(BlockType.BLOCK_CODE, None, code)]

    def block_quote(self, text):
        raise NotImplementedError()
    def block_html(self, html):
        raise NotImplementedError()

    def header(self, text, level, raw=None):
        if self.verbose:
            print('DocRenderer header(,{},{},{})'.format(text, level, raw))
        return DocResolver.resolve_all_doc_uri(
            BlockType.HEADER, text, {'level': level})
    
    def hrule(self):
        raise NotImplementedError()

    def list(self, body, ordered=True):
        if self.verbose:
            print('DocRenderer list(,\n{}\n,{})'.format(body, ordered))
        return DocResolver.resolve_all_doc_uri(
            BlockType.LIST, body, {'ordered': ordered})

    def list_item(self, text):
        if self.verbose:
            print('DocRenderer list_item(,{})'.format(text))
        return DocResolver.resolve_all_doc_uri(BlockType.LIST_ITEM, text)

    def paragraph(self, text):
        resolved = DocResolver.resolve_all_doc_uri(BlockType.PARAGRAPH, text)
        outputs = [output
                   for output in DocResolver.process_at_commands(resolved)]
        if self.verbose:
            def json_dump(iterator, indent=4):
                return json.dumps(tuple(
                    item.asTuple() for item in iterator), indent=4)
            print('DocRenderer paragraph(,\n{})\nresolved{}\noutputs{}'.format(
                text, json_dump(resolved), json_dump(outputs)))
        return outputs

    def table(self, header, body):
        raise NotImplementedError()
    def table_row(self, content):
        raise NotImplementedError()
    def table_cell(self, content, **flags):
        raise NotImplementedError()
    
    #
    # Span item overrides.
    #
    # Same order as here: https://github.com/lepture/mistune#span-level
    def autolink(self, link, is_email=False):
        if self.verbose:
            print('DocRenderer autolink(,{},{})'.format(link, is_email))
        return [MarkdownItem(None, SpanType.AUTOLINK, link)]
    def codespan(self, text):
        if self.verbose:
            print('DocRenderer codespan(,\n{})'.format(text))
        return [MarkdownItem(None, SpanType.CODESPAN, text)]
    def double_emphasis(self, text):
        if self.verbose:
            print('DocRenderer double_emphasis(,\n{})'.format(text))
        return [MarkdownItem(None, SpanType.DOUBLE_EMPHASIS, text)]
    def emphasis(self, text):
        if self.verbose:
            print('DocRenderer emphasis(,\n{})'.format(text))
        return [MarkdownItem(None, SpanType.EMPHASIS, text)]
    def image(self, src, title, alt_text):
        raise NotImplementedError()
    def linebreak(self):
        raise NotImplementedError()
    def newline(self):
        if self.verbose:
            print('DocRenderer newline(,)')
        # return [MarkdownItem(None, SpanType.NEWLINE, "")]
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
        if self.verbose:
            print('DocRenderer text(,{}\n{})'.format(len(text), text))
        return [MarkdownItem(None, SpanType.TEXT, text)]
    def inline_html(self, text):
        if self.verbose:
            print('DocRenderer inline_html(,\n{})'.format(text))
        return [MarkdownItem(None, SpanType.INLINE_HTML, text)]

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
        return self.renderer.doc_uri(match.groupdict())

class MarkdownParser:
    # Not enjoying the implementation of docPath in this class. It's needed in
    # order to resolve relative doc: URIs but it's unclear how best to do it.

    # @property
    # def docPath(self):
    #     return self._renderer.docPath
    # @docPath.setter
    # def docPath(self, docPath):
    #     self._renderer.docPath = docPath
    # 
    def __init__(self, docGetter):
        self._renderer = DocRenderer(docGetter)
        inlineLexer = DocInlineLexer(self._renderer)
        inlineLexer.enable_doc_uri()
        self._markdown = mistune.Markdown(
            renderer=self._renderer, inline=inlineLexer
            , rules=DocInlineGrammar())
    
    def get_markdown_items(self, docPath, *args, **kwargs):
        self._renderer.docPath = docPath
        # Uncomment the following line to get a lot of render dump.
        # self._renderer.verbose = True
        return self._markdown(*args, **kwargs)
    
    def read(self, iterator, sourcePath):
        for item in iterator:
            if isinstance(item, CommentBlock):
                try:
                    item.markdownItems = self.get_markdown_items(
                        sourcePath, "".join(item.get_texts()))
                except Exception as exception:
                    raise exception.__class__(
                        'Error getting Markdown items. Block:{}.'.format(item)
                        ) from exception
            yield item
