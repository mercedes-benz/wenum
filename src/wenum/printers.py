from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wenum.fuzzobjects import FuzzResult, FuzzStats
import json
from .exception import FuzzExceptBadFile, FuzzExceptPluginError
from .facade import Facade
import sys
from abc import abstractmethod, ABC


class BasePrinter(ABC):
    def __init__(self, output):
        self.outputfile_handle = None
        # List containing every result information
        self.result_list = []
        if output:
            try:
                self.outputfile_handle = open(output, "w")
            except IOError as e:
                raise FuzzExceptBadFile("Error opening file. %s" % str(e))
        else:
            self.outputfile_handle = sys.stdout

        self.verbose = Facade().printers.kbase["verbose"]

    @abstractmethod
    def header(self, summary: FuzzStats):
        """
        Print at the beginning of the file
        """
        raise FuzzExceptPluginError("Method header not implemented")

    @abstractmethod
    def footer(self, summary: FuzzStats):
        """
        Print at the end of the file. Will also be called when runtime is done
        """
        raise FuzzExceptPluginError("Method footer not implemented")

    @abstractmethod
    def update_results(self, fuzz_result: FuzzResult, stats: FuzzStats):
        """
        Update the result list and return result information (response of request).
        """
        raise FuzzExceptPluginError("Method result not implemented")

    @abstractmethod
    def print_to_file(self, data_to_write):
        """
        Overwrite file contents with data
        """
        raise FuzzExceptPluginError("Method result not implemented")


class JSON(BasePrinter):
    name = "json"
    summary = "Results in json format"

    def __init__(self, output):
        BasePrinter.__init__(self, output)

    def header(self, stats: FuzzStats):
        # Empty JSON header to avoid messing up the file structure
        pass

    def update_results(self, fuzz_result: FuzzResult, stats: FuzzStats):
        location = ""
        if fuzz_result.history.redirect_header:
            location = fuzz_result.history.full_redirect_url
        server = ""
        if "Server" in fuzz_result.history.headers.response:
            server = fuzz_result.history.headers.response["Server"]
        post_data = []
        if fuzz_result.history.method.lower() == "post":
            for n, v in list(fuzz_result.history.params.post.items()):
                post_data.append({"parameter": n, "value": v})

        plugin_dict = {}

        for plugin in fuzz_result.plugins_res:
            # Removing ansi color escapes when logging, which plugins may
            # have inserted (magic from https://stackoverflow.com/a/14693789)
            # 7-bit C1 ANSI sequences
            ansi_escape = re.compile(r"""
                \x1B  # ESC
                (?:   # 7-bit C1 Fe (except CSI)
                    [@-Z\\-_]
                |     # or [ for CSI, followed by a control sequence
                    \[
                    [0-?]*  # Parameter bytes
                    [ -/]*  # Intermediate bytes
                    [@-~]   # Final byte
                )
            """, re.VERBOSE)
            result = ansi_escape.sub('', plugin.message)
            plugin_dict[plugin.name] = result

        res_entry = {
            "result_number": fuzz_result.result_number,
            "code": fuzz_result.code,
            "lines": fuzz_result.lines,
            "words": fuzz_result.words,
            "chars": fuzz_result.chars,
            "method": fuzz_result.history.method,
            "url": fuzz_result.url,
            "location": location,
            "post_data": post_data,
            "server": server,
            "description": fuzz_result.description,
            "plugins": plugin_dict
        }
        self.result_list.append(res_entry)
        return self.result_list

    def print_to_file(self, data_to_write):
        self.outputfile_handle.write(json.dumps(data_to_write))
        self.outputfile_handle.flush()
        # Resetting the file pointer so that the next file write overwrites the content
        self.outputfile_handle.seek(0)

    def footer(self, stats: FuzzStats):
        # Empty JSON footer to avoid messing up the file structure
        pass
