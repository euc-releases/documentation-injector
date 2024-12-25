# Run with Python 3
# Copyright 2024 Omnissa, LLC.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Doctor main module. Part of the Doctor documentation tool.
No standalone capability.
"""
# Exit if run other than as a module.
if __name__ == '__main__':
    print(__doc__)
    raise SystemExit(1)

# Standard library imports, in alphabetic order.
#
# Sequence comparison module.
# https://docs.python.org/3/library/difflib.html#difflib.context_diff
from difflib import context_diff
#
# JSON module.
# https://docs.python.org/3/library/json.html
import json
#
# Module for walking a directory and working with paths.
# https://docs.python.org/3/library/os.html#os.walk
# https://docs.python.org/3/library/os.path.html
import os
#
# Module for file copy.
# https://docs.python.org/3/library/shutil.html
import shutil
#
# Module for getting the current time. Used in extraction mode.
# https://docs.python.org/3/library/time.html#module-time
import time
#
# Temporary file module.
# https://docs.python.org/3/library/tempfile.html
from tempfile import NamedTemporaryFile
#
# Local imports
#
# Modules in the Doctor package.
from doctor import getter
from doctor.processing import Processing
from doctor.processing_adhoc import ProcessingAdHoc

class Doctor:
    @property
    def maxWidth(self):
        return self._maxWidth
    @maxWidth.setter
    def maxWidth(self, maxWidth):
        self._maxWidth = maxWidth
    
    @property
    def adHoc(self):
        return self._adHoc
    @adHoc.setter
    def adHoc(self, adHoc):
        self._adHoc = adHoc

    @property
    def dryRun(self):
        return self._dryRun
    @dryRun.setter
    def dryRun(self, dryRun):
        self._dryRun = dryRun

    @property
    def extractDir(self):
        return self._extractDir
    @extractDir.setter
    def extractDir(self, extractDir):
        self._extractDir = extractDir
    
    @property
    def extractMode(self):
        return self._extractMode
    @extractMode.setter
    def extractMode(self, extractMode):
        self._extractMode = extractMode
    
    @property
    def injector(self):
        return self._injector
    @injector.setter
    def injector(self, injector):
        self._injector = injector

    @property
    def markers(self):
        return self._markers
    @markers.setter
    def markers(self, markers):
        self._markers = markers

    def load_cache(self, *paths):
        if self.injector is None:
            self.injector = getter.DocGetter()
        self.injector.load(*paths)
    
    class Report:
        # Empty class, for now. It's used for the file-level report, and for the
        # job-level.
        pass
    
    def overwrite_all(self, paths):
        self._processor = (
            ProcessingAdHoc(self) if self.adHoc else Processing(self))

        report = self.Report()
        report.totalFiles = 0
        report.overwrites = 0
        report.edited = 0
        report.extensionCounts = {}
        for reportOne in self._overwrite_all(paths):
            edited = reportOne.diffs is not None and len(reportOne.diffs) > 0
            report.totalFiles += 1
            report.overwrites += 1 if reportOne.overwrote else 0
            report.edited += 1 if edited else 0

            extensionKey = (
                "not checked" if reportOne.extension is None
                else reportOne.extension[1:])
            if extensionKey in report.extensionCounts:
                report.extensionCounts[extensionKey] += 1
            else:
                report.extensionCounts[extensionKey] = 1
            
            if reportOne.extension is None:
                reportOne.extension = "not checked"

            yield reportOne.__dict__
        
        self.report = report.__dict__

    def _overwrite_all(self, paths):
        # Inject / extract documentation into / from each source file in paths
        for path in paths:
            if os.path.isdir(path):
                # Directory - loop over all files (inc. those in subdirs)
                for dirpath, _, filenames in os.walk(path):
                    for filename in filenames:
                        # Single file
                        if filename == '.DS_Store':
                            continue
                        report = self.Report()
                        report.path = os.path.join(dirpath, filename)
                        report.extension = os.path.splitext(filename)[1]
                        report.overwrote = report.extension in self.extensions
                        report.extract = self.extractMode
                        if report.overwrote:
                            # filetype is supported - inspect file
                            self._overwrite_one(report)
                        else:
                            report.lineTypes = None
                            report.diffs = None
                        yield report
            else:
                # Single file
                report = self.Report()
                report.path = path
                report.extension = None
                report.overwrote = True
                report.extract = self.extractMode
                # inspect file (regardless of filetype suitability)
                self._overwrite_one(report)
                yield report

    def _overwrite_one(self, report):
        # Inject / extract documentation into / from source file in report
        sourcePath = None
        report.lineTypes = {}
        
        # Extraction mode: docPath = path to new '.md' file
        # Injection mode: docPath = 'None'
        docPath = self._create_extract_path(report)

        # Create a temporary file
        with NamedTemporaryFile(mode='w', delete=False) as sourceFile:
            sourcePath = sourceFile.name
            reader = self._processor.path_to_comments(report.path)
            if report.extract:
                # extraction mode
                self._processor.comments_to_extract(
                    reader, report, docPath, sourceFile)
            else:
                # injection mode
                if self.injector is None:
                    self.injector = getter.DocGetter()
                self._processor.comments_to_outputs(
                    reader, sourceFile, report.path, report.lineTypes)
        #
        # Generate a context-diff with one line of context. The diff can be
        # printed by the main.py script.
        report.diffs = None
        with open(report.path) as originalFile:
            with open(sourcePath) as editedFile:
                report.diffs = tuple(context_diff(
                    originalFile.readlines(), editedFile.readlines(),
                    fromfile=report.path, tofile="Edited by the Doctor.", n=1))

        if not self.dryRun:
            shutil.copy(sourcePath, report.path)
        os.remove(sourcePath)
    
    def _create_extract_path(self, report):
        # Generate relative path to a target '.md' file
        if self.dryRun or not report.extract:
            report.extractPath = None
            return None
        extractPath = ".".join((os.path.splitext(report.path)[0], "md"))   

        # if extract dir - then create .md file there (retaining dir tree)
        if self.extractDir is None:
            report.extractPath = extractPath
        else:
            commonRoot = os.path.commonpath([extractPath, self.extractDir])
            commonToSource = os.path.relpath(extractPath, commonRoot)
            report.extractPath = os.path.join(self.extractDir, commonToSource)

            # create directory tree inside extraction dir
            finalExtractDir = os.path.abspath(os.path.join(
                report.extractPath, os.pardir))
            os.makedirs(finalExtractDir, exist_ok=True)

        if os.path.exists(report.extractPath):
            raise RuntimeError(
                'Extract path exists already "{}".'.format(report.__dict__))
        
        # Create the new '.md' file 
        with open(report.extractPath, mode="w") as extractFile:
            extractFile.writelines((
                "Automatic extraction by the Doctor.\n",
                "Extract time (ISO 8601): ", time.strftime("%FT%T%z%n")
            ))
            json.dump(report.__dict__, extractFile, indent=2)
            extractFile.write("\n\n")
        
        # Return a path to the '.md' file relative to the source file
        if self.extractDir is not None :
            parDirReport = os.path.join(report.path, os.pardir)
            relPath = os.path.relpath(report.extractPath, parDirReport);
            
            # Doctor relative paths must start with '../' or './' 
            if not relPath.startswith('../') and not relPath.startswith('./') :
                relPath = "./" + relPath
            return relPath
        else :
            return os.path.join(
                os.path.relpath(os.path.dirname(report.path)
                                , os.path.dirname(report.extractPath)),
                os.path.basename(report.extractPath))
    
    def add_fragment(self, path, startLine, finishLine, texts):
        fragment = f"line-{startLine}-{finishLine}"
        if path is not None and not self.dryRun:
            with open(path, mode="a") as extractFile:
                # The texts will have EOL, if they were present in the original
                # source. The last newline is always stripped by the Doctor, so an
                # extra one is added here.
                extractFile.writelines((
                    "# ", fragment, "\n", *texts, "\n"))
        return fragment
    
    def __init__(self):
        self._maxWidth = None
        self._adHoc = False
        self._dryRun = False
        self._markers = False
        self._extractDir = None
        self._extractMode = False
        
        self.extensions = ['.h', '.swift']
        self.report = None
        self._injector = None

