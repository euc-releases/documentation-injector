# Run with Python 3
# Copyright 2019 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Documentation source reader. Part of the Doctor documentation tool.
No standalone capability.
"""
# Exit if run other than as a module.
if __name__ == '__main__':
    print(__doc__)
    raise SystemExit(1)

#
# Standard library imports, in alphabetic order.
#
# Module for walking a directory and working with paths.
# https://docs.python.org/3/library/os.html#os.walk
# https://docs.python.org/3/library/os.path.html
import os
#
# Module for OO path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path
#
# URI parsing module.
# https://docs.python.org/3/library/urllib.parse.html
from urllib.parse import urlparse
#
# Module for XML handling.
# https://docs.python.org/3.5/library/xml.etree.elementtree.html#module-xml.etree.ElementTree
import xml.etree.ElementTree as ET

class DocGetter:
    def __init__(self):
        self._cachedFragments = []
        self._cachedFiles = []
    
    class Cache:
        def __init__(self, absPath, fragment, contentLines):
            self.absPath = absPath
            self.fragment = fragment
            self.contentLines = contentLines
        
        @classmethod
        def read(cls, absPath):
            contentLines = None
            fragment = None
            with open(absPath) as docFile:
                for line in docFile:
                    if fragment is not None:
                        if line.startswith("#") and not line.startswith("##"):
                            # Remove any EOL characters from the last line of
                            # content.
                            try:
                                contentLines[-1] = contentLines[
                                    -1].rstrip("\n\r")
                            except IndexError:
                                pass
                            yield cls(absPath, fragment, contentLines)
                            fragment = None
                            contentLines = None
                        else:
                            contentLines.append(line)

                    if fragment is None and line.startswith("#"):
                        fragment = line[1:].strip()
                        if fragment == "" or fragment.startswith("#"):
                            fragment = None
                        else:
                            contentLines = []
            if fragment is not None:
                yield cls(absPath, fragment, contentLines)
    
    def get_content(self, uri, basePath):
        # Backward compatible wrapper.
        return self._get_content(uri, basePath).contentLines

    def resolve(self, element):
        # New element-based return.
        sourceStr = element.get('source')
        cache = self._get_content(element.get('uri'), sourceStr)
        element.set('contentLines', str(len(cache.contentLines)))
        element.set('content', ''.join(cache.contentLines))
        return os.path.relpath(cache.absPath)
    
    def read(self, iterator, treeParser):
        for element in iterator:
            while True:
                count = 0
                for docOuter in element.findall(
                    f".//*[@resolved='{str(False)}']"
                ):
                    # Next line will:
                    #
                    # -   Resolve one level of the doc: uri, i.e. without
                    #     recursion.
                    # -   Set the resolution text into the `content` attribute.
                    # -   Set a count of the lines in the resolution text into
                    #     the `contentLines` attribute. The line count is needed
                    #     later.
                    source = self.resolve(docOuter)
                    #
                    # Next lines will parse the resolution text into an element
                    # tree, and then put the tree under the doc_uri element. The
                    # `source` attributes of any doc_uri elements in the
                    # resolution are set to the path of the original file from
                    # which the cache was loaded.
                    markdownInner = treeParser(docOuter.get('content'))
                    for docInner in markdownInner.findall(".//doc_uri"):
                        docInner.set('source', source)
                    docOuter.extend(markdownInner[:])

                    count += 1
                    docOuter.set('resolved', str(True))

                if count == 0:
                    break
            yield element

    def _get_content(self, uri, basePath):
        # Change backslash to forward slash in case this code gets run on a doc:
        # uri written on a Windows machine. 
        parsed = urlparse(uri.replace("\\", '/'))
        if parsed.netloc in ('.', '..'):
            path = os.path.dirname(os.path.abspath(basePath))
            if parsed.netloc == '..':
                path = os.path.join(path, os.path.pardir)
        elif parsed.netloc == "":
            path = None
        else:
            raise ValueError("Don't know how to get_content for"
                             '{} "{}".'.format(parsed, basePath))
        
        path = (
            None if path is None
            else os.path.abspath(''.join((path, parsed.path))))
        
        cached = None
        try:
            if path is not None:
                self.load_file(path)
            for cache in self._cachedFragments:
                if (cache.fragment == parsed.fragment
                    and (path is None or cache.absPath == path)
                ):
                    cached = cache
        except IOError as error:
            # Re-raise with context details.
            raise IOError(
                f'Error getting content for "{uri}" relative to:"{basePath}"'
            ) from error
        
        if cached is None:
            raise ValueError('Content for URI "{}" {} not found in {}.'.format(
                uri, parsed
                , "cache" if path is None else 'file "{}"'.format(path)))
        
        return cached
    
    def load(self, *paths):
        for path in paths:
            path = os.path.abspath(path)
            if os.path.isfile(path):
                self.load_file(path)
            else:
                for dirpath, _, filenames in os.walk(path):
                    for filename in filenames:
                        self.load_file(os.path.join(dirpath, filename))

    def load_file(self, path):
        if path in self._cachedFiles:
            return
        fragments = []
        for cache in self.Cache.read(path):
            self._cachedFragments[0:0] = [cache]
            if cache.fragment in fragments:
                raise RuntimeError(
                    'Repeated fragment "{}" in file "{}".'.format(
                        cache.fragment, path))
            fragments.append(cache.fragment)
            self._cachedFiles.append(path)
