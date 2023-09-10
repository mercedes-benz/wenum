from urllib.parse import urljoin

from wenum.plugin_api.base import BasePlugin
from wenum.plugin_api.urlutils import parse_url
from wenum.externals.moduleman.plugin import moduleman_plugin


@moduleman_plugin
class DomainPath(BasePlugin):
    name = "domainpath"
    author = ("TKA",)
    version = "0.1"
    summary = "Enqueues domain name parts as part of the path."
    description = ("Enqueues subdomain names as part of the path. E.g. fuzzing something.example.com "
                   "will throw something.example.com/something, /example, /com",)
    category = ["active", "discovery"]
    priority = 99

    parameters = ()

    def __init__(self, session):
        BasePlugin.__init__(self, session)
        # To prevent always running a lot of code, already processed domains will not repeatedly validate
        self.processed_domains = []

    def validate(self, fuzz_result):
        domain_name = parse_url(fuzz_result.url).netloc
        # Only if the domain name is not numeric (which would mean it's an IP address), and if
        # the domain has not been processed yet
        if domain_name not in self.processed_domains and not domain_name.replace('.', '').replace(':', '').isnumeric():
            self.processed_domains.append(domain_name)
            return True
        return False

    def process(self, fuzz_result):
        parsed_url = parse_url(fuzz_result.url)
        domain_name = parsed_url.netloc
        # In case there is a port with :123, do not consider it
        domain_name_parsed = domain_name.split(':')[0]
        split_path = domain_name_parsed.split('.')

        for path in split_path:
            self.queue_url(urljoin(fuzz_result.url, path))
