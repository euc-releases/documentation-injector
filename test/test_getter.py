# Run with Python 3
# Copyright 2019 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Unit tests for getter module in the Doctor tool.

Run just these tests like:

    python3 test/test_getter.py

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
from doctor.getter import DocGetter

class TestDocMarkdown(unittest.TestCase):
    def test_get_empties(self):
        docGetter = DocGetter()
        
        empty = docGetter.get_content(
            "doc://./docco.md#empty", set_up.data_path('source.h'))
        self.assertEqual(len(empty), 0)
        
        emptyline = docGetter.get_content(
            "doc://./docco.md#emptyline", set_up.data_path('source.h'))
        self.assertEqual(len(emptyline), 1)
        self.assertEqual(emptyline[0], "")
        
if __name__ == '__main__':
    unittest.main()
