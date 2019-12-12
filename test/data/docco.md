Copyright 2019 VMware, Inc.  
SPDX-License-Identifier: BSD-2-Clause

Text before the first heading is ignored by the Doctor.

# Sample
This is some sample.

This is the end of it.
# 
Text after an empty heading is also free

# infix
 fixed *emphatic* in 
#
The above item has a space at the start and another at the end.
Make sure your text editor doesn't remove the space at the end of the line.

# infixTwo
 fixed *emphatic* in again 
#

# product-name
turbo-encabulator
#

Next couple of fragments test some edge cases.

-   `empty` will come out of DocGetter.get_content() as an empty list: []
-   `emptyline` will come out as a list with an empty string in it: [""]

# empty
# emptyline

#

# Sample-List
-   Just a list.

    Nothing to see.
-   Middle of the list.
-   End of the list.

doc://./docco.md#Sample