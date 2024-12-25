# Run with Python 3
# Copyright 2024 Omnissa, LLC.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Unit tests for the parser module in the Doctor tool.

Run just these tests like:

    python3 test/test_parser.py
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
from doctor.parser import SlashStarsParser
from doctor.comment_line import match_groups, match_spans

class TestParser(unittest.TestCase):
    def test_continuation_RE(self):
        parser = SlashStarsParser()

        # Test empty string.
        match = parser.commentContinue.search("")
        self.assertEqual(match_spans(match), ("", "", ""))
        self.assertDictEqual(match_groups(match), {'indent': '', 'EOL': ''})

        # Test comment without symbol nor indent.
        input = 'flush comment\n'
        match = parser.commentContinue.search(input)
        self.assertEqual(match_spans(match), ("", "", input))
        self.assertDictEqual(match_groups(match), {
            'indent': '', 'nonSymbol': ''
        })
        
        # Test indent and comment without symbol.
        match = parser.commentContinue.search("  code\n")
        self.assertEqual(match_spans(match), ("", "  ", "code\n"))
        self.assertDictEqual(match_groups(match), {
            'indent': '  ', 'nonSymbol': ''
        })

        # Test space before newline is parsed as a margin.
        match = parser.commentContinue.search("  * \n")
        self.assertEqual(match_spans(match), ("", "  * ", "\n"))
        self.assertDictEqual(match_groups(match), {
            'indent': '  ', 'symbolMargin': '*', 'margin': ' '
        })
        
        # Test symbol, then immediate newline.
        match = parser.commentContinue.search("  *\n")
        self.assertEqual(match_spans(match), ("", "  *", "\n"))
        self.assertDictEqual(match_groups(match), {
            'indent': '  ', 'symbolEOL': '*',
        })
        
        # Test end comment isn't matched.
        match = parser.commentContinue.search("  */\n")
        self.assertIsNone(match)

        # Test symbol, then immediate comment text.
        match = parser.commentContinue.search("  *g\n")
        self.assertEqual(match_spans(match), ("", "  *", "g\n"))
        self.assertDictEqual(match_groups(match), {
            'indent': '  ', 'symbolNonSlash': '*',
        })
        
        # Test symbol, then space, then comment text is parsed as a margin.
        match = parser.commentContinue.search("  * b\n")
        self.assertEqual(match_spans(match), ("", "  * ", "b\n"))
        self.assertDictEqual(match_groups(match), {
            'indent': '  ', 'symbolMargin': '*', 'margin': ' '
        })
        
        # Test indent on its own.
        match = parser.commentContinue.search("      ")
        self.assertEqual(match_spans(match), ("", "      ", ""))
        self.assertDictEqual(match_groups(match), {
            'indent': "      ", 'EOL': ""
        })
        
    def test_finishing_RE(self):
        parser = SlashStarsParser()

        # Test bare end comment.
        match = parser.commentFinish.search("*/")
        self.assertEqual(match_spans(match), ("", "*/", ""))
        self.assertDictEqual(match_groups(match), {
            'indent': "", 'symbol': "*/"
        })

        match = parser.commentFinish.search("end space */")
        self.assertEqual(match_spans(match), ("end space ", "*/", ""))
        self.assertDictEqual(match_groups(match), {'symbol': "*/"})

        match = parser.commentFinish.search("not end")
        self.assertIsNone(match)

        match = parser.commentFinish.search("      */")
        self.assertEqual(match_spans(match), ("", "      */", ""))
        self.assertDictEqual(match_groups(match), {
            'indent': "      ", 'symbol': "*/"
        })

if __name__ == '__main__':
    unittest.main()
