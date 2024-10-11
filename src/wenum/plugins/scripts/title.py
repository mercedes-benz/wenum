from urllib.parse import urljoin

from wenum.plugin_api.base import BasePlugin
from wenum.externals.moduleman.plugin import moduleman_plugin
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
import warnings

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

    def __init__(self, session):
        BasePlugin.__init__(self, session)

    def validate(self, fuzz_result):
        return True

    def process(self, fuzz_result):
        soup = BeautifulSoup(fuzz_result.history.content, "html.parser")

        title = soup.title.string if soup.title else ""

        if title and title != "" and title not in self.kbase["title"]:
            self.kbase["title"] = title
            self.add_information(f"[u]{title}[/u]")
            if title == "Your Azure Function App is up and running.":
                self.add_information("Azure Function App detected")
                self.queue_url(urljoin(fuzz_result.url, "api/"))
                self.queue_url(urljoin(fuzz_result.url, "admin/"))