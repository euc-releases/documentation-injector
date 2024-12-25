# Run with Python 3
# Copyright 2024 Omnissa, LLC.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Unit tests for comment_line module in the Doctor tool.

Run just these tests like:

    python3 test/test_comment_line.py
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
from doctor.comment_line import CommentLine, dump_match, CommentLineType

class TestCommentLine(unittest.TestCase):
    def test_textEOL_setter(self):
        commentLine = CommentLine()

        commentLine.textEOL = "\n"
        self.assertEqual(commentLine.text, "")
        self.assertEqual(commentLine.eol, "\n")

        commentLine.textEOL = "\r\n"
        self.assertEqual(commentLine.text, "")
        self.assertEqual(commentLine.eol, "\r\n")

        commentLine.textEOL = "noeol"
        self.assertEqual(commentLine.text, "noeol")
        self.assertEqual(commentLine.eol, "")

        commentLine.textEOL = "blib\n"
        self.assertEqual(commentLine.text, "blib")
        self.assertEqual(commentLine.eol, "\n")

        commentLine.textEOL = ""
        self.assertEqual(commentLine.text, "")
        self.assertEqual(commentLine.eol, "")

        commentLine.textEOL = None
        self.assertIsNone(commentLine.text)
        self.assertIsNone(commentLine.eol)

    def test_lineType_setter(self):
        # No idea why but at some point it seemed necessary to test this
        # fundamental. Maybe there was uncertainty that `is` could be used on a
        # property and an enumerated constant.
        
        commentLine = CommentLine()
        commentLine.lineType = CommentLineType.FINISH
        self.assertIs(commentLine.lineType, CommentLineType.FINISH)

if __name__ == '__main__':
    unittest.main()
