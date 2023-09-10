import os
from urllib.parse import urlparse
import pathlib

from urllib.parse import urljoin

from wenum.plugin_api.base import BasePlugin
from wenum.externals.moduleman.plugin import moduleman_plugin


@moduleman_plugin
class Sourcemap(BasePlugin):
    name = "sourcemap"
    author = ("MTD",)
    version = "0.1"
    summary = "Check whether requested file is a JavaScript file or source map file."
    description = ("Checks for JavaScript files",)
    category = ["active", "discovery"]
    priority = 99

    parameters = (
    )

    def check_filter_options(self, fuzz_result):
        """
        #TODO Same problem as in context.py
        """
        if fuzz_result.chars in self.session.options.hs_list or fuzz_result.lines in self.session.options.hl_list or \
                fuzz_result.words in self.session.options.hw_list:
            return False
        else:
            return True

    def __init__(self, session):
        BasePlugin.__init__(self, session)

    def validate(self, fuzz_result):
        if fuzz_result.code in [200] and self.check_filter_options(fuzz_result):
            return True

        return False

    def process(self, fuzz_result):
        parsed_url = urlparse(fuzz_result.url)
        filename = os.path.basename(parsed_url.path)
        extension = pathlib.Path(filename).suffix.lower()

        if extension == ".js" or extension == ".jsx":
            self.add_information(f"JavaScript file "
                                 f"{filename} identified, checking for source map")
            map_url = urljoin(fuzz_result.url, parsed_url.path) + ".map"
            self.queue_url(map_url)
        elif extension == ".map":
            self.add_information(f"Potential source map {filename} identified")
