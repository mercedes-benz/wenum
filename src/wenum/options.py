import logging
import sys
from typing import Optional
from urllib.parse import urlparse

from .exception import (
    FuzzExceptBadRecipe,
    FuzzExceptBadOptions,
    FuzzExceptBadFile,
)
from os.path import isfile
from .facade import (
    Facade,
    ERROR_CODE,
)

from .factories.fuzzresfactory import resfactory
from .factories.dictfactory import dictionary_factory
from .fuzzobjects import FuzzStats, FuzzResult
from .filters.ppfilter import FuzzResFilter
from .filters.simplefilter import FuzzResSimpleFilter
from .helpers.str_func import json_minify
from . import __version__ as version

from .core import Fuzzer
from .myhttp import HttpPool

from .externals.reqresp.cache import HttpCache

from collections import defaultdict, UserDict

from .printers import JSON, BasePrinter
import json

# The priority moves in steps of 10 to allow a buffer zone for future finegrained control. This way, one group of
# requests (such as within a seed) has leverage over queuing with less prio than the other requests while being
# prioritized higher than the next group of requests (e.g. the next seed)
PRIORITY_STEP = 10


class FuzzSession(UserDict):
    def __init__(self, parsed_args=None):
        self.url: Optional[str] = None
        self.wordlist_list: list[list[str]] = []
        self.colorless: Optional[bool] = None
        self.quiet: Optional[bool] = None
        self.noninteractive: Optional[bool] = None
        self.verbose: Optional[bool] = None
        self.output: Optional[str] = None
        self.debug_log: Optional[str] = None
        self.proxy_list: list[list[str]] = []
        self.threads: Optional[int] = None
        self.sleep: Optional[int] = None
        self.location: Optional[bool] = None
        self.recursion: Optional[int] = None
        self.plugin_recursion: Optional[int] = None
        self.method: Optional[str] = None
        self.poooost_data: Optional[str] = None
        self.header_dict: dict = {}
        self.cookie: Optional[str] = None
        self.stop_error: Optional[bool] = None
        self.hc_list: list[list[str]] = []
        self.hl_list: list[list[str]] = []
        self.hw_list: list[list[str]] = []
        self.hs_list: list[list[str]] = []
        self.hr: Optional[str] = None
        self.sc_list: list[list[str]] = []
        self.sl_list: list[list[str]] = []
        self.sw_list: list[list[str]] = []
        self.ss_list: list[list[str]] = []
        self.sr: Optional[str] = None
        self.filter: Optional[str] = None
        self.pre_filter: Optional[str] = None
        self.hard_filter: Optional[bool] = None
        self.auto_filter: Optional[bool] = None
        self.dump_config: Optional[str] = None
        self.config: Optional[str] = None
        self.dry_run: Optional[bool] = None
        self.limit_requests: Optional[int] = None
        self.ip: Optional[str] = None
        self.request_timeout: Optional[int] = None
        self.domain_scope: Optional[bool] = None
        self.plugins_list: list[list[str]] = []
        self.iterator: Optional[str] = None
        self.version: Optional[bool] = None
        #TODO this if statement is only temporary, will be necessary soon enough
        if parsed_args:
            self.validate_args(parsed_args)

        self.compiled_stats: Optional[FuzzStats] = None
        self.compiled_filter: Optional[FuzzResFilter] = None
        self.compiled_simple_filter: Optional[FuzzResSimpleFilter] = None
        self.compiled_seed: Optional[FuzzResult] = None
        self.compiled_printer: Optional[BasePrinter] = None

        self.data: dict = self._defaults()
        self.keys_not_to_dump = [
            "recipe",
            "seed_payload",
            "compiled_seed",
            "compiled_stats",
            "compiled_dictio",
            "compiled_simple_filter",
            "compiled_filter",
            "compiled_prefilter",
            "compiled_printer",
            "description",
            "transport",
        ]

        ## recipe must be superseded by options
        #if "recipe" in kwargs and kwargs["recipe"]:
        #    for recipe in kwargs["recipe"]:
        #        self.import_from_file(recipe)

        #self.update(kwargs)

        self.cache: HttpCache = HttpCache()
        self.http_pool: Optional[HttpPool] = None

        #TODO Unused?
        self.stats = FuzzStats()

    def validate_args(self, parsed_args):
        """Checks all options for their validity, parses and assigns them to the FuzzSession object"""

        if parsed_args.version:
            print(f"wenum version: {version}")
            sys.exit(0)

        if parsed_args.url is None:
            raise FuzzExceptBadOptions("Specify the URL either with -u")
        self.url = parsed_args.url

        if not parsed_args.wordlist:
            raise FuzzExceptBadOptions("Bad usage: You must specify a payload.")
        for wordlist_args in parsed_args.wordlist:
            for wordlist in wordlist_args:
                if not isfile(wordlist):
                    raise FuzzExceptBadFile(f"Wordlist {wordlist} could not be found.")
                self.wordlist_list.append(wordlist)

        self.colorless = parsed_args.colorless

        self.quiet = parsed_args.quiet

        self.noninteractive = parsed_args.noninteractive

        self.verbose = parsed_args.verbose

        self.output = parsed_args.output

        if parsed_args.debug_log:
            logger = logging.getLogger("runtime_log")
            logger.propagate = False
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%d.%m.%Y %H:%M:%S")
            handler = logging.FileHandler(filename=parsed_args.debug_log)
            handler.setLevel(logging.DEBUG)
            logger.handlers.clear()
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        self.debug_log = parsed_args.debug_log

        if parsed_args.proxy:
            for proxy_args in parsed_args.proxy:
                for proxy in proxy_args:
                    parsed_proxy = urlparse(proxy)
                    if parsed_proxy.scheme.lower() not in ["socks4", "socks5", "http"]:
                        raise FuzzExceptBadOptions("The supplied proxy protocol is not supported. Please use SOCKS4, SOCKS5, "
                                                   "or HTTP.")
                    if ":" not in parsed_proxy.netloc:
                        raise FuzzExceptBadOptions("Please supply the port that should be used for the proxy.")
                    split_netloc = parsed_proxy.netloc.split(":")
                    if not len(split_netloc) == 2:
                        raise FuzzExceptBadOptions("Please ensure that the proxy string contains exactly one colon.")
                    try:
                        int(split_netloc[1])
                    except ValueError:
                        raise FuzzExceptBadOptions("Please ensure that the proxy string's port is numeric.")
                    self.proxy_list.append(proxy)

        if parsed_args.threads < 0:
            raise FuzzExceptBadOptions("Threads can not be a negative number.")
        self.threads = parsed_args.threads

        if parsed_args.sleep < 0:
            raise FuzzExceptBadOptions("Can not sleep for a negative time.")
        self.sleep = parsed_args.sleep

        self.location = parsed_args.location

        if parsed_args.recursion < 0 or parsed_args.plugin_recursion < 0:
            raise FuzzExceptBadOptions("Can not set a negative recursion limit.")
        self.recursion = parsed_args.recursion
        if not parsed_args.plugin_recursion:
            self.plugin_recursion = self.recursion
        else:
            self.plugin_recursion = parsed_args.plugin_recursion

        self.method = parsed_args.method

        self.poooost_data = parsed_args.data

        if parsed_args.header:
            for header_args in parsed_args.header:
                for header in header_args:
                    split_header = header.split(":", maxsplit=1)
                    if len(split_header) != 2:
                        raise FuzzExceptBadOptions("Please provide the header in the format 'name: value'")
                    self.header_dict[split_header[0]] = split_header[1]

        self.stop_error = parsed_args.stop_error

        if ((parsed_args.hw or parsed_args.hc or parsed_args.hl or parsed_args.hs or parsed_args.hr) and
                (parsed_args.sw or parsed_args.sc or parsed_args.sl or parsed_args.ss or parsed_args.sr)):
            raise FuzzExceptBadOptions("Bad usage: Hide and show flags are mutually exclusive.")

        if parsed_args.hc:
            for hc_args in parsed_args.hc:
                for hc in hc_args:
                    self.hc_list.append(hc)

        if parsed_args.hw:
            for hw_args in parsed_args.hw:
                for hw in hw_args:
                    self.hw_list.append(hw)

        if parsed_args.hl:
            for hl_args in parsed_args.hl:
                for hl in hl_args:
                    self.hl_list.append(hl)

        if parsed_args.hs:
            for hs_args in parsed_args.hs:
                for hs in hs_args:
                    self.hs_list.append(hs)

        self.hr = parsed_args.hr

        if parsed_args.sc:
            for sc_args in parsed_args.sc:
                for sc in sc_args:
                    self.sc_list.append(sc)

        if parsed_args.sw:
            for sw_args in parsed_args.sw:
                for sw in sw_args:
                    self.sw_list.append(sw)

        if parsed_args.sl:
            for sl_args in parsed_args.sl:
                for sl in sl_args:
                    self.sl_list.append(sl)

        if parsed_args.ss:
            for ss_args in parsed_args.ss:
                for ss in ss_args:
                    self.ss_list.append(ss)

        self.sr = parsed_args.sr

        self.filter = parsed_args.filter

        self.hard_filter = parsed_args.hard_filter

        self.auto_filter = parsed_args.auto_filter

        self.dump_config = parsed_args.dump_config

        self.dry_run = parsed_args.dry_run

        self.limit_requests = parsed_args.limit_requests

        if parsed_args.ip:
            parsed_ip = urlparse(parsed_args.ip)
            split_netloc = parsed_ip.netloc.split(":")
            if ":" not in parsed_ip.netloc:
                self.ip = parsed_ip.netloc + ":80"
            elif len(split_netloc) == 2:
                try:
                    int(split_netloc[1])
                    self.ip = parsed_ip.netloc
                except ValueError:
                    raise FuzzExceptBadOptions("Please ensure that the port of the --ip argument is numeric.")
            else:
                raise FuzzExceptBadOptions("Please ensure that the --ip argument string contains one colon.")

        self.request_timeout = parsed_args.request_timeout

        self.domain_scope = parsed_args.domain_scope

        self.plugins_list = parsed_args.plugins

        if len(self.wordlist_list) == 1 and parsed_args.iterator:
            raise FuzzExceptBadOptions("Several dictionaries must be used when specifying an iterator.")
        self.iterator = parsed_args.iterator

        if not self.wordlist_list:
            raise FuzzExceptBadOptions("At least one wordlist needs to be specified.")

        if not self.url:
            raise FuzzExceptBadOptions("A target URL needs to be specified.")

        if self.plugins_list and self.dry_run:
            raise FuzzExceptBadOptions(
                "Bad usage: Plugins cannot work without making any HTTP request."
            )

        #if "FUZZ" not in [self.url, self.header_dict, self.cookie, self.method, self.poooost_data]:
        #    raise FuzzExceptBadOptions("No FUZZ keyword has been supplied.")

        if self.dump_config:
            self.export_to_file(self.dump_config)
            print(f"Recipe written into {self.dump_config}.")
            sys.exit(0)

    @staticmethod
    def _defaults():
        return dict(
            hs=None,
            hc=[],
            hw=[],
            hl=[],
            hh=[],
            ss=None,
            sc=[],
            sw=[],
            sl=[],
            sh=[],
            payloads=None,
            limitrequests=False,
            LIMITREQUESTS_THRESHOLD=20000,
            auto_filter=False,
            follow_redirects=False,
            iterator=None,
            printer=(None, None),
            color=True,
            verbose=False,
            interactive=False,
            hard_filter=False,
            transport="http/s",
            recipe=[],
            proxies=None,
            conn_delay=int(Facade().settings.get("connection", "conn_delay")),
            req_delay=int(Facade().settings.get("connection", "req_delay")),
            retries=int(Facade().settings.get("connection", "retries")),
            rlevel=0,
            plugin_rlevel=0,
            scanmode=True,
            delay=None,
            concurrent=int(Facade().settings.get("connection", "concurrent")),
            url="",
            domain_scope=False,
            method=None,
            auth={},
            postdata=None,
            headers=[],
            cookie=[],
            script="",
            script_args={},
            connect_to_ip=None,
            # Session keeps track of current prio level to be assigned to requests.
            # Useful to poll which prio level the next seed should receive, and increase by that amount
            current_priority_level=PRIORITY_STEP,
            # this is equivalent to payloads but in a different format
            dictio=None,
            # these will be compiled
            seed_payload=False,
            filter="",
            prefilter=[],
            compiled_filter=None,
            compiled_prefilter=[],
            compiled_printer=None,
            compiled_seed=None,
            compiled_stats=None,
            compiled_dictio=None,
            runtime_log=None,)

    def update(self, options):
        self.data.update(options)

    def export_to_file(self, filename):
        """
        Probably broken, needs to be fixed to be functional
        """
        try:
            with open(filename, "w") as f:
                json_options = json.dumps(self.export_active_options_dict(), sort_keys=True)
                f.write(json_options)
        except IOError:
            raise FuzzExceptBadFile("Error writing recipe file.")

    def import_from_file(self, filename):
        try:
            with open(filename, "r") as file:
                self.import_json(file.read())
        except IOError:
            raise FuzzExceptBadFile("Error loading recipe file {}.".format(filename))
        except json.decoder.JSONDecodeError as e:
            raise FuzzExceptBadRecipe(
                "Incorrect JSON recipe {} format: {}".format(filename, str(e))
            )

    def assign_next_priority_level(self):
        """
        Pulls current priority level, increases it and returns the value. Useful for assigning new level
        to new recursions
        """
        self.data["current_priority_level"] += PRIORITY_STEP
        return self.data["current_priority_level"]

    def import_json(self, data):
        """
        Load options stored as JSON into memory
        """
        json_data = json.loads(json_minify(data))

        try:
            if "wenum_recipe" in json_data and json_data["wenum_recipe"]["recipe_version"] == "0.3":
                for key, value in json_data["wenum_recipe"].items():
                    if key not in self.keys_not_to_dump:
                        if key in self.data and isinstance(self.data[key], list):
                            self.data[key] += value
                        else:
                            self.data[key] = value
            else:
                raise FuzzExceptBadRecipe("Unsupported recipe version.")
        except KeyError:
            raise FuzzExceptBadRecipe("Incorrect recipe format.")

    def export_active_options_dict(self) -> dict:
        """
        Returns active options as a dictionary
        """
        active_options_dict = dict(wenum_recipe=defaultdict(dict))
        defaults = self._defaults()

        for key, value in self.data.items():
            # Only dump the non-default options
            if key not in self.keys_not_to_dump and value != defaults[key]:
                active_options_dict["wenum_recipe"][key] = self.data[key]
        active_options_dict["wenum_recipe"]["recipe_version"] = "0.3"

        return active_options_dict

    def fuzz(self, **kwargs):
        """Method used by the API"""
        self.data.update(kwargs)

        fz = None
        try:
            fz = Fuzzer(self.compile())

            for f in fz:
                yield f

        finally:
            if fz:
                fz.cancel_job()
                self.stats.update(self.compiled_stats)

            if self.http_pool:
                self.http_pool.deregister()
                self.http_pool = None

    def __enter__(self):
        self.http_pool = HttpPool(self)
        self.http_pool.register()
        return self

    def __exit__(self, *args):
        self.close()

    def get_fuzz_words(self) -> set:
        fuzz_words = self.compiled_filter.get_fuzz_words()

        if self.compiled_seed:
            fuzz_words += self.compiled_seed.payload_man.get_fuzz_words()

        return set(fuzz_words)

    def compile_dictio(self):
        self.data["compiled_dictio"] = dictionary_factory.create(
            "dictio_from_options", self
        )
        for i in range(10):
            print(self.data["compiled_dictio"])

    def compile_seeds(self):
        self.compiled_seed = resfactory.create("seed_from_options", self)

    def compile(self):
        """
        Sets some things before actually running
        """

        if self.output:
            self.compiled_printer = JSON(self.output, self.verbose)

        self.compile_seeds()
        self.compile_dictio()

        # filter options
        self.compiled_simple_filter = FuzzResSimpleFilter.from_options(self)
        self.compiled_filter = FuzzResFilter(self.filter)

        self.compiled_stats = FuzzStats.from_options(self)

        # Check payload num
        fuzz_words = self.get_fuzz_words()

        if self.data["compiled_dictio"].width() != len(fuzz_words):
            raise FuzzExceptBadOptions("FUZZ words and number of payloads do not match!")

        if not self.http_pool:
            self.http_pool = HttpPool(self)
            self.http_pool.register()

        return self

    def close(self):
        if self.data["compiled_dictio"]:
            self.data["compiled_dictio"].cleanup()

        if self.http_pool:
            self.http_pool.deregister()
            self.http_pool = None
