# Run with Python 3
# Copyright 2024 Omnissa, LLC.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Markdown tree manipulation subroutines. Part of the Doctor documentation tool.
No standalone capability.
"""
# Exit if run other than as a module.
if __name__ == '__main__':
    print(__doc__)
    raise SystemExit(1)

# Standard library imports, in alphabetic order.
#
# Module for XML handling.
# https://docs.python.org/3.5/library/xml.etree.elementtree.html#module-xml.etree.ElementTree
import xml.etree.ElementTree as ET

# ElementTree utility functions.
#
def ET_string(element):
    return ET.tostring(element, encoding="unicode")
def ET_copy_attr(source, destination, names=None):
    if names is None:
        names = source.keys()
    elif isinstance(names, str):
        names = [names]
    for name in names:
        value = source.get(name)
        if value is not None:
            destination.set(name, value)
    return names

# ET_index does the same as this:
#
#     return parent.index(child)
#
# ET_index uses `is` comparison, which Element.index() might not.
def ET_index(parent, child, returnNone=False):
    for index, check in enumerate(parent):
        if check is child:
            return index
    if returnNone:
        return None
    raise ValueError(
        "Child wasn't found by index."
        f'\nparent:{ET_string(parent)}\nchild:{ET_string(child)}'
    )

def ET_grandparent(element, xpath):
    grandparent = element.find(f'.//{xpath}/../..')
    if grandparent is None:
        return None, None, None
    parent = grandparent.find(f'./*/{xpath}/..')
    if parent is None:
        raise AssertionError(
            "Grandparent but no parent"
            f'\ngrandparent:{ET_string(grandparent)}'
            f'\nxpath:"{xpath}')
    child = parent.find(f'./{xpath}')
    if child is None:
        raise AssertionError(
            "Parent but no child"
            f'\nparent:{ET_string(parent)}'
            f'\nxpath:"{xpath}')
    return grandparent, parent, child

def lift_singles(
    iterator, tagRemove='paragraph', countAttribute='contentLines'
):
    # If there was exactly one line in the resolution, then destructure the
    # markdown parser's return value, i.e. remove the paragraph layer.
    for element in iterator:
        while True:
            found = element.find(f".//*[@{countAttribute}='1']")
            if found is None:
                break

            if len(found) == 0:
                # Attribute must be set to stop it being found again.
                found.set(countAttribute, 'zero')
                continue

            if len(found) != 1:
                # Maybe should be an AssertionError or ValueError.
                raise NotImplementedError(
                    'Single content line but multiple child elements'
                    f' {ET_string(found)}.')

            if found[0].tag != tagRemove:
                # Maybe should be an AssertionError or ValueError.
                raise NotImplementedError(
                    "Single content line doesn't have expected tag"
                    f' "{tagRemove}"\n{ET_string(found)}.')

            # Destructure by boosting the grandchildren.
            child = found[0]
            found.remove(child)
            found.extend(child[:])
            # Attribute must be set to stop it being found again.
            found.set(countAttribute, 'lifted')
            found[0].set('liftedSingle', str(True))

        yield element

def lift_trees(iterator, leaveMarkers):
    # insertIndex = None
    # insertParent = None
    # def insert_here(insertion):
    #     insertParent.insert(insertIndex, insertion)
    #     insertIndex += 1

    for element in iterator:
        while True:
            grandparent, parent, docElement = ET_grandparent(
                element, '*[@resolved]')
            if grandparent is None:
                break
            parentIndex = ET_index(grandparent, parent)
            docIndex = ET_index(parent, docElement)
            
            # Create doc markers.
            if leaveMarkers:
                docStart = ET.Element('doc', {'layout': 'marker'})
                ET_copy_attr(docElement, docStart, ('source', 'uri'))
                #
                # Next lines are a bit of a cheeky use of the ET interface. The
                # code generates the marker text by stringifying the element
                # itself and then changing the end from "/>" to ">".
                startText = ET_string(docStart)
                if startText.endswith(' />'):
                    docStart.text = ''.join((startText[:-3], startText[-1]))
                else:
                    raise AssertionError(
                        'Wrong ending on doc start marker.\nExpected: " />"'
                        f'\nActual: "{startText}".')
                docEnd = ET.Element('doc', {'layout': 'marker'})
                ET_copy_attr(docElement, docEnd, ('source', 'uri'))
                docEnd.text = '</doc>'
            else:
                docStart = None
                docEnd = None

            # Remove the doc_uri from its parent. It won't be released yet
            # because the docElement variable retains a reference to it.
            del parent[docIndex]

            insertIndex = docIndex
            insertParent = parent
            for child in docElement:
                if insertParent is parent and not can_contain(parent, child):
                    insertParent = grandparent
                    insertIndex = parentIndex + 1
                
                if docStart is not None:
                    insertParent.insert(insertIndex, docStart)
                    insertIndex += 1
                    docStart = None
                insertParent.insert(insertIndex, child)
                child.set(
                    'liftedTree'
                    , 'parent' if insertParent is parent else 'grandparent')
                insertIndex += 1

            # If the doc_uri had no child elements, the start marker won't have
            # been inserted.
            if docStart is not None:
                insertParent.insert(insertIndex, docStart)
                insertIndex += 1
                docStart = None

            if docEnd is not None:
                insertParent.insert(insertIndex, docEnd)
                insertIndex += 1
                # insert_here(docEnd)

            # If insertion moved to the grandparent, then any remaining
            # children to the right of the doc_uri should be moved to a new
            # parent. The new parent should have the same tag as the original 
            # parent and be after the docEnd marker.
            if insertParent is grandparent and len(parent) > docIndex:
                tailParent = ET.Element(parent.tag)
                ET_copy_attr(parent, tailParent)
                tailParent.set('liftedTree', 'tailParent')
                tailParent.extend(parent[docIndex:])
                del parent[docIndex:]
                insertParent.insert(insertIndex, tailParent)
                insertIndex += 1
                # insert_here(tailParent)

            # Remove the parent if the doc_uri was its only child and has been
            # boosted to the grandparent so the parent is now empty.
            if docIndex == 0 and len(parent) == 0:
                del grandparent[parentIndex]

        found = element.find(".//paragraph//paragraph")
        if found is not None:
            raise AssertionError(
                f'Nested paragraph: {ET_string(found)}'
                f'\nunder:{ET_string(element)}')

        yield element

def can_contain(parentElement, childElement):
    layout = childElement.get('layout')
    docURI = childElement.get('resolved') is not None

    # The renderer sets an attribute layout:span on all span elements.  
    # This module sets layout:marker on <doc> elements that it inserts.  
    # Span and marker items can be contained by anything. So can doc_uri
    # elements, which could be encountered if nested.
    if layout == 'span' or layout == 'marker' or docURI:
        return True

    parent = parentElement.tag
    if parent == 'paragraph' or parent == 'header':
        # Paragraphs and headers cannot contain any block type.
        return False

    child = childElement.tag
    if parent == 'list_item':
        if child == 'paragraph' or child == 'list':
            return True
        if child == parent:
            return False

    if parent == 'list':
        return child == 'list_item'

    raise NotImplementedError(
        f"Don't know if {parent} can or cannot contain {child}.")
    
def set_newlines(iterator):
    detector = 'setNewlines'
    outcome = 'newlines'
    for element in iterator:
        for found in element.findall(f'.//*[@{detector}]'):
            # Find an immediate child with tag equal to the value of the
            # detector.
            found.set(outcome, str(
                1 if found.find(f'./{found.get(detector)}') is None else 2
            ))
        yield element

def resolve_splitters(iterator):
    for element in iterator:
        while True:
            grandparent, parent, splitter = ET_grandparent(
                element, f'*[@splitter="{str(True)}"]')
            if grandparent is None:
                break
            splitter.set('splitter', str(False))

            parentIndex = ET_index(grandparent, parent)
            splitterIndex = ET_index(parent, splitter)
            parent.set('split', f'{splitterIndex} {ET_string(splitter)}')
            if splitterIndex > 0:
                parent.set(
                    'split',
                    f'{splitterIndex} {ET_string(parent[splitterIndex - 1])}')
                splitParent = ET.Element(parent.tag)
                splitParent.extend(parent[splitterIndex:])
                splitParent.set('split', 'new')
                ET_copy_attr(parent, splitParent, 'newlines')
                del parent[splitterIndex:]
                grandparent.insert(parentIndex + 1, splitParent)
        yield element

def join_texts(iterator):
    # Join together adjacent `text` elements. This has the side effect of
    # discarding attributes of the second and subsequent elements. They'd
    # only have diagnostic transcript so it isn't too bad.

    for element in iterator:
        # The XPath finds parent elements of text elements.
        for found in element.findall('.//text/..'):
            consolidated = None
            removals = []
            # Go through the list start to finish. Any element that should be
            # consolidated with the previous element is added to the removals
            # list. Removals are processed after, to avoid modifying the list in
            # the middle of the enumeration.
            for index, child in enumerate(found):
                if child.tag == 'text':
                    if consolidated is None:
                        consolidated = child
                    else:
                        # The removals list will be highest first.
                        removals.insert(0, index)
                        consolidated.text += child.text
                else:
                    consolidated = None
            if len(removals) > 0:
                # found.set('consolidated', str(removals))
                found.set('consolidated', str([
                    [removal, found[removal].text] for removal in removals]))
                for index in removals:
                    del found[index]
        yield element

def strip_leading_newlines(iterator):
    # This is a carryover from the ad hoc Doctor.
    #
    # It's possible to get a leading line break, in some cases in which a doc:
    # substitution was made. Remove these here.
    for element in iterator:
        for paragraph in element.findall('.//paragraph/text/..'):
            found = paragraph.find('./text')
            if found is None or found.text is None:
                continue
            stripped = found.text.lstrip("\r\n")
            if stripped != found.text:
                found.set('stripped', str(len(found.text) - len(stripped)))
                found.text = stripped
        yield element
