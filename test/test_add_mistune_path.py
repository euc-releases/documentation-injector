# Run with Python 3
# Copyright 2019 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Unit tests.

Run just these tests like:

    python3 test/test_add_mistune_path.py
"""
#
# Standard library imports, in alphabetic order.
#
# Stream tools module
# https://docs.python.org/3/library/io.html#io.StringIO
from io import StringIO
#
# File path module.
# https://docs.python.org/3/library/os.path.html
import os.path
#
# Module for manipulation of the import path.
# https://docs.python.org/3/library/sys.html#sys.path
import sys
#
# Unit test framework.
# https://docs.python.org/3/library/unittest.html
import unittest
#
# Local imports

# This module includes tests of the interface that is called by the set_up.py
# file, so it mustn't import them. Instead, it has to do some of the things that
# set_up does.
#
# Add the location of the Doctor to sys.path so that its `main` module can be
# imported.
toolPath = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir))
sys.path.append(toolPath)
from doctor import main

class TestMistunePath(unittest.TestCase):
    def capture_add_mistune_path(self, path, addFile=False):
        captureStream = StringIO()

        sys.stderr = captureStream
        main.add_mistune_path(path)
        sys.stderr = sys.__stderr__

        captured = captureStream.getvalue()
        captureStream.close()
        
        expectedPath = path if os.path.isabs(path) else os.path.abspath(path)
        if addFile:
            expectedPath = os.path.join(expectedPath, "mistune.py")
        expected = '"{}"'.format(expectedPath)
        message = str({"expected": expected, "captured": captured})
        self.assertTrue(expected in captured, message)
        self.assertTrue(captured.startswith("Warning:"), captured)
        self.assertTrue(captured.endswith("\n"), captured)
        return captured
       
    def test_add_mistune_path(self):
        captured = self.capture_add_mistune_path('/duff/absolute/path')
        self.assertTrue("isn't a directory" in captured, captured)
        
        captured = self.capture_add_mistune_path('duff/relative/path')
        self.assertTrue("isn't a directory" in captured, captured)
        
        captured = self.capture_add_mistune_path(os.path.curdir, True)
        self.assertTrue("doesn't include expected file" in captured, captured)

if __name__ == '__main__':
    unittest.main()
