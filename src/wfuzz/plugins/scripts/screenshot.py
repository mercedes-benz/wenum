from wfuzz.plugin_api.base import BasePlugin
from wfuzz.externals.moduleman.plugin import moduleman_plugin

import subprocess
import tempfile
import pipes
import os
import re


@moduleman_plugin
class Screenshot(BasePlugin):
    name = "screenshot"
    author = ("Xavi Mendez (@xmendez)",)
    version = "0.1"
    summary = "Performs a screen capture using linux cutycapt tool"
    description = (
        "Performs a screen capture using linux cutycapt tool",
        "The tool must be installed and in the executable path",
    )
    category = ["tools", "active"]
    priority = 99

    parameters = ()

    def __init__(self, options):
        BasePlugin.__init__(self, options)

    def validate(self, fuzz_result):
        return fuzz_result.code not in [404]

    def process(self, fuzz_result):
        temp_name = next(tempfile._get_candidate_names())
        defult_tmp_dir = tempfile._get_default_tempdir()

        filename = os.path.join(
            defult_tmp_dir,
            (temp_name + "_" + re.sub(r"[^a-zA-Z0-9_-]", "_", fuzz_result.url))[:200]
            + ".jpg",
        )

        subprocess.call(
            [
                "cutycapt",
                "--url=%s" % pipes.quote(fuzz_result.url),
                "--out=%s" % filename,
                "--insecure",
                "--print-backgrounds=on",
            ]
        )
        self.add_information(f"Screenshot taken, output at {filename}")
