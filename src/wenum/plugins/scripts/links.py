import os
import re

from urllib.parse import urljoin
import pathlib

from wenum.plugin_api.mixins import DiscoveryPluginMixin
from wenum.plugin_api.base import BasePlugin
from wenum.plugin_api.static_data import valid_codes, head_extensions
from wenum.plugin_api.urlutils import parse_url
from wenum.externals.moduleman.plugin import moduleman_plugin


@moduleman_plugin
class Links(BasePlugin, DiscoveryPluginMixin):
    """
    # TODO We want to phase this out. Functionality should be replaced by follow_redirects and linkparser.py.
        Make sure linkparser does not miss things this plugin catches, and delete plugin
    """
    name = "links"
    author = ("Xavi Mendez (@xmendez)",)
    version = "0.1"
    summary = "Parses HTML looking for new content."
    description = ("Parses HTML looking for new content. Redirects to dirs of URLs and to files of them if proper "
                   "URLs are detected through regex statements.",)
    category = ["active", "discovery"]
    priority = 99

    limit = 10

    parameters = (
        (
            "add_path",
            "False",
            False,
            "if True, re-enqueue found paths. ie. /path/link.html link enqueues also /path/",
        ),
        (
            "domain",
            None,
            False,
            "Regex of accepted domains tested against url.netloc. This is useful for restricting crawling certain domains.",
        ),
        (
            "regex",
            None,
            False,
            "Regex of accepted links tested against the full url. If domain is not set and regex is, domain defaults to .*. This is useful for restricting crawling certain file types.",
        ),
    )

    def __init__(self, session):
        BasePlugin.__init__(self, session)

        # Detect links based on these regex statements
        regex = [
            r'\b(?:(?<!data-)href)="((?!mailto:|tel:|#|javascript:).*?)"',
            r'\bsrc="((?!javascript:).*?)"',
            r'\baction="((?!javascript:).*?)"',
            r'<meta.*content="\d+;url=(.*?)">',  # http://en.wikipedia.org/wiki/Meta_refresh
            r'getJSON\("(.*?)"',
            r"[^/][`'\"]([\/][a-zA-Z0-9_.-]+)+(?!(?:[,;\s]))",  # based on https://github.com/nahamsec/JSParser/blob/master/handler.py#L93
        ]

        self.regex = []
        for regex_str in regex:
            self.regex.append(re.compile(regex_str, re.MULTILINE | re.DOTALL))

        self.regex_header = [
            ("Link", re.compile(r"<(.*)>;")),
            ("Location", re.compile(r"(.*)")),
        ]

        self.add_path = self._bool(self.kbase["links.add_path"][0])

        self.domain_regex = None
        if self.kbase["links.domain"][0]:
            self.domain_regex = re.compile(
                self.kbase["links.domain"][0], re.IGNORECASE
            )

        self.regex_param = None
        if self.kbase["links.regex"][0]:
            self.regex_param = re.compile(
                self.kbase["links.regex"][0], re.IGNORECASE
            )

        if self.regex_param and self.domain_regex is None:
            self.domain_regex = re.compile(".*", re.IGNORECASE)

        self.list_links = set()

    def validate(self, fuzz_result):
        self.list_links = set()
        return fuzz_result.code in valid_codes

    def process(self, fuzz_result):
        # <a href="www.owasp.org/index.php/OWASP_EU_Summit_2008">O
        # ParseResult(scheme='', netloc='', path='www.owasp.org/index.php/OWASP_EU_Summit_2008', params='', query='', fragment='')

        for header, regex in self.regex_header:
            if header in fuzz_result.history.headers.response:
                all_links = regex.findall(fuzz_result.history.headers.response[header])
                for link_url in all_links:
                    if link_url:
                        self.process_link(fuzz_result, link_url)

        for regex in self.regex:
            all_links = regex.findall(fuzz_result.history.content)
            if not all_links:
                continue
            for link_url in all_links:
                if link_url:
                    self.process_link(fuzz_result, link_url)

    def process_link(self, fuzz_result, link_url):
        parsed_link = parse_url(link_url)

        if (
            not parsed_link.scheme
            or parsed_link.scheme == "http"
            or parsed_link.scheme == "https"
        ) and self.from_domain(parsed_link):
            #TODO Cache key does not need to be manually checked. PluginManager handles centrally
            cache_key = parsed_link.cache_key(self.base_fuzz_res.history.urlparse)
            if cache_key not in self.list_links:
                self.list_links.add(cache_key)
                self.enqueue_link(fuzz_result, link_url, parsed_link)

    def enqueue_link(self, fuzz_result, link_url, parsed_link):
        filename = os.path.basename(parsed_link.path)
        extension = pathlib.Path(filename).suffix

        # dir path
        if self.add_path:
            split_path = parsed_link.path.split("/")
            newpath = "/".join(split_path[:-1]) + "/"
            full_path_url = urljoin(fuzz_result.url, newpath)
            self.queue_url(full_path_url)

        # file path
        new_link = urljoin(fuzz_result.url, link_url)
        split_path = parsed_link.path.split("/")

        if not self.regex_param or (
            self.regex_param and self.regex_param.search(new_link) is not None
        ):
            links = set()
            links.add(new_link)
            if extension in [".js", ".json"]:
                # try each directory
                for i in range(1, len(split_path)-1):
                    newpath = "/".join(split_path[:i]) + "/" + filename
                    links.add(urljoin(fuzz_result.url, newpath))
                # the other way around (remove directories from the start)
                for i in range(len(split_path)-1, 0, -1):
                    newpath = "/".join(split_path[i:-1]) + "/" + filename
                    links.add(urljoin(fuzz_result.url, newpath))
            if extension in head_extensions:
                for link in links:
                    self.queue_url(link, method="HEAD")
            else:
                for link in links:
                    self.queue_url(link)

    def from_domain(self, parsed_link):
        # Returns True if it is a relative path
        if not parsed_link.netloc and parsed_link.path:
            return True

        # regex domain
        if (
            self.domain_regex
            and self.domain_regex.search(parsed_link.netloc) is not None
        ):
            return True

        # same domain
        if parsed_link.netloc == self.base_fuzz_res.history.urlparse.netloc:
            return True

        if (
            parsed_link.netloc
            and parsed_link.netloc not in self.kbase["links.new_domains"]
        ):
            self.kbase["links.new_domains"].append(parsed_link.netloc)
