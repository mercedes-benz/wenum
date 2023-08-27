import re

from wenum.plugin_api.base import BasePlugin
from wenum.plugin_api.static_data import ERRORS_regex_list
from wenum.externals.moduleman.plugin import moduleman_plugin
from wenum.ui.console.common import Term


@moduleman_plugin
class Errors(BasePlugin):
    name = "errors"
    author = ("Xavi Mendez (@xmendez)",)
    version = "0.1"
    summary = "Looks for known error messages"
    description = ("Looks for common error messages",)
    category = ["default", "passive", "info"]
    priority = 99

    parameters = ()

    def __init__(self, options):
        BasePlugin.__init__(self, options)

        self.error_regex = []
        for regex in ERRORS_regex_list:
            self.error_regex.append(re.compile(regex, re.MULTILINE | re.DOTALL))

    def validate(self, fuzz_result):
        return True

    def process(self, fuzz_result):
        for regex in self.error_regex:
            # Some error pages contain the same error message several times,
            # but logging them more than once would not be of interest and clutters the log instead
            unique_regex_matches = set(regex.findall(fuzz_result.history.content))
            for regex_match in unique_regex_matches:
                colored_part = self.term.color_string(self.term.fgRed, regex_match)
                self.add_information(f"{colored_part}")
