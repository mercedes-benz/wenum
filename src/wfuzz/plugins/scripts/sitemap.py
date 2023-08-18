from wfuzz.plugin_api.mixins import DiscoveryPluginMixin
from wfuzz.plugin_api.base import BasePlugin
from wfuzz.externals.moduleman.plugin import moduleman_plugin

import xml.dom.minidom


@moduleman_plugin
class Sitemap(BasePlugin, DiscoveryPluginMixin):
    name = "sitemap"
    author = ("Xavi Mendez (@xmendez)",)
    version = "0.1"
    summary = "Parses sitemap.xml file"
    description = ("Parses sitemap.xml file",)
    category = ["active", "discovery"]
    priority = 99

    parameters = ()

    def __init__(self, options):
        BasePlugin.__init__(self, options)

    def validate(self, fuzz_result):
        return (
                fuzz_result.history.urlparse.ffname == "sitemap.xml"
                and fuzz_result.code == 200
        )

    def process(self, fuzz_result):
        try:
            dom = xml.dom.minidom.parseString(fuzz_result.history.content)
        except Exception:
            self.add_exception_information(f"Error while parsing {fuzz_result.url}")

        url_list = dom.getElementsByTagName("loc")
        for url in url_list:
            u = url.childNodes[0].data

            self.queue_url(u)
