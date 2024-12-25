# Run with Python 3
# Copyright 2024 Omnissa, LLC.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Markdown Manipulator. Part of the Doctor documentation tool.
No standalone capability.
"""
# Exit if run other than as a module.
if __name__ == '__main__':
    print(__doc__)
    raise SystemExit(1)

#
# Standard library imports, in alphabetic order.
#
# Module for enumerated types.
# https://docs.python.org/3/library/enum.html
import enum
#
# Text wrapping module.
# https://docs.python.org/3/library/textwrap.html
from textwrap import wrap
#
# Local imports, in alphabetic order, would go here.

class BlockType(enum.Enum):
    #
    # Types from original Markdown, in the same order as here:
    # https://github.com/lepture/mistune#block-level
    BLOCK_CODE = enum.auto()
    HEADER = enum.auto()
    LIST = enum.auto()
    LIST_ITEM = enum.auto()
    PARAGRAPH = enum.auto()
    #
    # Custom types, in alphabetic order.
    DOC_URI = enum.auto()

class SpanType(enum.Enum):
    # Same order as here: https://github.com/lepture/mistune#span-level
    AUTOLINK = enum.auto()
    CODESPAN = enum.auto()
    DOUBLE_EMPHASIS = enum.auto()
    EMPHASIS = enum.auto()
    # NEWLINE = enum.auto()
    TEXT = enum.auto()
    INLINE_HTML = enum.auto()

class MarkdownItem:
    def __init__(self, blockType, spanType, contents, custom=None):
        # ToDo: Check consistent types and raise if not.
        self.blockType = blockType
        self.spanType = spanType
        self.contents = contents
        self.custom = custom
    
    @property
    def type(self):
        return self.spanType if self.blockType is None else self.blockType
        
    def asTuple(self):
        return (self.type.name,) + (
            tuple() if self.custom is None else (self.custom,)
        ) + (
            (self.contents,) if isinstance(self.contents, str) else tuple(
                content.asTuple() if isinstance(content, MarkdownItem)
                else (content,)
                for content in self.contents)
        )
    
    def __repr__(self):
        return self.asTuple().__repr__()
    
    def output(self, isLast=False, maxWidth=None):
        if maxWidth is not None and maxWidth < 1:
            maxWidth = 1
        if self.spanType is not None:
            outputs = MarkdownItem.output_spans(self.contents)
            if self.spanType is SpanType.EMPHASIS:
                return outputs.join(('*',) * 2)
            if self.spanType is SpanType.DOUBLE_EMPHASIS:
                return outputs.join(('**',) * 2)
            if self.spanType is SpanType.CODESPAN:
                return outputs.join((r'`',) * 2)
            if (self.spanType is SpanType.TEXT
                or self.spanType is SpanType.INLINE_HTML
                or self.spanType is SpanType.AUTOLINK
            ):
                return outputs
            raise NotImplementedError(str(self))
        
        outputs = None
        eols = 2
        if self.blockType is BlockType.HEADER:
            outputs = ["#" * self.custom['level'], " "
                       # No maxWidth for headers.
                       , MarkdownItem.output_spans(self.contents)]
            eols = 1
        
        if self.blockType is BlockType.PARAGRAPH:
            outputs = [MarkdownItem.output_spans(
                self.contents, maxWidth, self.custom)]

        if self.blockType is BlockType.LIST:
            childOutputs = MarkdownItem.output_all(self.contents, maxWidth)
            outputs = []
            for index, childOutput in enumerate(childOutputs):
                outputs.extend((
                    '{:<4}'.format(
                        '{:d}.'.format(index + 1) if self.custom['ordered']
                        else "-"),
                    childOutput
                ))
        
        if self.blockType is BlockType.LIST_ITEM:
            childOutputs = MarkdownItem.output_all(
                self.contents, maxWidth if maxWidth is None else maxWidth - 4)

            outputs = []
            # Indent every line except the first of each with four spaces. The
            # LIST output, above, will indent the first line with whatever's
            # suitable to the list type.
            for index, line in enumerate(''.join(childOutputs).splitlines(True)):
                outputs.extend(('    ' if index > 0 else '', line))

            eols = 2 if self.contents[-1].type is BlockType.PARAGRAPH else 1
        
        if self.blockType is BlockType.BLOCK_CODE:
            # No line-wrapping in a code block.
            # Indent every line by four spaces.
            outputs = [
                ''.join(('    ', line)) for line in "".join(
                    MarkdownItem.output_all(self.contents, None)
                    ).splitlines(True)
            ]
            
            # Mistune preserves any line breaks at the end of a code block, so
            # don't add any here. Note that the line breaks would be unnecessary
            # if the code block is at the end of a comment.
            eols = 0

        if outputs is None:
            raise NotImplementedError(str(self))
        
        return ''.join(outputs + ['' if isLast else "\n" * eols])

    
    # https://docs.python.org/3/library/functions.html#staticmethod
    @staticmethod
    def output_all(iterator, maxWidth=None):
        if maxWidth is not None and maxWidth < 1:
            maxWidth = 1

        items = (iterator,) if isinstance(iterator, str) else tuple(iterator)
        itemCount = len(items)

        result = []
        spans = None
        
        # The code treats blocks and spans differently:
        #
        # -   Blocks are output as they are encountered in the iterator.
        #
        # -   Spans are accumulated until:
        #     -   The iterator is finished.
        #     -   There is a block item in the iterator.
        #
        #     The accumulated spans are then output, by calling output_spans.
        #
        for index, item in enumerate(items):
            if isinstance(item, MarkdownItem) and item.blockType is not None:
                if spans is not None:
                    result.append(''.join((
                        MarkdownItem.output_spans(spans, maxWidth), "\n")))
                    spans = None
                    
                result.append(item.output(index == itemCount - 1, maxWidth))
            
            else:
                if spans is None:
                    spans = []
                spans.append(item)
        
        if spans is not None:
            result.append(MarkdownItem.output_spans(spans, maxWidth))

        return result
        
    @staticmethod
    def output_spans(iterator, maxWidth=None, subsequent_indent=None):
        '''\
        Only specify maxWidth if calling from output_all or a block output().
        '''
        if maxWidth is not None and maxWidth < 1:
            maxWidth = 1

        outputs = [iterator] if isinstance(iterator, str) else [
                span if isinstance(span, str) else span.output()
                for span in iterator]
        # print('output_spans 0', maxWidth, outputs)
        
        # It's possible to get a leading line break, in some cases in which a
        # doc: substitution was made. Remove these here.
        try:
            outputs[0] = outputs[0].lstrip("\r\n")
        except IndexError:
            pass
        
        joined = ''.join(outputs)

        # print('output_spans 1', maxWidth, joined.encode())
        if maxWidth is None:
            return joined
        
        joined = " ".join(joined.splitlines())
        
        # print('output_spans 2', maxWidth, joined.encode())
        return "\n".join(wrap(
            joined, maxWidth
            , subsequent_indent=" " * (0 if subsequent_indent is None
                                       else subsequent_indent)
        ))
        # Near here the code has lost the original EOLs, which might have been
        # CR-LF. Worry about that later if necessary.
