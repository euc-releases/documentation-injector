# Run with Python 3
# Copyright 2024 Omnissa, LLC.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Common utility code for unit tests. Can set up the import path, and make
temporary copies of the test suite data. Can also be run from the command line;
run with -h switch for usage.
"""
#
# Standard library imports, in alphabetic order.
# 
# Module for command line switches.
# Tutorial: https://docs.python.org/3/howto/argparse.html
# Reference: https://docs.python.org/3/library/argparse.html
import argparse
#
# Module for facilitation of context manager creation.
# https://docs.python.org/3.5/library/contextlib.html
from contextlib import contextmanager
#
# File path module.
# https://docs.python.org/3/library/os.path.html
import os.path
#
# Module for OO path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path
#
# Module for recursive copy.
# https://docs.python.org/3/library/shutil.html
import shutil
#
# Module for manipulation of the import path.
# https://docs.python.org/3/library/sys.html#sys.path
import sys
#
# Temporary file module.
# https://docs.python.org/3/library/tempfile.html
import tempfile
#
# Module for text dedentation.
# Only used for --help description.
# https://docs.python.org/3/library/textwrap.html
import textwrap
#
# Local imports
#
# Add the location of the Doctor to sys.path so that its `main` module can be
# imported.
toolPath = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir))
sys.path.append(toolPath)
from doctor import main
#
# Now add the path for Mistune, so that it can be imported by any test that
# requires it.
main.add_mistune_path()

dataPath = os.path.abspath(os.path.join(toolPath, 'test', 'data'))

def data_path(*basename):
    '''Get a path within the test data directory.'''
    return os.path.join(dataPath, *basename)

def copy_data(temporaryRoot, addBase=True, ignoring=None):
    '''Copy the test data to a temporary directory.'''
    if ignoring is None:
        ignoring = tuple()
    ignorePatterns = shutil.ignore_patterns(
        '*_output.*', '*_extract.*', *ignoring)
    return shutil.copytree(
        dataPath,
        os.path.join(temporaryRoot, os.path.basename(dataPath)) if addBase
        else temporaryRoot,
        ignore=ignorePatterns)

def _print_paths(label, paths):
    indent = " " * 2
    if isinstance(paths, str):
        print("{}:\n{}{}".format(label, indent, paths))
        return
    print('{}[{}]:'.format(label, len(paths)))
    for path in paths:
        print("{}{}".format(indent, path))

def copy_files(source, destination, suffix):
    Path(destination).mkdir(exist_ok=True)
    names = []
    for path in Path(source).iterdir():
        # print(path, path.suffix, suffix)
        if path.suffix == suffix:
            destinationPath = Path(destination, path.name)
            shutil.copyfile(str(path), str(destinationPath))
            names.append(str(destinationPath))
    return names

@contextmanager
def temporary_data_directory(**kwargs):
    '''\
Creates a temporary directory, changes the working directory to it, and creates
a copy of the test data there, all as a context manager. Accepts keyword
arguments for the copy_data() subroutine.
'''
    cwd = os.getcwd()
    temporaryDirectory = tempfile.TemporaryDirectory()
    os.chdir(temporaryDirectory.name)
    yield copy_data(os.getcwd(), **kwargs)
    # Note that the previous line calls os.getcwd() again. It doesn't assume
    # that getcwd() returns the same value that was just passed to chdir(), even
    # though it's an absolute path. This seems to be required for macOS, which
    # adds a prefix like "/private/" maybe because this will be running in a
    # temporary directory.
    os.chdir(cwd)
    temporaryDirectory.cleanup()

@contextmanager
def temporary_working_directory():
    '''\
Creates a temporary directory, and changes the working directory to it, as a
context manager.
'''
    cwd = os.getcwd()
    temporaryDirectory = tempfile.TemporaryDirectory()
    os.chdir(temporaryDirectory.name)
    yield os.getcwd()
    # See the note in the temporary_data_directory() subroutine, above, for a
    # discussion of the second call to getcwd().
    os.chdir(cwd)
    temporaryDirectory.cleanup()

def main(argv):
    argumentParser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__doc__), epilog=r"""
Default is to delete the local `data/` directory, and then make a copy of the
unit test data there, i.e.:

    python3 test/set_up.py \
        --copy-data /path/where/you/cloned/documentation-injector/data/
    
""")
    argumentParser.add_argument(
        '-p', '--print-paths', dest='print_paths', action='store_true', help=
        'Print various paths.')
    argumentParser.add_argument(
        '-d', '--copy-data', dest='copy_data', metavar='destination', type=str
        , help="Copy the unit test data to a new directory.")
    arguments = argumentParser.parse_args(argv[1:])

    didSomething = False
    if arguments.print_paths:
        didSomething = True
        _print_paths('toolPath', toolPath)
        _print_paths('dataPath', dataPath)
        _print_paths('sys.path', sys.path)
    
    destination = (
        None if didSomething
        else os.path.join(toolPath, 'data') if arguments.copy_data is None
        else arguments.copy_data)
    
    if destination is not None:
        if os.path.exists(destination):
            shutil.rmtree(destination)
        copy_data(destination, False)
    
    # Shell return code convention
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
