import sys
from wfuzz import __version__ as version

examples_banner = """Examples:\n\twfuzz -z file,users.txt -z file,pass.txt --sc 200 http://www.site.com/log.asp?user=FUZZ&pass=FUZ2Z
\twfuzz -z range,1-10 --hc=BBB http://www.site.com/FUZZ{something not there}
\twfuzz --script=robots -z list,robots.txt http://www.webscantest.com/FUZZ"""

exec_banner = """********************************************************\r
* Wfuzz OffSec {version} - The Web Fuzzer {align: <{width1}}*\r
********************************************************\r\n""".format(
    version=version, align=" ", width1=22 - len(version)
)

help_banner = """********************************************************
* Wfuzz {version} - The Web Fuzzer {align: <{width1}}*
*                                                      *
* Version up to 1.4c coded by:                         *
* Christian Martorella (cmartorella@edge-security.com) *
* Carlos del ojo (deepbit@gmail.com)                   *
*                                                      *
* Version 1.4d to {version} coded by: {align: <{width2}}*
* Xavier Mendez (xmendez@edge-security.com)            *
*  __   ___  ___  __   ___  __      ___  __   __       *
* /  \ |__  |__  /__` |__  /  `    |__  /  \ |__) |__/ *
* \__/ |    |    .__/ |___ \__,    |    \__/ |  \ |  \ *
********************************************************\r\n""".format(
    version=version, width1=29 - len(version), align=" ", width2=26 - len(version)
)

help_banner2 = """********************************************************
* Wfuzz {version} - The Web Fuzzer {align: <{width1}}*
*                                                      *
* Coded by:                                            *
*                                                      *
* Xavier Mendez (xmendez@edge-security.com)            *
*  __   ___  ___  __   ___  __      ___  __   __       *
* /  \ |__  |__  /__` |__  /  `    |__  /  \ |__) |__/ *
* \__/ |    |    .__/ |___ \__,    |    \__/ |  \ |  \ *
********************************************************\r\n""".format(
    version=version, align=" ", width1=29 - len(version)
)

header_usage_wfpayload = """Usage:\twfpayload [options] -z payload --zD params\r\n
"""

header_usage = """Usage:\twfuzz [options] -z payload,params <url>\r\n
\tFUZZ, ..., FUZnZ  wherever you put these keywords wfuzz will replace them with the values of the specified payload.
\tFUZZ{baseline_value} FUZZ will be replaced by baseline_value. It will be the first request performed and could be used as a base for filtering.
"""

brief_usage = (f"""{header_usage}\n\n{examples_banner}\n\nType wfuzz -h for \
further information or --help for advanced usage.""")

options = header_usage + f"""

Options:
\t-h                        : This help
\t--help                    : Advanced help
\t--version                 : Wfuzz version details
\t-e <type>                 : List of available encoders/payloads/iterators/printers/scripts
\t
\t-c                        : Output without colors
\t-a                        : Output without showing progress messages. Useful if the term can not handle them.
\t-v                        : Verbose information.
\t--interact                : Listens for key presses. Interact with the program. Press 'p' for pause, 'h' for help.
\t
\t-p addr                   : Use Proxy in format ip:port:type. Repeat option for using various proxies.
\t                            Where type could be SOCKS4,SOCKS5 or HTTP if omitted.
\t
\t-t N                      : Specify the number of concurrent connections (20 default)
\t-s N                      : Specify time delay between requests (0 default)
\t-F                        : When a redirection is detected, follow by sending an additional request to it
\t-o                        : Switch scope check from IP based to domain name based
\t-R depth                  : Recursive path discovery being depth the maximum recursion level (0 default)
\t-q depth                  : Specify the recursion depth originating from plugins (equal to -R default).
\t
\t-u url                    : Specify a URL for the request.
\t-f filename               : Store results in the output file as JSON.
\t--runtime-log             : Save runtime information to a file, such as which seeds have been thrown.
\t-z payload                : Specify a payload for each FUZZ keyword used in the form of type,parameters,encoder.
\t                            A list of encoders can be used, ie. md5-sha1. Encoders can be chained, ie. md5@sha1.
\t                            Encoders category can be used. ie. url
\t                            Use help as a payload to show payload plugin's details (you can filter using --slice)
\t-w wordlist               : Specify a wordlist file (alias for -z file,wordlist).
\t-V alltype                : All parameters bruteforcing (allvars and allpost). No need for FUZZ keyword.
\t-X method                 : Specify an HTTP method for the request, ie. HEAD or FUZZ
\t
\t-b cookie                 : Specify a cookie for the requests
\t-d postdata               : Use post data (ex: "id=FUZZ&catalogue=1")
\t-H header                 : Use header (ex:"Cookie:id=1312321&user=FUZZ")
\t--basic/ntlm/digest auth  : in format "user:pass" or "FUZZ:FUZZ" or "domain\\FUZ2Z:FUZZ"
\t
\t--hc/hl/hw/hh N[,N]+      : Hide responses with the specified code/lines/words/chars (Use BBB for taking values from baseline)
\t--sc/sl/sw/sh N[,N]+      : Show responses with the specified code/lines/words/chars (Use BBB for taking values from baseline)
\t--ss/hs regex             : Show/Hide responses with the specified regex within the content
\t--auto-filter             : Activate automatic runtime filtering on responses. If a response repeats itself too often, it will get filtered out of postprocessing.
"""

all_options = options + """

Advanced options:

\t--filter-help             : Filter language specification
\t--dump-recipe <filename>  : Prints specified options in dedicated format that can later be imported
\t--recipe <filename>       : Reads options from a recipe. Repeat for various recipes.
\t--dry-run                 : Test run without actually making any HTTP request.
\t--prev                    : Print the previous HTTP requests (only when using payloads generating fuzzresults)
\t--efield <expr>           : Show the specified language expression together with the current payload. Repeat for various fields.
\t--field <expr>            : Do not show the payload but only the specified language expression. Repeat for various fields.
\t--limit-requests          : Limit recursions. Once 20000 requests are sent, recursions will be deactivated
\t--ip host:port            : Specify an IP to connect to instead of the URL's host in the format ip:port
\t-Z                        : Disable Scan mode (Connection errors will cause the script to exit).
\t--req-delay N             : Sets the maximum time in seconds the request is allowed to take (CURLOPT_TIMEOUT). Default 90.
\t--conn-delay N            : Sets the maximum time in seconds the connection phase to the server to take (CURLOPT_CONNECTTIMEOUT). Default 90.
\t
\t-A                        : Alias for -v and --script=default
\t--script=<plugins>        : Runs script's scan. <plugins> is a comma separated list of plugin-files or plugin-categories
\t--script-help=<plugins>   : Show help about scripts.
\t--script-args n1=v1,...   : Provide arguments to scripts. ie. --script-args grep.regex=\"<A href=\\\"(.*?)\\\">\"
\t
\t-m iterator               : Specify an iterator for combining payloads (product by default)

\t--zP <params>             : Arguments for the specified payload (it must be preceded by -z or -w).
\t--zD <default>            : Default parameter for the specified payload (it must be preceded by -z or -w).
\t--zE <encoder>            : Encoder for the specified payload (it must be preceded by -z or -w).

\t--slice <filter>          : Filter payload\'s elements using the specified expression. It must be preceded by -z.
\t--filter <filter>         : Show/hide responses using the specified filter expression (Use BBB for taking values from baseline)
\t--hard-filter             : Change the filter to not only hide the responses, but also prevent post processing of them.
\t--prefilter <filter>      : Filter items before fuzzing using the specified expression. Repeat for concatenating filters.

"""

usage = options

verbose_usage = all_options

wfpayload_usage = f"""{header_usage_wfpayload}\n\nOptions:
\t-h/--help                 : This help
\t--help                    : Advanced help
\t--version                 : Wfuzz version details
\t-e <type>                 : List of available encoders/payloads/iterators/printers/scripts
\t
\t--recipe <filename>       : Reads options from a recipe. Repeat for various recipes.
\t--dump-recipe <filename>  : Prints current options as a recipe
\t
\t-c                        : Output without colors
\t-v                        : Verbose information.
\t-f filename               : Store results in the output file as JSON.
\t--prev                    : Print the previous HTTP requests (only when using payloads generating fuzzresults)
\t--efield <expr>           : Show the specified language expression together with the current payload. Repeat option for various fields.
\t--field <expr>            : Do not show the payload but only the specified language expression. Repeat option for various fields.
\t
\t-A                        : Alias for -v and --script=default
\t-F                        : When a redirection is detected, follow it by sending an additional request to it
\t--script=<plugins>        : Runs script's scan. <plugins> is a comma separated list of plugin-files or plugin-categories
\t--script-help=<plugins>   : Show help about scripts.
\t--script-args n1=v1,...   : Provide arguments to scripts. ie. --script-args grep.regex=\"<A href=\\\"(.*?)\\\">\"
\t
\t-z payload                : Specify a payload for each FUZZ keyword used in the form of name[,parameter][,encoder].
\t                            A list of encoders can be used, ie. md5-sha1. Encoders can be chained, ie. md5@sha1.
\t                            Encoders category can be used. ie. url
\t                            Use help as a payload to show payload plugin's details (you can filter using --slice)
\t--zP <params>             : Arguments for the specified payload (it must be preceded by -z or -w).
\t--zD <default>            : Default parameter for the specified payload (it must be preceded by -z or -w).
\t--zE <encoder>            : Encoder for the specified payload (it must be preceded by -z or -w).
\t--slice <filter>          : Filter payload\'s elements using the specified expression. It must be preceded by -z.
\t-w wordlist               : Specify a wordlist file (alias for -z file,wordlist).
\t
\t--hc/hl/hw/hh N[,N]+      : Hide responses with the specified code/lines/words/chars (Use BBB for taking values from baseline)
\t--sc/sl/sw/sh N[,N]+      : Show responses with the specified code/lines/words/chars (Use BBB for taking values from baseline)
\t--ss/hs regex             : Show/hide responses with the specified regex within the content
\t--filter <filter>         : Show/hide responses using the specified filter expression (Use BBB for taking values from baseline)
\t--prefilter <filter>      : Filter items before fuzzing using the specified expression. Repeat for concatenating filters.
"""


class Term:
    """Class designed to handle terminal matters. Provides convenience functions."""
    reset = "\x1b[0m"
    bright = "\x1b[1m"
    dim = "\x1b[2m"
    underscore = "\x1b[4m"
    blink = "\x1b[5m"
    reverse = "\x1b[7m"
    hidden = "\x1b[8m"

    delete = "\x1b[0K"
    oneup = "\x1b[1A"

    fgBlack = "\x1b[30m"
    fgRed = "\x1b[31m"
    fgGreen = "\x1b[32m"
    fgYellow = "\x1b[33m"
    fgBlue = "\x1b[34m"
    fgMagenta = "\x1b[35m"
    fgCyan = "\x1b[36m"
    fgWhite = "\x1b[37m"

    bgBlack = "\x1b[40m"
    bgRed = "\x1b[41m"
    bgGreen = "\x1b[42m"
    bgYellow = "\x1b[43m"
    bgBlue = "\x1b[44m"
    bgMagenta = "\x1b[45m"
    bgCyan = "\x1b[46m"
    bgWhite = "\x1b[47m"

    noColour = ""

    @staticmethod
    def get_colour(code: int) -> str:
        """Return appropriate color based on the response's  status code"""
        if code == 0:
            cc = Term.fgYellow
        elif 400 <= code < 500:
            cc = Term.fgRed
        elif 300 <= code < 400:
            cc = Term.fgBlue
        elif 200 <= code < 300:
            cc = Term.fgGreen
        else:
            cc = Term.fgMagenta

        return cc

    @staticmethod
    def set_colour(colour):
        """Directly prints the color to the terminal."""
        sys.stdout.write(colour)

    @staticmethod
    def colour_string(colour: str, text: str) -> str:
        """
        Return supplied string with supplied colour (ANSI Escapes).
        Useful when supplied string is not to be immediately printed
        """
        return colour + text + Term.reset

    @staticmethod
    def erase_lines(lines: int) -> None:
        """Erases the amount of lines specified from the terminal"""
        for i in range(lines - 1):
            sys.stdout.write("\r" + Term.delete)
            sys.stdout.write(Term.oneup)

        sys.stdout.write("\r" + Term.delete)


class UncolouredTerm(Term):
    reset = bright = dim = underscore = blink = reverse = hidden = fgBlack = fgRed = fgGreen = fgYellow = fgBlue =\
        fgMagenta = fgCyan = fgWhite = bgBlack = bgRed = bgGreen = bgYellow = bgBlue = bgMagenta = bgCyan = bgWhite = ""

    @staticmethod
    def get_colour(code: int) -> str:
        return ""

    @staticmethod
    def colour_string(colour: str, text: str) -> str:
        return text
