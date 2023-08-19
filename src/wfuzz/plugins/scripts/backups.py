from wfuzz.externals.moduleman.plugin import moduleman_plugin
from wfuzz.plugin_api.base import BasePlugin

from urllib.parse import urljoin


@moduleman_plugin
class Backups(BasePlugin):
    name = "backups"
    summary = "Looks for known backup filenames."
    description = ("""Looks for known backup filenames.
    For example, given http://localhost.com/dir/index.html, it will perform the following requests,
    * http://localhost/dir/index.EXTENSIONS,
    * http://localhost/dir/index.html.EXTENSIONS,
    * http://localhost/dir.EXTENSIONS""")
    author = ("Xavi Mendez (@xmendez)",)
    version = "0.1"
    category = ["fuzzer", "active"]
    priority = 99

    parameters = ((
                           "ext",
                           ".bak,.tgz,.zip,.tar.gz,~,.rar,.old,.swp",
                           False,
                           "Extensions to look for.",
                       ),)

    def __init__(self, options):
        BasePlugin.__init__(self, options)
        self.extensions = self.kbase["backups.ext"][0].split(",")

    def validate(self, fuzz_result):
        return fuzz_result.code != 404 and (
                fuzz_result.history.urlparse.fext not in self.extensions
        )

    def process(self, fuzz_result):
        for extension in self.extensions:

            # http://localhost/dir/test.html -----> test.BAKKK
            self.queue_url(urljoin(fuzz_result.url, fuzz_result.history.urlparse.fname + extension))

            # http://localhost/dir/test.html ---> test.html.BAKKK
            self.queue_url(urljoin(fuzz_result.url, fuzz_result.history.urlparse.ffname + extension))
