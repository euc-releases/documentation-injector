/* Copyright 2019 VMware, Inc.
 * SPDX-License-Identifier: BSD-2-Clause
 *
 * The copyright notice, above, should be ignored by the Doctor.
 */

import Foundation

/**
 Blankly tryin' out some documentationification. Same "html" line.
 
 -   Startled list.
 -   Second star of two.
 
 Now some code:
 
 this.aint.code();
 */
public class DocumentationTryClass {
    
    /**
     Blibbity subroutine.
     
     Some initial discussion is here.
     
     - Parameter inty: The number of yourselves. continuation and on.
     
     No more params but some bonus code.
     
         Block o' code
         Here()
         
     - Returns: string of them
     */
    public func blib(_ inty: Int) -> String {
        
        return ""
    }
    
    /**
     Blobby subroutine. Next line starts with a span to test the case that a
     newline is at the end of a text string, i.e. a marked up span is the first
     thing on a line. *blobs* I say **blobs**.
     
     - Returns: blobs of them.
     */
    public func blobby(_ inty: Int) -> String {
        
        return ""
    }

    /**
     Hambalic function.
     
     -   Parameter stringy:
     -   Returns:34 always
     
     Swift preferred documentation comment convention, except empty parameter
     documentation.
     */
    public func hambalic(_ stringy: String) -> Int {
        return 34
    }

    /**
     Test that at return is changed to Swift documentation.
     
     - Parameter test001p1: Paragraph about parameter one.
     
     - Parameter test001p2: Paragraph about the other parameter that
                            emphatically *isn't* a string type on funny
                            newline.
     
     - Returns: Paragraph about the return value, which goes on for a bit and
                has a Markdown span in *italics*. The first line is exactly 80
                characters.
     */
    public func test_001(_ test001p1: String, _ test001p2: Int) -> Int {
        return 1
    }
    
    /**
     Test that at return is changed to Swift documentation.
     
     - Parameter test002p1: Paragraph about parameter one.
     
     - Parameter test002p2: Paragraph about the other parameter that
                            emphatically *isn't* a string type on funny
                            newline.
     
     - Returns: Paragraph about the return value, which goes on for a bit and
                has a Markdown span in *italics*. The first line isn't exactly
                80 characters.
     */
    public func test_002(_ test002p1: String, _ test002p2: Int) -> Int {
        return 2
    }
    
    /**
     Test that at return is changed to Swift documentation in a single block.
     
     - Parameter test003p1: Paragraph about parameter one.
     
     - Parameter test003p2: Paragraph about the other parameter that isn't with
                            funny newline.
     
     - Returns: Paragraph about the return value, which goes on for a bit but
                doesn't have any spans within it.
     */
    public func test_003(_ test003p1: String, _ test003p2: Int) -> Int {
        return 3
    }
    
    /**
     Test that at param and at return are changed to Swift documentation after
     a span at the end of a line.
     
     - Parameter test004p1: Paragraph about parameter *one.*
     
     - Parameter test004p2: Paragraph about the "over-declared" parameter that
                            isn't **with funny newline.**
     
     - Returns: Paragraph about the `Int` return value, which goes on for a bit
                but doesn't have any spans within it.
     */
    public func test_004(_ test004p1: String, _ test004p2: Int) -> Int {
        return 4
    }
    
    
    /**
     Test that at return is changed to Swift documentation in paragraphs
     already.
     
     - Parameter test005p1: Paragraph about parameter one.
     
     - Parameter test005p2: Paragraph about the other parameter that isn't with
                            funny newline.
     
     - Returns: Paragraph about the return value, which goes on for a bit but
                doesn't have any spans within it.
     */
    public func test_005(_ test005p1: String, _ test005p2: Int) -> Int {
        return 5
    }
    
    /**
     Brief description using `brief` at-command, old-timey Java and Obj-C
     style.
     
     Longer description, and how, using the antedeluvial at-command
     `description` which appears to be a synonym for `details`. That's tested
     in another place. The description text is indented by three spaces,
     because there was some documentation commentary written like that in some
     test input in the early stages of development. The spaces get collapsed.
     There are also some artificially long words, that could be like verbose
     class or method names application(_:shouldAllowExtensionPointIdentifier:)
     and then this too disableThirdPartyKeyboard() which isn't as long. Check
     UIApplicationExtensionPointIdentifier.keyboard and return false, else call
     the original function.
     
     This line introduces a code snippet, and isn't indented like the
     description paragraph was
     
         SDKCustomKeyboardController.shared.disallowKeyboardRestrictionsEnforcement = true
     */
    public func test_006() {
        return 6
    }

    /**
     Neat but unconventional indentation of the brief description and ...
     
     ... the long description, although it is marked up by the `details` at-
     command.
     
     - Version: 2.2
     */
    public func test_007() {
        return 7
    }

}
