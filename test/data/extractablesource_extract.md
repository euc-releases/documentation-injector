Automatic extraction by the Doctor.
Extract time (ISO 8601): 2019-12-09T14:55:50+0000
{
  "path": "data/extractablesource.h",
  "extension": ".h",
  "overwrote": true,
  "extract": true,
  "lineTypes": {},
  "extractPath": "data/extractablesource.md"
}

# line-7-9
@file extractablesource.h
These are pretend file-level comments.

# line-11-12
Sample

# line-15-16
Funny end.
with text first.
# line-17-18
Sample List

# line-20-23
Sample
With added note.
@param supposed_parameter Supposed parameter.

# line-26-32
This is inset like if it was for a method or something.

The Markdown could be tidier, or extracted to a docco source file, because it passes the 80 column limit.

## Header for a special paragraph [product-name]
This is the special para.

# line-34-41
No space after the docco comment start.

This has no inline doc uri.
This piece isn't from the explicit cache it has no
path.

Next one isn't only an inline doc uri.

# line-43-43
infix Two
# line-45-45
One-liner; next one is empty. 
# line-47-48


# line-50-56
Put the injected MD into a list.

-   Sample not injected
-   This isn't sample.

    But this is the end of it.

# line-59-83
Starred list with leaders.

Here's the list:

*   Item one.
*   Item *number* two.
    *   Item two *point* one. It has a bunch of extra text to
        make it exceed the line and get wrapped.
    *   Item two *point* two.

Here's another, *with* hyphens:

-   Hyphenitem one.
-   Hyphenitem two, wait for it.

    Second para.

There aren't any more lists but this is the first paragraph of two and it
extends onto a second line. And a second sentence.

Long line. The next line starts with a span to test the case that a newline is at the end of a text string.
*emphatic line start*.

This is the second paragraph and really is the last.

# line-85-106
Leaderless.

No leaders in the comment. Next line is just spaces.

*   Starred list, item one. Next line is empty.

*   Item two.

That's not all; numbered list coming.

1.  Item number one.
    - With nest.
1.  Item number two.
1.  Item number three.

-   Nested numbers.
    2. Point one.
    2. Point two.
    
    End of nest.
-   Postnest.

# line-108-117
Leaderless backdent.

No leaders in the comment. Next line is just spaces.

*   Starred list, item one. Next line is empty.

*   Item two.

That's all.

# line-119-128
Leaderful backdent.

No leaders in the comment.

*   Starred list, item one.

*   Item two.

That's all.

# line-130-132

Nothing on first line.

# line-135-135

# line-140-140
empty line 
# line-142-142
One-liner with code. 
# line-144-145
* star in start

# line-154-157
Variable indent, naughty.
OK indent
 bad indent

# line-159-162
Variable indent, naughty.
  OK indent
 bad indent

# line-164-168
Blank line in leaderful block, tut tut.
*

* summat.

# line-170-171
Tricky
last line
