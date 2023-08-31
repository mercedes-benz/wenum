from wenum.plugin_api.base import BasePlugin
from wenum.externals.moduleman.plugin import moduleman_plugin
from wenum.ui.console.term import Term


@moduleman_plugin
class Title(BasePlugin):
    name = "title"
    author = ("Xavi Mendez (@xmendez)",)
    version = "0.1"
    summary = "Parses HTML page title"
    description = ("Parses HTML page title",)
    category = ["info", "passive", "default"]
    priority = 99

    parameters = ()

    def __init__(self, options):
        BasePlugin.__init__(self, options)

    def validate(self, fuzz_result):
        return True

    def process(self, fuzz_result):
        soup = fuzz_result.history.get_soup()
        title = soup.title.string if soup.title else ""

        if title and title != "" and title not in self.kbase["title"]:
            self.kbase["title"] = title
            self.add_information(f"{self.term.color_string(self.term.fgYellow, title)}")
