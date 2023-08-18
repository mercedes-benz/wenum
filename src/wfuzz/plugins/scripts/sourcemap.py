import os
from urllib.parse import urlparse
import pathlib

from urllib.parse import urljoin

from wfuzz.plugin_api.base import BasePlugin
from wfuzz.externals.moduleman.plugin import moduleman_plugin


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

    def check_filter_options(self, fuzzresult):
        if fuzzresult.chars in self.options.data['hh'] or fuzzresult.lines in \
                self.options.data['hl'] or fuzzresult.words in self.options.data['hw']:
            return False
        else:
            return True

    def __init__(self, options):
        BasePlugin.__init__(self, options)

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
