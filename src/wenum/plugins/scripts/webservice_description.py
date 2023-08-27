from urllib.parse import urlparse
from wenum.externals.moduleman.plugin import moduleman_plugin
from wenum.plugin_api.base import BasePlugin
from wenum.ui.console.common import Term


@moduleman_plugin
class WebserviceDescription(BasePlugin):
    name = "webservice_description"
    summary = "Looks for REST-APIs and queues endpoints that may contain interesting files."
    description = """Looks for REST-APIs and queues endpoints that may contain interesting files."""
    author = ("IPA",)
    version = "0.1"
    category = ["active"]
    priority = 99

    parameters = ()

    def __init__(self, options):
        BasePlugin.__init__(self, options)
        self.webservice_endpoint_list = [
            "application.wadl",
            "application.wadl?detail=true",
            "?_wadl",
            "/rs?_wadl",
        ]

    def validate(self, fuzz_result):
        return fuzz_result.code != 404

    def process(self, fuzz_result):
        # We want the check to be case-insensitive
        url = fuzz_result.url.lower()

        if url.endswith("/api") or url.endswith("/api/v1") or url.endswith("/api/v2") or \
                url.endswith("/services") or url.endswith("/webservices") or url.endswith("/ws"):
            for endpoint in self.webservice_endpoint_list:
                self.queue_url(fuzz_result.url + "/" + endpoint)

        parsed_url = urlparse(fuzz_result.url)
        split_path = parsed_url.path.split('/')
        # If the URL that has been found ends with one of the web service URLs
        if split_path[-1] in self.webservice_endpoint_list:
            if "<application" in fuzz_result.content:
                self.add_information(f"{self.term.color_string(self.term.fgYellow, 'REST description discovered.')}"
                                     f" Inspect endpoint")
