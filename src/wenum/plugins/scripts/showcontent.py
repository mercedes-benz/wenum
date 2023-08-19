from wenum.plugin_api.base import BasePlugin
from wenum.externals.moduleman.plugin import moduleman_plugin


@moduleman_plugin
class ShowContent(BasePlugin):
    name = "show_content"
    author = ("MTD",)
    version = "0.1"
    summary = "Show used HTTP method"
    description = ("Show used HTTP method.",)
    category = ["debug"]
    priority = 99

    parameters = (
    )

    def __init__(self, options):
        BasePlugin.__init__(self, options)

    def validate(self, fuzz_result):
        # if(fuzzresult.history.method in ["HEAD"]):
        return True

    def process(self, fuzz_result):
        self.add_information(f"{fuzz_result.history.content}")
