import socket
from urllib.parse import parse_qs


from wenum.plugin_api.base import BasePlugin
from wenum.plugin_api.urlutils import parse_url
from wenum.externals.moduleman.plugin import moduleman_plugin


@moduleman_plugin
class DaimlerSSO(BasePlugin):
    name = "daimler_sso"
    author = ("MTD",)
    version = "0.1"
    summary = "Checks if redirects Daimler SSO."
    description = ("Checks if redirects Daimler SSO.",)
    category = ["active", "discovery"]
    priority = 99

    parameters = ()

    def __init__(self, options):
        BasePlugin.__init__(self, options)

    def validate(self, fuzz_result):
        if fuzz_result.code in [302, 301]:
            target_link = fuzz_result.history.full_redirect_url
            parsed_target_url = parse_url(target_link)
            target_hostname = parsed_target_url.netloc.strip()

            sso_providers = [
                "sso.daimler.com",
                "sso-int.daimler.com"
                "sso.mercedes-benz.com",
                "sso-int.mercedes-benz.com",
            ]

            if target_hostname in sso_providers:
                return True

        return False

    def process(self, fuzz_result):
        redirect_hostname = ""
        try:
            target_link = fuzz_result.history.full_redirect_url
            parsed_target_url = parse_url(target_link)

            query_args = parse_qs(parsed_target_url.query)
            redirect_uri = query_args['redirect_uri'][0]

            scope_url_object = parse_url(fuzz_result.url)
            scope_hostname = scope_url_object.netloc.strip()

            redirect_url_object = parse_url(redirect_uri)
            redirect_hostname = redirect_url_object.netloc.strip()

            if scope_hostname.find(':') != -1:
                scope_hostname = scope_hostname[0:scope_hostname.find(':')]

            scope_ip = socket.gethostbyname(scope_hostname)

            if redirect_hostname.find(':') != -1:
                redirect_hostname = redirect_hostname[0:redirect_hostname.find(':')]

            target_ip = socket.gethostbyname(redirect_hostname)
        except:
            self.add_exception_information(f"Exception on {redirect_hostname}")
            return

        if target_ip == scope_ip or scope_hostname == redirect_hostname:
            self.add_information(f"Target URL in scope: {fuzz_result.url} --> {redirect_url_object.geturl()}")
            self.queue_url(redirect_url_object.geturl())
        else:
            self.add_information(f"Target URL NOT in scope: {fuzz_result.url} --> {redirect_url_object.geturl()}")
