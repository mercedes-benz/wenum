from urllib.parse import urljoin

from wenum.plugin_api.mixins import DiscoveryPluginMixin
from wenum.plugin_api.base import BasePlugin
from wenum.plugin_api.urlutils import check_content_type
from wenum.externals.moduleman.plugin import moduleman_plugin


@moduleman_plugin
class Robots(BasePlugin, DiscoveryPluginMixin):
    name = "robots"
    author = ("Xavi Mendez (@xmendez)",)
    version = "0.1"
    summary = "Parses robots.txt looking for new content."
    description = ("Parses robots.txt looking for new content.",)
    category = ["active", "discovery", "active_default"]
    priority = 99

    parameters = ()

    def __init__(self, options):
        BasePlugin.__init__(self, options)

    def validate(self, fuzz_result):
        return (
                fuzz_result.history.urlparse.ffname == "robots.txt"
                and fuzz_result.code == 200
                and check_content_type(fuzz_result, "text")
        )

    def process(self, fuzz_result):
        self.add_information(f"robots.txt detected. Processing")
        # Shamelessly (partially) copied from w3af's plugins/discovery/robotsReader.py
        for line in fuzz_result.history.content.split("\n"):
            line = line.strip()

            if (
                len(line) > 0
                and line[0] != "#"
                and (
                    line.upper().find("ALLOW") == 0
                    or line.upper().find("DISALLOW") == 0
                    or line.upper().find("SITEMAP") == 0
                )
            ):

                url = line[line.find(":") + 1:]
                url = url.strip(" *")

                if url:
                    new_link = urljoin(fuzz_result.url, url)
                    self.queue_url(new_link)
