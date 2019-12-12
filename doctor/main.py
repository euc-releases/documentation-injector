# Run with Python 3
# Copyright 2019 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
"""\
DOCumentation injecTOR tool.

Run with Python 3 as follows.

-   python3 -m doctor -o -i path/to/a/directory -i path/to/another/directory

    Overwrites all .h files anywhere under the specified directories.

-   python3 -m doctor -h
    
    Prints usage.

Set the MISTUNE environment variable to a path to add to the import paths to
enable `import mistune`, or use the `-m PATH` command line switch, or
use `-m ""` and set PYTHONPATH.
"""
#
# Standard library imports, in alphabetic order.
# 
# Module for command line switches.
# Tutorial: https://docs.python.org/3/howto/argparse.html
# Reference: https://docs.python.org/3/library/argparse.html
import argparse
#
# JSON module.
# https://docs.python.org/3/library/json.html
import json
#
# Module for environment variables and working with paths.
# https://docs.python.org/3/library/os.html#os.environ
# https://docs.python.org/3/library/os.path.html
import os
#
# Module for manipulation of the import path and other system access.
# https://docs.python.org/3/library/sys.html
import sys
#
# Module for text dedentation.
# Only used for --help description.
# https://docs.python.org/3/library/textwrap.html
import textwrap

# Local imports would go here, in alphabetic order.
# The `doctor` module can't be imported unless mistune can also be imported.
# That requires its repository's path to be added to the sys.path list, which in
# turn can only happen after it has been specified. So, there is an import
# statement after the argument parser.

def add_mistune_path(path=None):
    """\
Add a directory for the mistune Markdown parser to sys.path, the search path for
Python module import, depending on the parameter value:

-   If path is None, adds one of the following to sys.path:
    -   The value of the MISTUNE environment variable, if set.
    -   dirname(__file__)/../../mistune otherwise.
    
    Then returns the path that was added.
    
-   If path is the empty string, does nothing and returns the empty string. This
    supports use of the $PYTHONPATH environment variable.

-   Otherwise, adds the specified path, and returns it.
    """
    # The error messages of this subroutine are tested by the unittest suite.
    
    if path == "":
        return path
    # This supports use of the PYTHONPATH environment variable.
    # https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH

    if path is None:
        try:
            path = os.environ['MISTUNE']
        except KeyError:
            path = None
        
    if path is None:
        path =  os.path.join(
            os.path.dirname(__file__), *([os.path.pardir] * 2), 'mistune')

    path =  os.path.abspath(path)
    if os.path.isdir(path):
        filePath = os.path.join(path, 'mistune.py')
        if not os.path.isfile(filePath):
            sys.stderr.write(
                "Warning: Directory for mistune import doesn't include"
                ' expected file "{}".\n'.format(filePath))
    else:
        sys.stderr.write("Warning: Path for mistune import isn't a directory"
                         ' "{}".\n'.format(path))
    
    sys.path.append(path)
    return path

def main(prog, commandLine):
    argumentParser = argparse.ArgumentParser(
        prog=prog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__doc__))
    # Not really happy that `help` messages have to start with a small letter,
    # and don't end with full stops. However, that's the default for the --help
    # so it has to be that way for consistency.
    argumentParser.add_argument(
        '--ad-hoc', action='store_true', dest='adHoc', help=
        'run old ad-hoc code, for compatibility;'
        ' default is to run latest tree-based code')
    argumentParser.add_argument(
        '-m', '--mistune', type=str, help=
        'directory to add to the import paths to enable `import mistune`,'
        ' or pass "" to add nothing and rely on PYTHONPATH;'
        " default is to read the MISTUNE environment variable or, if that"
        " isn't set, go up two levels from the directory of this file,"
        ' and then down into mistune/')
    argumentParser.add_argument(
        '-e', '--extract', action='store_true', help=
        'extract documentation comments from source files and write them to'
        ' .md files')
    argumentParser.add_argument(
        '-x', '--extract_dir', type=str, help=
        "root directory for new .md files created by '--extract'; default is"
        " to put .md files alongside source files")
    argumentParser.add_argument(
        '-k', '--markers', action='store_true', help=
        'leave <doc> markers where text was injected')
    argumentParser.add_argument(
        '-o', '--overwrite', action='store_true', help=
        'overwrite the input files in place; default is a dry run')
    argumentParser.add_argument(
        '-w', '--width', type=int, help=
        "maximum column width, for wrapping, or zero to switch off wrapping;"
        " default is don't wrap")
    argumentParser.add_argument(
        '-d', '--diffs', action='store_true', help=
        'log context diffs to stdout')
    argumentParser.add_argument(
        '-j', '--json', action='store_true', help=
        'log per-source file reports in JSON format to stdout')
    argumentParser.add_argument(
        '-l', '--load', type=str, nargs='*', help=
        'documentation source files or directories to be pre-loaded into the'
        ' getter cache')
    argumentParser.add_argument(
        '-i', '--input', dest='inputs', type=str, nargs='+', help=
        'input files or directories')

    arguments = argumentParser.parse_args(commandLine)
    
    add_mistune_path(arguments.mistune)
    
    from doctor import doctor_class

    doctorJob = doctor_class.Doctor()
    doctorJob.adHoc = arguments.adHoc
    doctorJob.maxWidth = (
        None if arguments.width is None or arguments.width <= 0
        else arguments.width)
    doctorJob.dryRun = not arguments.overwrite
    if arguments.load is not None:
        doctorJob.load_cache(*arguments.load)
    
    doctorJob.extractDir = arguments.extract_dir
    doctorJob.extractMode = arguments.extract
    doctorJob.markers = arguments.markers
    
    if arguments.inputs is None:
        argumentParser.error("At least one input must be specified.")
    
    for report in doctorJob.overwrite_all(arguments.inputs):
        diffs = report['diffs']
        del report['diffs']
        if arguments.json:
            json.dump(report, sys.stdout)
            sys.stdout.write("\n")
        if arguments.diffs and diffs is not None:
            sys.stdout.writelines(diffs)
    json.dump(doctorJob.report, sys.stdout, indent=4)
    sys.stdout.write("\n")
    
    # Shell convention: return zero for OK.
    return 0

def default_main():
    """\
    Command line entry point. Suppresses the stack trace, in case of an
    exception.
    """
    # This is here, instead of in the __main__.py file, because that file won't
    # have the __package__ variable, in case it was run without the Python -m
    # switch.
    try:
        return main(__package__, sys.argv[1:])
    except ValueError as error:
        sys.stderr.writelines((str(error), "\n"))
        # The MarkdownParser read method makes use of Python raise ... from.
        # See: https://docs.python.org/3/library/exceptions.html
        #
        # Jim doesn't have a complete understanding of how that should be
        # represented so the code here looks for a couple of things and prints
        # them and it seems to work.
        if hasattr(error, '__cause__'):
            sys.stderr.writelines((str(error.__cause__), "\n"))
        elif hasattr(error, '__context__'):
            sys.stderr.writelines((str(error.__context__), "\n"))
        return 2
    except OSError as error:
        # Documentation is here:
        # https://docs.python.org/3/library/exceptions.html#OSError
        sys.stderr.writelines((str(error), "\n"))
        return (error.errno
                if hasattr(error, "errno")
                and error.errno != 0
                and error.errno is not None
                else 1)

if __name__ == '__main__':
    default_main()
