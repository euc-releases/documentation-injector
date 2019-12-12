Documentation Injector Test Suite
=================================
This page has some notes on the test suite for the Documentation Injector tool
aka the Doctor. For an introduction to the tool see the [parent directory](/../)
readme file.

The test suite uses the Python Unit Test framework. See:
[https://docs.python.org/3/library/unittest.html](https://docs.python.org/3/library/unittest.html)

The tests can be run like this:
    
    cd /path/where/you/cloned/doctor
    cd test
    MISTUNE=/your/mistune/directory python3 -m unittest

The expected output if all tests pass is like this:

    $ python3 -m unittest
    .........
    ----------------------------------------------------------------------
    Ran 10 tests in 0.044s
    
    OK

Tips
====
You can run an individual test like this:

    cd /path/where/you/cloned/doctor
    cd test
    MISTUNE=/your/mistune/directory python3 -m unittest test_doctor.TestDoctor.test_extract_mode

Test Data
=========
The test suite includes a set of data that may be useful during development of
the Doctor. The data can be copied and used as input, for example as follows.

    $ cd /path/where/you/cloned/doctor
    $ python3 test/set_up.py
    $ ls -l data
    total 48
    -rw-r--r--  1 yourname  staff   623  1 May  2019 cache.md
    -rw-r--r--  1 yourname  staff   817  1 May  2019 docco.md
    -rw-r--r--  1 yourname  staff  3627  9 Dec 14:54 extractablesource.h
    -rw-r--r--  1 yourname  staff  3791  2 Dec 17:31 source.h
    -rw-r--r--  1 yourname  staff  4869  1 May  2019 swiftsource.swift

    $ python3 -m doctor -o -l data/cache.md -i data/ -w 80

Run the test/set_up.py script with the -h command line switch for usage.

Legal
=====
Copyright 2019 VMware, Inc.  
SPDX-License-Identifier: BSD-2-Clause
