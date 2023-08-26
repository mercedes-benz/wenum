import logging
import re
import sys
import getopt
import warnings
from collections import defaultdict

from wenum.helpers.file_func import get_filter_help_file
from wenum.facade import Facade
from wenum.options import FuzzSession
from wenum.exception import FuzzException, FuzzExceptBadOptions
from .common import help_banner, exec_banner
from .common import usage
from .common import brief_usage
from .common import verbose_usage
from wenum import __version__ as version
from .output import table_print
import argparse

short_opts = "hLAFZX:vcab:e:R:D:d:l:z:i:r:o:t:w:H:m:o:s:p:n:q:w:u"
long_opts = [
    "ee=",
    "zE=",
    "zD=",
    "ip=",
    "filter-help",
    "recipe=",
    "dump-config=",
    "req-delay=",
    "conn-delay=",
    "sc=",
    "sh=",
    "sl=",
    "sw=",
    "ss=",
    "hc=",
    "hh=",
    "hl=",
    "hw=",
    "hs=",
    "script-help=",
    "plugins=",
    "script-args=",
    "prefilter=",
    "filter=",
    "interact",
    "hard-filter",
    "auto-filter",
    "debug-log",
    "help",
    "version",
    "dry-run",
    "limit-requests"
]
REPEATABLE_OPTS = [
    "--prefilter",
    "--recipe",
    "-w",
    "-b",
    "-H",
    "-p",
]


def parse_args():
    """Define all options"""
    parser = argparse.ArgumentParser(prog="wenum", description="A Web Fuzzer. The options follow the curl schema where possible.", epilog="Examples")
    parser.add_argument("-u", "--url", help="Specify a URL for the request.")
    # argparse offers a way of directly reading in a file, but that feature seems unstable
    # (file handle supposedly kept open for the entire runtime?) - see https://bugs.python.org/issue13824
    # Therefore simply reading in a string and manually checking instead
    parser.add_argument("-w", "--wordlist", action="append", help="Specify a wordlist file.")
    parser.add_argument("-c", "--colorless", action="store_true", help="Disable colours in CLI output.")
    parser.add_argument("-q", "--quiet", action="store_true", help="Disable progress messages in CLI output.")
    parser.add_argument("-n", "--noninteractive", action="store_true",
                        help="Disable runtime interactions.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose information in CLI output.")
    parser.add_argument("-o", "--output", help="Store results in the specified output file.")
    #parser.add_argument("-f", "--output-format", help="Set the format of the output file. Note: Currently only json, html will come.", choices=["json", "html", "all"], default="json")#TODO Check and reimplement html output
    parser.add_argument("-l", "--debug-log", help="Save runtime information to a file.")
    parser.add_argument("-p", "--proxy", action="append", help="Proxy requests. Use format 'protocol://ip:port'. "
                                              "Protocols SOCKS4, SOCKS5 and HTTP are supported. If supplied multiple "
                                              "times, the requests will be split between all supplied proxies.")
    #parser.add_argument("-P", "--replay-proxy", help="Send requests that were not filtered through the specified proxy. Format and conditions match -p.")#TODO implement
    parser.add_argument("-t", "--threads", type=int, help="Modify the number of concurrent \"threads\",/connections for requests", default=40)
    #parser.add_argument("--plugin-executors", type=int, help="Modify the amount of threads used for concurrent execution of plugins.", default=3)#TODO implement
    parser.add_argument("-s", "--sleep", type=float, help="Wait supplied seconds between requests.", default=0)
    parser.add_argument("-L", "--location", action="store_true", help="Follow redirections by sending an additional request to the redirection URL.")
    parser.add_argument("-R", "--recursion", type=int, help="Enable recursive path discovery by specifying a maximum depth.", default=0)
    parser.add_argument("-r", "--plugin-recursion", type=int, help="Adjust the max depth for recursions originating from plugins. Matches --recursion by default.")
    #parser.add_argument("-K", "--config", help="Read config from specified path. By default read from XDG_CONFIG_HOME ~/.config/wenum/wenum-config.toml")#TODO implement
    parser.add_argument("-X", "--method", help="Change the HTTP method used for requests.", default="GET")
    parser.add_argument("-d", "--data", help="Use POST method with supplied data (e.g. \"id=FUZZ&catalogue=1\"). Method can be overridden with -X.")
    parser.add_argument("-H", "--header", help="Add/modify a header, e.g. \"User-Agent: Changed\". Multiple flags accepted.")
    parser.add_argument("-b", "--cookie", help="Add cookies, e.g. \"Cookie1=abc; Cookie2=def\".")
    #parser.add_argument("-e", "--stop-errors", action="store_true", help="Stop when 10 errors were detected")#TODO Implement
    parser.add_argument("-E", "--stop-error", action="store_true", help="Stop on any connection error.")
    parser.add_argument("--hc", help="Hide responses matching the supplied comma-separated codes.")
    parser.add_argument("--hl", help="Hide responses matching the supplied comma-separated lines.")
    parser.add_argument("--hw", help="Hide responses matching the supplied comma-separated words.")
    parser.add_argument("--hs", help="Hide responses matching the supplied comma-separated sizes/chars.")
    parser.add_argument("--hr", help="Hide responses matching the supplied regex.")
    parser.add_argument("--sc", help="Show responses matching the supplied comma-separated codes.")
    parser.add_argument("--sl", help="Show responses matching the supplied comma-separated lines.")
    parser.add_argument("--sw", help="Show responses matching the supplied comma-separated words.")
    parser.add_argument("--ss", help="Show responses matching the supplied comma-separated sizes/chars.")
    parser.add_argument("--sr", help="Show responses matching the supplied regex.")
    parser.add_argument("--filter", help="Show/hide responses using the supplied regex.")
    parser.add_argument("--pre-filter", help="Filter items before fuzzing using the specified expression. Repeat for concatenating filters.")#TODO Remove repetition, unnecessary complexity?
    #parser.add_argument("--filter-help", action="store_true", help="Show the filter language specification.")#TODO May be phased out with the generic info option, currently broken
    parser.add_argument("--hard-filter", action="store_true", help="Don't only hide the responses, but also prevent post processing of them (e.g. sending to plugins).")
    parser.add_argument("--auto-filter", action="store_true", help="Filter automatically during runtime. If a response occurs too often, it will get filtered out.")
    parser.add_argument("--dump-config", help="Print specified options to file that can later be imported.")
    parser.add_argument("--recipe", help="Reads options from a config. Repeat for various recipes.") #TODO Remove repetition option. Fuse --config and make config toml format
    #parser.add_argument("--cache-file", help="Read in a cache file from a previous run, and post process the results without sending the requests.")#TODO implement
    parser.add_argument("--dry-run", help="Test run without actually making any HTTP request.")
    parser.add_argument("--limit-requests", type=int, help="Limit recursions. Once specified amount of requests are sent, recursions will be deactivated", default=0)
    parser.add_argument("--ip", help="Specify an IP to connect to. Format ip:port. This can help if you want to force connecting to a specific IP and still present a host name in the SNI, which will remain the URL's host.")#TODO Change from --ip to --sni, which allows for same featureset and feels less convoluted next to --url
    parser.add_argument("--request‐timeout", type=int, help="Change the maximum seconds the request is allowed to take.", default=20)
    parser.add_argument("--domain-scope", action="store_true", help="Base the scope check on the domain name instead of IP.")
    #parser.add_argument("--list-plugins", help="List all plugins and categories")#TODO implement, though maybe this falls off with the info option
    parser.add_argument("--plugins", help="Plugins to be run as a comma separated list of plugin-files or plugin-categories")#TODO add nargs and in future handle that way instead of comma separation. Maybe same with other options with multiple args?
    parser.add_argument("--plugin-args", help="Provide arguments to scripts. e.g. --plugin-args grep.regex=\"<A href=\\\"(.*?)\\\">\"")#TODO Maybe remove? Really no plugin utilizes this except for regex.py, and I dont know if they ever will
    parser.add_argument("-i", "--iterator", help="Modify the iterator used for combining wordlists.", default="product", choices=["product", "zip", "chain"])
    #parser.add_argument("--info", help="Print information about the specified topic and exit.", choices=["plugins", "iterators", "filter"])#TODO implement, and this feels like a good positional argument. Why?
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    return parser.parse_args()


class CLParser:
    def __init__(self,
                 argv,
                 short_opts=short_opts,
                 long_opts=long_opts,
                 help_banner=help_banner,
                 brief_usage=brief_usage,
                 verbose_usage=verbose_usage,
                 usage=usage,):
        self.argv = argv
        self.short_opts = short_opts
        self.long_opts = long_opts
        self.help_banner = help_banner
        self.brief_usage = brief_usage
        self.verbose_usage = verbose_usage
        self.usage = usage

    def show_brief_usage(self):
        print(self.help_banner)
        print(self.brief_usage)

    def show_verbose_usage(self):
        print(self.help_banner)
        print(self.verbose_usage)

    def show_usage(self):
        print(self.help_banner)
        print(self.usage)

    @staticmethod
    def show_plugins_help(registrant, cols=3, category="$all$"):
        print("\nAvailable %s:\n" % registrant)
        table_print(
            [x[cols:] for x in Facade().proxy(registrant).get_plugins_ext(category)]
        )
        sys.exit(0)

    @staticmethod
    def show_plugins_names(registrant):
        print("\n".join(Facade().proxy(registrant).get_plugins_names("$all$")))

    @staticmethod
    def show_plugin_ext_help(registrant, category="$all$"):
        for plugin in Facade().proxy(registrant).get_plugins(category):
            print("Name: %s %s" % (plugin.name, plugin.version))
            print("Categories: %s" % ",".join(plugin.category))
            print("Summary: %s" % plugin.summary)
            print("Author: %s" % ",".join(plugin.author))
            print("Description:")
            for desc_lines in plugin.description:
                print("   %s" % desc_lines)
            print("Parameters:")
            for name, default_value, mandatory, description in plugin.parameters:
                print(
                    "   {} {}{}: {}".format(
                        "+" if mandatory else "-",
                        name,
                        " (= %s)" % str(default_value)
                        if default_value is not None
                        else "",
                        description,
                    )
                )
            print("\n")

        sys.exit(0)

    def parse_cl(self) -> FuzzSession:
        # Usage and command line help
        print("Phewwwwwww")

        arguments = parse_args()

        try:
            opts, args = getopt.getopt(self.argv[1:], self.short_opts, self.long_opts)
            optsd = defaultdict(list)

            for option, value in opts:
                optsd[option].append(value)

            if not args and not optsd:
                self.show_brief_usage()
                sys.exit(1)

            self._parse_help_opt(optsd)

            url = None
            if len(args) == 1:
                url = args[0]
            elif len(args) > 1:
                raise FuzzExceptBadOptions("Too many arguments.")

            options = FuzzSession(arguments)

            # check command line options correctness
            self._check_options(optsd)

            ## parse options from recipe first
            #if "--recipe" in optsd:
            #    for recipe in optsd["--recipe"]:
            #        options.import_from_file(recipe)

            # command line has priority over recipe

            if "-i" in optsd:
                options["iterator"] = optsd["-i"][0]

            self._parse_options(optsd, options)
            self._parse_conn_options(optsd, options)
            self._parse_filters(optsd, options)
            self._parse_seed(url, optsd, options)
            self._parse_scripts(optsd, options)

            if "--dump-config" in optsd:
                print(exec_banner)

                for error_msg in options.validate():
                    warnings.warn("Recipe parsing error: {}".format(error_msg))

                print("")

                options.export_to_file(optsd["--dump-config"][0])
                print("Recipe written to %s." % (optsd["--dump-config"][0],))
                sys.exit(0)

            print("Phewww")
            return options
        except FuzzException as e:
            self.show_brief_usage()
            raise e
        except ValueError as e:
            self.show_brief_usage()
            raise FuzzExceptBadOptions("Incorrect options, please check help.")
        except getopt.GetoptError as qw:
            self.show_brief_usage()
            raise FuzzExceptBadOptions("%s." % str(qw))

    def _parse_help_opt(self, optsd):
        if "--version" in optsd:
            print(version)
            sys.exit(0)

        if "-h" in optsd:
            self.show_usage()
            sys.exit(0)

        if "--help" in optsd:
            self.show_verbose_usage()
            sys.exit(0)

        if "--filter-help" in optsd:
            FILTER_HELP_REGEX_EXP = (
                "Filter Language\n---------------\n\n(.*?)Filtering results"
            )
            FILTER_HELP_REGEX = re.compile(
                FILTER_HELP_REGEX_EXP, re.MULTILINE | re.DOTALL
            )

            print(FILTER_HELP_REGEX.search(get_filter_help_file()).group(1))

            sys.exit(0)

        # Extensions help
        if "--script-help" in optsd:
            script_string = optsd["--script-help"][0]
            if script_string == "":
                script_string = "$all$"

            self.show_plugin_ext_help("scripts", category=script_string)

        if "--ee" in optsd:
            if "encoders" in optsd["--ee"]:
                self.show_plugins_names("encoders")
            elif "iterators" in optsd["--ee"]:
                self.show_plugins_names("iterators")
            elif "printers" in optsd["--ee"]:
                self.show_plugins_names("printers")
            elif "scripts" in optsd["--ee"]:
                self.show_plugins_names("scripts")
            elif "files" in optsd["--ee"]:
                print("\n".join(Facade().settings.get("general", "lookup_dirs").split(",")))
            elif "registrants" in optsd["--ee"]:
                print("\n".join(Facade().get_registrants()))
            elif "options" in optsd["--ee"]:
                print(
                    "\n".join(
                        ["-{}".format(opt) for opt in self.short_opts.replace(":", "")]
                    )
                )
                print(
                    "\n".join(
                        ["--{}".format(opt.replace("=", "")) for opt in self.long_opts]
                    )
                )
            else:
                raise FuzzExceptBadOptions(
                    "Unknown category. Valid values are: payloads, encoders, iterators, printers or scripts."
                )
            sys.exit(0)

        if "-e" in optsd:
            if "encoders" in optsd["-e"]:
                self.show_plugins_help("encoders", 2)
            elif "iterators" in optsd["-e"]:
                self.show_plugins_help("iterators")
            elif "printers" in optsd["-e"]:
                self.show_plugins_help("printers")
            elif "scripts" in optsd["-e"]:
                self.show_plugins_help("scripts", 2)
            else:
                raise FuzzExceptBadOptions(
                    "Unknown category. Valid values are: payloads, encoders, iterators, printers or scripts."
                )

    @staticmethod
    def _check_options(optsd):
        # Check for repeated flags
        opt_list = [i for i in optsd if i not in REPEATABLE_OPTS and len(optsd[i]) > 1]
        if opt_list:
            raise FuzzExceptBadOptions(
                "Bad usage: Only one %s option could be specified at the same time."
                % " ".join(opt_list)
            )

    @staticmethod
    def _parse_filters(optsd, options: FuzzSession) -> None:
        """
        Populates the options with the filter parameters
        filter_params = dict(
            hs = None,
            hc = [],
            hw = [],
            hl = [],
            hh = [],
            ss = None,
            sc = [],
            sw = [],
            sl = [],
            sh = [],
            filter = "",
            prefilter = "",
            ),
        """

        if "--prefilter" in optsd:
            for prefilter_opt in optsd["--prefilter"]:
                options["prefilter"].append(prefilter_opt)

        if "--filter" in optsd:
            options["filter"] = optsd["--filter"][0]

        if "--hc" in optsd:
            options["hc"] = optsd["--hc"][0].split(",")
        if "--hw" in optsd:
            options["hw"] = optsd["--hw"][0].split(",")
        if "--hl" in optsd:
            options["hl"] = optsd["--hl"][0].split(",")
        if "--hh" in optsd:
            options["hh"] = optsd["--hh"][0].split(",")
        if "--hs" in optsd:
            options["hs"] = optsd["--hs"][0]
        if "--sc" in optsd:
            options["sc"] = optsd["--sc"][0].split(",")
        if "--sw" in optsd:
            options["sw"] = optsd["--sw"][0].split(",")
        if "--sl" in optsd:
            options["sl"] = optsd["--sl"][0].split(",")
        if "--sh" in optsd:
            options["sh"] = optsd["--sh"][0].split(",")
        if "--ss" in optsd:
            options["ss"] = optsd["--ss"][0]

        if "--auto-filter" in optsd:
            options["auto_filter"] = True

        if "--hard-filter" in optsd:
            options["hard_filter"] = True

    @staticmethod
    def _parse_seed(url, optsd, options):
        if url:
            options.url = url

        if "-X" in optsd:
            options["method"] = optsd["-X"][0]

        if "--ip" in optsd:
            splitted = optsd["--ip"][0].partition(":")
            if not splitted[0]:
                raise FuzzExceptBadOptions("An IP must be specified")

            options["connect_to_ip"] = {
                "ip": splitted[0],
                "port": splitted[2] if splitted[2] else "80",
            }

        if "-d" in optsd:
            options["postdata"] = optsd["-d"][0]

        for bb in optsd["-b"]:
            options["cookie"].append(bb)

        for x in optsd["-H"]:
            splitted = x.partition(":")
            if splitted[1] != ":":
                raise FuzzExceptBadOptions(
                    'Wrong header specified, it should be in the format "name: value".'
                )
            options["headers"].append((splitted[0], splitted[2].strip()))

        if "-R" in optsd:
            options["rlevel"] = int(optsd["-R"][0])
            # By default, set the plugin_rlevel to the ordinary rlevel
            options["plugin_rlevel"] = int(optsd["-R"][0])

        # Optionally overwrite default value
        if "-r" in optsd:
            options["plugin_rlevel"] = int(optsd["-r"][0])

        if "-L" in optsd:
            options["follow_redirects"] = True

    @staticmethod
    def _parse_conn_options(optsd, conn_options: FuzzSession):

        if "--conn-delay" in optsd:
            conn_options["conn_delay"] = int(optsd["--conn-delay"][0])

        if "--req-delay" in optsd:
            conn_options["req_delay"] = int(optsd["--req-delay"][0])

        if "--limit-requests" in optsd:
            conn_options["limitrequests"] = True

        # "-Z" option disables scanmode. Scanmode disabled exits the script on an unsuccessful request
        if "-Z" in optsd:
            conn_options["scanmode"] = False

        if "--domain-scope" in optsd:
            conn_options["domain_scope"] = True

        if "-s" in optsd:
            conn_options["delay"] = float(optsd["-s"][0])

        if "-t" in optsd:
            conn_options["concurrent"] = int(optsd["-t"][0])

    @staticmethod
    def _parse_options(optsd, options):

        if "--recipe" in optsd:
            options["recipe"] = optsd["--recipe"]

        if "--dry-run" in optsd:
            options["transport"] = "dryrun"

    @staticmethod
    def _parse_scripts(optsd, options):
        """
        options = dict(
            script = "",
            script_args = {},
        )
        """

        if "--plugins" in optsd:
            options["script"] = "" if optsd["--script"][0] == "" else optsd["--script"][0]

        if "--script-args" in optsd:
            try:
                options["script_args"] = dict(
                    [x.split("=", 1) for x in optsd["--script-args"][0].split(",")]
                )
            except ValueError:
                raise FuzzExceptBadOptions(
                    "Script arguments: Incorrect arguments format supplied."
                )
