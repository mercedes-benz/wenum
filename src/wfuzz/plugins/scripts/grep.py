import re

from wfuzz.plugin_api.base import BasePlugin
from wfuzz.exception import FuzzExceptPluginBadParams
from wfuzz.externals.moduleman.plugin import moduleman_plugin


@moduleman_plugin
class Grep(BasePlugin):
    name = "grep"
    author = ("Xavi Mendez (@xmendez)",)
    version = "0.1"
    summary = "HTTP response grep"
    description = (
        "Extracts the given regex pattern from the HTTP response and prints it",
        "(It is not a filter operator)",
    )
    category = ["tools"]
    priority = 99

    parameters = (("regex", "", True, "Regex to perform the grep against."),)

    def __init__(self, options):
        BasePlugin.__init__(self, options)
        try:
            print(self.kbase["grep.regex"])
            self.regex = re.compile(
                self.kbase["grep.regex"][0], re.MULTILINE | re.DOTALL
            )
        except Exception:
            raise FuzzExceptPluginBadParams(
                "Incorrect regex or missing regex parameter."
            )

    def validate(self, fuzz_result):
        return True

    def process(self, fuzz_result):
        for r in self.regex.findall(fuzz_result.history.content):
            self.add_information(f"Pattern match {r}")
