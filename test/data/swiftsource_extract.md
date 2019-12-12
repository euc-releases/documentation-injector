Automatic extraction by the Doctor.
Extract time (ISO 8601): 2019-05-08T15:45:15+0100
{
  "path": "data/swiftsource.swift",
  "extension": ".swift",
  "overwrote": true,
  "extract": true,
  "lineTypes": {},
  "extractPath": "data/swiftsource.md"
}

# line-9-19

Blankly tryin' out some documentationification.
Same "html" line.

*   Startled list.
*   Second star of two.

Now some code:

this.aint.code();

# line-22-36

Blibbity subroutine.

Some initial discussion is here.
@param inty The number of yourselves.
continuation and on.


No more params but some bonus code.

    Block o' code
    Here()

@return string of them

# line-42-48

Blobby subroutine. Next line starts with a span to test the case that a
newline is at the end of a text string, i.e. a marked up span is the first
thing on a line.
*blobs* I say **blobs**.
@returns blobs of them.

# line-54-62

Hambalic function.

- Parameter stringy:
- Returns:34 always

Swift preferred documentation comment convention, except empty parameter
documentation.

# line-67-76

Test that at return is changed to Swift documentation.

@param test001p1 Paragraph about parameter one.
@param test001p2 Paragraph about the other parameter that emphatically
*isn't* a string
type on funny newline.
@return Paragraph about the return value, which goes on for a bit and has a
Markdown span in *italics*. The first line is exactly 80 characters.

# line-81-83

doc://#swiftsource-test_002

# line-88-95

Test that at return is changed to Swift documentation in a single block.
@param test003p1 Paragraph about parameter one.
@param test003p2 Paragraph about the other parameter that isn't
with funny newline.
@returns Paragraph about the return value, which goes on for a bit but doesn't
have any spans within it.

# line-100-108

Test that at param and at return are changed to Swift documentation after a
span at the end of a line.
@param test004p1 Paragraph about parameter *one.*
@parameter test004p2 Paragraph about the "over-declared" parameter that isn't
**with funny newline.**
@returns Paragraph about the `Int` return value, which goes on for a bit
but doesn't have any spans within it.

# line-114-123

Test that at return is changed to Swift documentation in paragraphs already.

@param test005p1 Paragraph about parameter one.

@param test005p2 Paragraph about the other parameter that isn't
with funny newline.
@returns Paragraph about the return value, which goes on for a bit but doesn't
have any spans within it.

# line-128-144

@brief Brief description using `brief` at-command, old-timey Java and Obj-C style.
@description Longer description, and how, using the antedeluvial at-command
   `description` which appears to be a synonym for `details`. That's tested
   in another place. The description text is indented by three spaces, because
   there was some documentation commentary written like that in some test input
   in the early stages of development. The spaces get collapsed.
   There are also some artificially long words, that could be like verbose
   class or method names application(_:shouldAllowExtensionPointIdentifier:)
   and then this too disableThirdPartyKeyboard() which isn't as long.
   Check UIApplicationExtensionPointIdentifier.keyboard and return false, else
   call the original function.

This line introduces a code snippet, and isn't indented like the description paragraph was

    SDKCustomKeyboardController.shared.disallowKeyboardRestrictionsEnforcement = true

# line-149-153

@brief       Neat but unconventional indentation of the brief description and ...
@details     ... the long description, although it is marked up by the `details` at-command.
@version     2.2

