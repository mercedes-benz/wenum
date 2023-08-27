import argparse


def parse_args() -> argparse.Namespace:
    """Define all options"""
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
    io_group.add_argument("-w", "--wordlist", action="append", help="Specify a wordlist file.")
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
    filter_group.add_argument("--hl", action="append", help="Hide responses matching the supplied comma-separated lines.",
                        nargs="*", type=int)
    filter_group.add_argument("--hw", action="append", help="Hide responses matching the supplied comma-separated words.",
                        nargs="*", type=int)
    filter_group.add_argument("--hs", action="append",
                        help="Hide responses matching the supplied comma-separated sizes/chars.", nargs="*", type=int)
    filter_group.add_argument("--hr", help="Hide responses matching the supplied regex.")
    filter_group.add_argument("--sc", action="append", help="Show responses matching the supplied comma-separated codes.",
                        nargs="*", type=int)
    filter_group.add_argument("--sl", action="append", help="Show responses matching the supplied comma-separated lines.",
                        nargs="*", type=int)
    filter_group.add_argument("--sw", action="append", help="Show responses matching the supplied comma-separated words.",
                        nargs="*", type=int)
    filter_group.add_argument("--ss", action="append",
                        help="Show responses matching the supplied comma-separated sizes/chars.", nargs="*", type=int)
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
    # io.add_argument("-K", "--config", help="Read config from specified path. By default read from XDG_CONFIG_HOME ~/.config/wenum/wenum-config.toml")#TODO implement
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
    request_proessing_group.add_argument("--request‐timeout", type=int,
                        help="Change the maximum seconds the request is allowed to take.", default=20)
    request_proessing_group.add_argument("--domain-scope", action="store_true",
                        help="Base the scope check on the domain name instead of IP.")
    # parser.add_argument("--list-plugins", help="List all plugins and categories")#TODO implement, though maybe this falls off with the info option
    io_group.add_argument("--plugins",
                        help="Plugins to be run as a comma separated list of plugin-files or plugin-categories",
                        nargs="*")  # TODO add nargs and in future handle that way instead of comma separation. Maybe same with other options with multiple args?
    # parser.add_argument("--plugin-args", help="Provide arguments to scripts. e.g. --plugin-args grep.regex=\"<A href=\\\"(.*?)\\\">\"", nargs="*")#TODO Maybe remove? Really no plugin utilizes this except for regex.py, and I dont know if they ever will
    request_building_group.add_argument("-i", "--iterator", help="Set the iterator used when combining multiple wordlists (default: product).",
                        choices=["product", "zip", "chain"])
    # parser.add_argument("info", help="Print information about the specified topic and exit.", choices=["plugins", "iterators", "filter"])#TODO implement, and this feels like a good positional argument. Probably because by design the user should not use it in combination with anything else
    parser.add_argument("-V", "--version", action="store_true", help="Print version and exit.")
    return parser.parse_args()
