# Run with Python 3
# Copyright 2019 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Doctor processing interface. Part of the Doctor documentation tool.
No standalone capability.
"""
# Exit if run other than as a module.
if __name__ == '__main__':
    print(__doc__)
    raise SystemExit(1)
#
# Standard library imports, in alphabetic order.
#
# Module for OO path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path
#
# Module for XML handling.
# https://docs.python.org/3.5/library/xml.etree.elementtree.html#module-xml.etree.ElementTree
import xml.etree.ElementTree as ET
#
# Local imports
#
# Modules in the Doctor package.
from doctor import markdown_tree
from doctor.comment_tree import CommentTree
from doctor.mistree import TreeParser
from doctor.output_tree import OutputTree

class Processing:
    def __init__(self, doctorJob):
        self._job = doctorJob
        self._markdownParser = None
        self._treeParser = TreeParser()
        self._outputTree = OutputTree(maxWidth=self._job.maxWidth)

    def path_to_comments(self, sourcePath):
        path = Path(sourcePath)
        iterator = CommentTree.read_lines(path, 4)
        iterator = CommentTree.comment_blocks(iterator)
        iterator = self._write_xml(iterator, path, '_lines')

        iterator = CommentTree.manipulate_comment_lines(iterator)
        iterator = CommentTree.extract(iterator)
        iterator = self._write_xml(iterator, path, '_comments')
        for element in iterator:
            yield element

    def comments_to_outputs(self, iterator, writer, sourcePath, report=None):
        path = Path(sourcePath)
        iterator = self._report_tags(iterator, report)
        iterator = self._treeParser.read(iterator)
        iterator = self._delete_stage(iterator, 'lines')
        iterator = self._write_xml(iterator, path, '_md')

        iterator = self._job.injector.read(iterator, self._treeParser)
        iterator = self._write_xml(iterator, path, '_resolved')

        iterator = markdown_tree.lift_singles(iterator)
        iterator = self._write_xml(iterator, path, '_single')
        iterator = markdown_tree.lift_trees(iterator, self._job.markers)
        iterator = self._write_xml(iterator, path, '_trees')
        iterator = markdown_tree.set_newlines(iterator)
        iterator = markdown_tree.resolve_splitters(iterator)
        iterator = markdown_tree.join_texts(iterator)
        iterator = markdown_tree.strip_leading_newlines(iterator)
        iterator = self._write_xml(iterator, path, '_manipulated')

        iterator = self._outputTree.markdown_outputs(iterator)
        iterator = self._outputTree.indent_outputs(iterator)
        iterator = self._outputTree.write_lines(iterator, writer)
        iterator = self._write_xml(iterator, path, '_output')
        for element in iterator:
            pass

    def _report_tags(self, iterator, report=None):
        for element in iterator:
            if report is not None:
                if element.tag in report:
                    report[element.tag] += 1
                else:
                    report[element.tag] = 1
            yield element

    def comments_to_extract(
        self, iterator, report, docPath, writer, tagExtract='extract'
    ):
        firstDoc = True
        for element in iterator:
            extract = element.find(tagExtract)
            if extract is not None:
                fragment = self._job.add_fragment(
                    report.extractPath
                    , int(element.get('lineFirst'))
                    , int(element.get('lineLast'))
                    , extract.text)
                if not self._job.dryRun:
                    CommentTree.write_replacement(
                        element, writer, docPath if firstDoc else "", fragment)
                firstDoc = False
            else:
                writer.writelines(element.text)

    def _write_xml(self, iterator, basePath, stemSuffix):
        root = ET.Element('file', {'path': str(basePath)})
        root.extend(tuple(iterator))
        document = ET.ElementTree(root)
        xmlPath = basePath.with_suffix('.xml')
        path = xmlPath.with_name(''.join((
            xmlPath.stem, stemSuffix, xmlPath.suffix)))
        # print(f'Writing "{str(path)}".')
        with path.open('w') as file:
            document.write(file, encoding="unicode")
        return root
    
    def _delete_stage(self, iterator, tag):
        for parent in iterator:
            foundIndex = None
            for index, child in enumerate(parent):
                if child.tag == tag:
                    foundIndex = index
                    break
            if foundIndex is not None:
                del parent[foundIndex]
            yield parent
