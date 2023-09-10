from wenum.plugin_api.base import BasePlugin
from wenum.plugin_api.urlutils import parse_url
from wenum.externals.moduleman.plugin import moduleman_plugin
import subprocess


@moduleman_plugin
class Gau(BasePlugin):
    name = "gau"
    author = ("MTD",)
    version = "0.1"
    summary = "Execute gau once."
    description = ("Execute gau once",)
    category = ["active", "discovery"]
    priority = 99
    output = []

    parameters = (
    )

    def __init__(self, session):
        BasePlugin.__init__(self, session)
        self.proxy_list = session.options.proxy_list
        self.run_once = True

    def validate(self, fuzz_result):
        return True

    @staticmethod
    def exec_cmd(cmd):
        cmd_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, executable='/bin/bash')
        stdout, stderr = cmd_process.communicate()
        return stdout

    def process(self, fuzz_result):
        initial_url = fuzz_result.history.fuzzing_url.replace("FUZZ", "")
        if self.proxy_list:
            # Concatenate protocol + IP + port -> e.g. SOCKS5://127.0.0.1:8081
            proxy_string = self.proxy_list[0]
            proxy_option = f"--proxy {proxy_string}"
        else:
            proxy_option = ""

        parsed_link = parse_url(initial_url)
        target_url = (parsed_link.hostname + parsed_link.path).rstrip("/")

        gau_cmd = f"gau {target_url} {proxy_option} --threads 10 --blacklist ttf,woff,svg,png,jpg,gif,ico"
        gau_urls = self.exec_cmd(gau_cmd)
        gau_urls = gau_urls.decode("utf-8").splitlines()
        if not gau_urls:
            self.add_information(f"Did not find anything")
            return

        for url in gau_urls:
            self.queue_url(url)
