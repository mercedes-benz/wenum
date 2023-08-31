import argparse
import logging
import sys
from os.path import isfile
from typing import Optional
from urllib.parse import urlparse
from wenum import __version__ as version

from tomlkit import document, dumps, comment

from wenum.exception import FuzzExceptBadOptions, FuzzExceptBadFile


class Options:
    """
    Class responsible for the user options
    """
    def __init__(self):
        self.url: Optional[str] = None
        self.wordlist_list: list[str] = []
        self.colorless: Optional[bool] = None
        self.quiet: Optional[bool] = None
        self.noninteractive: Optional[bool] = None
        self.verbose: Optional[bool] = None
        self.output: Optional[str] = None
        self.debug_log: Optional[str] = None
        self.proxy_list: list[str] = []
        self.threads: Optional[int] = None
        self.sleep: Optional[int] = None
        self.location: Optional[bool] = None
        self.recursion: Optional[int] = None
        self.plugin_recursion: Optional[int] = None
        self.method: Optional[str] = None
        self.data: Optional[str] = None
        self.header_dict: dict = {}
        self.cookie: Optional[str] = None
        self.stop_error: Optional[bool] = None
        self.hc_list: list[str] = []
        self.hl_list: list[str] = []
        self.hw_list: list[str] = []
        self.hs_list: list[str] = []
        self.hr: Optional[str] = None
        self.sc_list: list[str] = []
        self.sl_list: list[str] = []
        self.sw_list: list[str] = []
        self.ss_list: list[str] = []
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
        self.plugins_list: list[str] = []
        self.iterator: Optional[str] = None
        self.version: Optional[bool] = None

    def read_args(self):
        """Checks all options for their validity, parses and assigns them to the FuzzSession object"""
        #TODO Remove default values from argparse, and rather set them here if neither the config file nor argparse contained a value. Also do the option validation after reading in all the args, because only then is it possible to have
        #TODO a full look at what came in both from the config and command line.

        parsed_args = parse_args()

        self.check_config()

        self.url = parsed_args.url

        for wordlist_args in parsed_args.wordlist:
            for wordlist in wordlist_args:
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

        self.data = parsed_args.data

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

        if self.dump_config:
            self.export_config()
            print(f"Config written into {self.dump_config}.")
            sys.exit(0)

    def create_default_config(self):
        """
        Creates default files if they don't exist yet
        """
        #TODO Create ~/.config/wenum, create config.toml with comment explaining the structure, create ~/.config/wenum/plugins/
        pass

    def export_config(self):
        """
        Exports the configuration specified in the CLI into a TOML file.
        All TOML keys are named according to their corresponding command line option names.
        The TOML file also is formatted without any table, as it can be confusing to the user trying to find out
        which table the option belongs to.
        """
        doc = document()
        doc.add(comment("""All keys are named equal to the command line options. 
        If you are unsure about the syntax of an option,
        you can use the command line option to export the specified options to a config file 
        and use it as a reference."""))
        doc.add("url", self.url)
        doc.add("wordlist", self.wordlist_list)
        doc.add("colorless", self.colorless)
        doc.add("quiet", self.quiet)
        doc.add("noninteractive", self.noninteractive)
        doc.add("verbose", self.verbose)
        doc.add("output", self.output)
        doc.add("debug-log", self.debug_log)
        doc.add("proxy", self.proxy_list)
        doc.add("threads", self.threads)
        doc.add("sleep", self.sleep)
        doc.add("location", self.location)
        doc.add("recursion", self.recursion)
        doc.add("plugin-recursion", self.plugin_recursion)
        doc.add("method", self.method)
        doc.add("data", self.data)
        doc.add("header", self.header_dict)
        doc.add("cookie", self.cookie)
        doc.add("stop-error", self.stop_error)
        doc.add("hc", self.hc_list)
        doc.add("hw", self.hw_list)
        doc.add("hl", self.hl_list)
        doc.add("hs", self.hs_list)
        doc.add("hr", self.hr)
        doc.add("sc", self.sc_list)
        doc.add("sw", self.sw_list)
        doc.add("sl", self.sl_list)
        doc.add("ss", self.ss_list)
        doc.add("sr", self.sr)
        doc.add("filter", self.filter)
        doc.add("auto-filter", self.auto_filter)
        doc.add("hard-filter", self.hard_filter)
        doc.add("dry-run", self.dry_run)
        doc.add("limit-requests", self.limit_requests)
        doc.add("ip", self.ip)
        doc.add("request-timeout", self.request_timeout)
        doc.add("domain-scope", self.domain_scope)
        doc.add("plugins", self.plugins_list)
        doc.add("iterator", self.iterator)
        doc.add("version", self.version)
        with open(self.dump_config, "w") as file:
            file.writelines(dumps(doc))

    def import_config(self, config_path: str):
        """
        Imports the config with the given path.
        """
        pass

    def check_config(self):
        """
        Checks for possible config locations and imports if any are valid. Looks in $XDG_HOME by default.
        If supplied, reads from --config flag's file instead.
        """
        pass

    def basic_validate(self):
        """
        Check for the initially set opts. Raises exception on faulty states.
        """
        if self.version:
            print(f"wenum version: {version}")
            sys.exit(0)

        if self.url is None:
            raise FuzzExceptBadOptions("Specify the URL either with -u")

        if not self.wordlist_list:
            raise FuzzExceptBadOptions("Bad usage: You must specify a wordlist.")

        for wordlist in self.wordlist_list:
            if not isfile(wordlist):
                raise FuzzExceptBadFile(f"Wordlist {wordlist} could not be found.")


def parse_args() -> argparse.Namespace:
    """Define all options. No defaults should be set here, as the config file should take precedence as long as the user
    does not by their own will specify a value in the command line options."""
    parser = argparse.ArgumentParser(prog="wenum",
                                     description="A Web Fuzzer. The options follow the curl schema where possible.",
                                     epilog="Examples")
    request_building_group = parser.add_argument_group("Request building options")
    request_proessing_group = parser.add_argument_group("Request processing options")
    request_building_group.add_argument("-u", "--url", help="Specify a URL for the request.")
    # argparse offers a way of directly reading in a file, but that feature seems unstable
    # (file handle supposedly kept open for the entire runtime?) - see https://bugs.python.org/issue13824
    # Unsure if should be used, therefore simply reading in a string and manually checking instead
    io_group = parser.add_argument_group("Input/Output options")
    io_group.add_argument("-w", "--wordlist", action="append", help="Specify a wordlist file.", nargs="*")
    cli_group = parser.add_argument_group("CLI options")
    cli_group.add_argument("-c", "--colorless", action="store_true", help="Disable colors in CLI output.")
    cli_group.add_argument("-q", "--quiet", action="store_true", help="Disable progress messages in CLI output.")
    cli_group.add_argument("-n", "--noninteractive", action="store_true",
                        help="Disable runtime interactions.")
    cli_group.add_argument("-v", "--verbose", action="store_true", help="Enable verbose information in CLI output.")
    io_group.add_argument("-o", "--output", help="Store results in the specified output file as JSON.")
    # io_group.add_argument("-f", "--output-format", help="Set the format of the output file. Note: Currently only json, html will come.", choices=["json", "html", "all"], default="json")#TODO Check and reimplement html output
    io_group.add_argument("-l", "--debug-log", help="Save runtime information to a file.")
    request_building_group.add_argument("-p", "--proxy", action="append", help="Proxy requests. Use format 'protocol://ip:port'. "
                                                               "Protocols SOCKS4, SOCKS5 and HTTP are supported. If "
                                                               "supplied multiple"
                                                               "times, the requests will be split between all "
                                                               "supplied proxies.")
    # request_building_group.add_argument("-P", "--replay-proxy", help="Send requests that were not filtered through the specified proxy. Format and conditions match -p.")#TODO implement
    request_proessing_group.add_argument("-t", "--threads", type=int,
                        help="Modify the number of concurrent \"threads\"/connections for requests (default: 40)", default=40)
    # request_processing_group.add_argument("--plugin-executors", type=int, help="Modify the amount of threads used for concurrent execution of plugins.", default=3)#TODO implement
    request_proessing_group.add_argument("-s", "--sleep", type=float, help="Wait supplied seconds between requests.", default=0)
    request_proessing_group.add_argument("-L", "--location", action="store_true",
                        help="Follow redirections by sending an additional request to the redirection URL.")
    request_proessing_group.add_argument("-R", "--recursion", type=int,
                        help="Enable recursive path discovery by specifying a maximum depth.", default=0)
    request_proessing_group.add_argument("-r", "--plugin-recursion", type=int,
                        help="Adjust the max depth for recursions originating from plugins. "
                             "Matches --recursion by default.",
                        default=0)
    request_building_group.add_argument("-X", "--method", help="Change the HTTP method used for requests.", default="GET")
    request_building_group.add_argument("-d", "--data",
                        help="Use POST method with supplied data (e.g. \"id=FUZZ&catalogue=1\"). "
                             "Method can be overridden with -X.")
    request_building_group.add_argument("-H", "--header", action="append",
                        help="Add/modify a header, e.g. \"User-Agent: Changed\". Multiple flags accepted.",
                        nargs="*")  # TODO Ensure both specifying multiple args and multiple flags are supported
    request_building_group.add_argument("-b", "--cookie", help="Add cookies, e.g. \"Cookie1=foo; Cookie2=bar\".")
    # request_processing_group.add_argument("-e", "--stop-errors", action="store_true", help="Stop when 10 errors were detected")#TODO Implement
    request_proessing_group.add_argument("-E", "--stop-error", action="store_true", help="Stop on any connection error.")

    filter_group = parser.add_argument_group("Filter options")
    filter_group.add_argument("--hc", action="append",
                        help="Hide responses matching the supplied codes (e.g. --hc 302 404 405).", nargs="*",
                        type=int)  # TODO do these last as the custom Parser doesnt allow several args for one flag
    filter_group.add_argument("--hl", action="append", help="Hide responses matching the supplied lines.",
                        nargs="*", type=int)
    filter_group.add_argument("--hw", action="append", help="Hide responses matching the supplied words.",
                        nargs="*", type=int)
    filter_group.add_argument("--hs", action="append",
                        help="Hide responses matching the supplied sizes/chars.", nargs="*", type=int)
    filter_group.add_argument("--hr", help="Hide responses matching the supplied regex.")
    filter_group.add_argument("--sc", action="append", help="Show responses matching the supplied codes.",
                        nargs="*", type=int)
    filter_group.add_argument("--sl", action="append", help="Show responses matching the supplied lines.",
                        nargs="*", type=int)
    filter_group.add_argument("--sw", action="append", help="Show responses matching the supplied words.",
                        nargs="*", type=int)
    filter_group.add_argument("--ss", action="append",
                        help="Show responses matching the supplied sizes/chars.", nargs="*", type=int)
    filter_group.add_argument("--sr", help="Show responses matching the supplied regex.")
    filter_group.add_argument("--filter", help="Show/hide responses using the supplied regex.")
    # parser.add_argument("--pre-filter", help="Filter items before fuzzing using the specified expression. Repeat for concatenating filters.")#TODO Current prefilter function is not what we want it to be. We want to provide a means to block sending requests that contain a specific request, e.g. because dynamically generated by plugins.
    # parser.add_argument("--filter-help", action="store_true", help="Show the filter language specification.")#TODO May be phased out with the generic info option, currently broken
    filter_group.add_argument("--hard-filter", action="store_true",
                        help="Don't only hide the responses, but also prevent post processing of them (e.g. sending "
                             "to plugins).")
    filter_group.add_argument("--auto-filter", action="store_true",
                        help="Filter automatically during runtime. If a response occurs too often, it will get "
                             "filtered out.")
    io_group.add_argument("--dump-config", help="Print all supplied options to a config file and exit.")
    io_group.add_argument("-K", "--config", help="Read config from specified path. By default read from XDG_CONFIG_HOME ~/.config/wenum/wenum-config.toml")#TODO implement
    # io_group.add_argument("--recipe", help="Reads options from a config. Repeat for various recipes.") #TODO Remove repetition option. Fuse --config and make config toml format
    # io_group.add_argument("--cache-file", help="Read in a cache file from a previous run, and post process the results without sending the requests.")#TODO implement
    request_proessing_group.add_argument("--dry-run", action="store_true", help="Test run without actually making any HTTP request.")
    request_proessing_group.add_argument("--limit-requests", type=int,
                        help="Limit recursions. Once specified amount of requests are sent, recursions will be "
                             "deactivated",
                        default=0)
    request_building_group.add_argument("--ip",
                        help="Specify an IP to connect to. Format ip:port. Uses port 80 if none specified. "
                             "This can help if you want to force connecting to a specific IP and still present a "
                             "host name in the SNI, which will remain the URL's host.")  # TODO Change from --ip to --sni, which allows for same featureset and feels less convoluted next to --url
    request_proessing_group.add_argument("--request-timeout", type=int,
                        help="Change the maximum seconds the request is allowed to take.", default=20)
    request_proessing_group.add_argument("--domain-scope", action="store_true",
                        help="Base the scope check on the domain name instead of IP.")
    # parser.add_argument("--list-plugins", help="List all plugins and categories")#TODO implement, though maybe this falls off with the info option
    io_group.add_argument("--plugins", action="append",
                        help="Plugins to be run, supplied as a list of plugin-files or plugin-categories",
                        nargs="*")
    # parser.add_argument("--plugin-args", help="Provide arguments to scripts. e.g. --plugin-args grep.regex=\"<A href=\\\"(.*?)\\\">\"", nargs="*")#TODO Maybe remove? Really no plugin utilizes this except for regex.py, and I dont know if they ever will
    request_building_group.add_argument("-i", "--iterator", help="Set the iterator used when combining multiple wordlists (default: product).",
                        choices=["product", "zip", "chain"])
    # parser.add_argument("info", help="Print information about the specified topic and exit.", choices=["plugins", "iterators", "filter"])#TODO implement, and this feels like a good positional argument. Probably because by design the user should not use it in combination with anything else
    parser.add_argument("-V", "--version", action="store_true", help="Print version and exit.")
    return parser.parse_args()
