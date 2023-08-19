from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wenum.fuzzobjects import FuzzResult, FuzzStats
import json as jjson

from wenum.externals.moduleman.plugin import moduleman_plugin
from wenum.plugin_api.base import BasePrinter


@moduleman_plugin
class JSON(BasePrinter):
    name = "json"
    summary = "Results in json format"
    author = ("Federico (@misterade)", "Minor rework by Ilya Glotov (@ilyaglow)")
    version = "0.2"
    category = ["default"]
    priority = 99

    def __init__(self, output):
        BasePrinter.__init__(self, output)

    def header(self, stats: FuzzStats):
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
        self.outputfile_handle.write(jjson.dumps(data_to_write))
        self.outputfile_handle.flush()
        # Resetting the file pointer so that the next file write overwrites the content
        self.outputfile_handle.seek(0)

    def footer(self, stats: FuzzStats):
        pass
        #self.outputfile_handle.write(jjson.dumps(self.json_res))
