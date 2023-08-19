from wfuzz.plugin_api.base import BasePlugin
from wfuzz.externals.moduleman.plugin import moduleman_plugin

KBASE_NEW_COOKIE = "cookies.cookie"


@moduleman_plugin
class Cookies(BasePlugin):
    name = "cookies"
    author = ("Xavi Mendez (@xmendez)",)
    version = "0.1"
    summary = "Looks for new cookies"
    description = ("Looks for new cookies",)
    category = ["info", "passive", "default"]
    priority = 99

    parameters = ()

    def __init__(self, options):
        BasePlugin.__init__(self, options)

    def validate(self, fuzz_result):
        return True

    def process(self, fuzz_result):
        new_cookies = list(fuzz_result.history.cookies.response.items())

        if len(new_cookies) > 0:
            for name, value in new_cookies:

                if (
                    name != ""
                    and KBASE_NEW_COOKIE not in self.kbase
                    or name not in self.kbase[KBASE_NEW_COOKIE]
                ):
                    self.kbase[KBASE_NEW_COOKIE] = name
                    coloured_key = self.term.colour_string(self.term.fgBlue, name)
                    coloured_value = self.term.colour_string(self.term.fgYellow, value)
                    self.add_information(f"Cookie first set: {coloured_key}={coloured_value}")
