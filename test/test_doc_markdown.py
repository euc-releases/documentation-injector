# Run# Run with Python 3
# Copyright 2019 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Unit tests for doc_markdown module in the Doctor tool.

Run just these tests like:

    python3 test/test_doc_markdown.py

There are only a couple of tests here and they are very basic.
"""
#
# Standard library imports, in alphabetic order.
#
# Unit test framework.
# https://docs.python.org/3/library/unittest.html
import unittest
#
# Local imports
#
# Handy common code to put the Doctor module on the import path.
import set_up
#
# Classes under test.
from doctor.doc_markdown import DocResolver
from doctor.markdown import BlockType, MarkdownItem

class TestDocMarkdown(unittest.TestCase):
    def test_doc_resolver(self):
        docResolver = DocResolver()
        #
        # Test that paragraph cannot contain paragraph.
        self.assertFalse(docResolver.can_contain(
            BlockType.PARAGRAPH, MarkdownItem(BlockType.PARAGRAPH, None, [])))
        #
        # Test that list item can contain paragraph.
        self.assertTrue(docResolver.can_contain(
            BlockType.LIST_ITEM, MarkdownItem(BlockType.PARAGRAPH, None, [])))

if __name__ == '__main__':
    unittest.main()
