# Run with Python 3
# Copyright 2024 Omnissa, LLC.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Doctor processing interface, original ad hoc implementation. This implementation
is deprecated; use the processing.py implementation instead. Part of the Doctor
documentation tool.
No standalone capability.
"""
# Exit if run other than as a module.
if __name__ == '__main__':
    print(__doc__)
    raise SystemExit(1)
#
# Standard library imports would go here, in alphabetic order.
#
# Local imports
#
# Modules in the Doctor package.
from doctor import comment_block, comment_line, doc_markdown, parser

class ProcessingAdHoc:
    def __init__(self, doctorJob):
        self._job = doctorJob
        self._markdownParser = None

    def path_to_comments(self, sourcePath):
        # Following lines build up an iterator nest of initial Doctor stages.
        reader = comment_line.SourceLine.read_file(sourcePath)
        reader = parser.SlashStarsParser.read(reader)
        reader = comment_block.CommentBlock.read(reader, sourcePath)
        for item in reader:
            yield item
    
    def comments_to_outputs(self, iterator, writer, sourcePath, report=None):
        if self._markdownParser is None:
            self._markdownParser = doc_markdown.MarkdownParser(
                self._job.injector)
        for item in self._markdownParser.read(iterator, sourcePath):
            if report is not None:
                itemType = item.__class__.__name__
                if itemType in report:
                    report[itemType] += 1
                else:
                    report[itemType] = 1
            writer.writelines(
                output for output in item.outputs(self._job.maxWidth))
    
    def comments_to_extract(self, iterator, report, docPath, writer):
        firstDoc = True
        for block in iterator:
            if isinstance(block, comment_block.CommentBlock):
                fragment = self._job.add_fragment(
                    report.extractPath, *block.lineNumber, block.get_texts())
                if not self._job.dryRun:
                    block.write_replacement(
                        writer, docPath if firstDoc else "", fragment)
                firstDoc = False
            else:
                writer.writelines(block.outputs())
