# Run with Python 3
# Copyright 2024 Omnissa, LLC.
# SPDX-License-Identifier: BSD-2-Clause
"""\
DOCumentation injecTOR tool.

Run with Python 3 as follows.

-   python3 -m doctor -o -i path/to/a/directory -i path/to/another/directory

    Overwrites all .h files anywhere under the specified directories.

-   python3 -m doctor -h
    
    Prints usage.
"""

# This file makes Doctor a runnable module, see:
# https://docs.python.org/3/using/cmdline.html#cmdoption-m

from sys import stderr, exit

# Local module with command line switches and such.
try:
    from doctor import main
except:
    stderr.writelines((__doc__,
                       "\nCan only be run as a module, with the Python -m"
                       " command line switch.\n\n"))
    exit(1)

exit(main.default_main())
