import re

from wenum.plugin_api.base import BasePlugin
from wenum.plugin_api.static_data import LISTING_dir_indexing_regexes
from wenum.externals.moduleman.plugin import moduleman_plugin
from wenum.ui.console.term import Term


@moduleman_plugin
class Listing(BasePlugin):
    name = "listing"
    author = ("Xavi Mendez (@xmendez)",)
    version = "0.1"
    summary = "Looks for directory listing vulnerabilities"
    description = ("Looks for directory listing vulnerabilities",)
    category = ["default", "passive", "info"]
    priority = 99

    parameters = ()

    def __init__(self, options):
        BasePlugin.__init__(self, options)

        self.regex = []
        for i in LISTING_dir_indexing_regexes:
            self.regex.append(re.compile(i, re.MULTILINE | re.DOTALL))

    def validate(self, fuzz_result):
        return fuzz_result.code in [200]

    def process(self, fuzz_result):
        for r in self.regex:
            if len(r.findall(fuzz_result.history.content)) > 0:
                self.add_information(f"{self.term.color_string(self.term.fgYellow, 'Directory listing')} identified")
                break
