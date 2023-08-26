import sys
from wenum import __version__ as version

examples_banner = """Examples:\n\twenum -w users.txt -w pass.txt --sc 200 http://www.site.com/log.asp?user=FUZZ&pass=FUZ2Z
\twenum --script=robots -w robots.txt http://www.webscantest.com/FUZZ"""

exec_banner = """********************************************************\r
* wenum {version} - A Web Fuzzer {align: <{width1}}*\r
********************************************************\r\n""".format(
    version=version, align=" ", width1=22 - len(version)
)

help_banner = """********************************************************
* wenum {version} - A Web Fuzzer {align: <{width1}}*
********************************************************\r\n""".format(
    version=version, width1=29 - len(version), align=" ", width2=26 - len(version)
)

help_banner2 = """********************************************************
* wenum {version} - The Web Fuzzer {align: <{width1}}*
********************************************************\r\n""".format(
    version=version, align=" ", width1=29 - len(version)
)

header_usage = """Usage:\twenum [options] -w wordlist <url>\r\n
\tFUZZ, ..., FUZnZ  wherever you put these keywords wenum will replace them with the values of the specified payload.
"""

brief_usage = (f"""{header_usage}\n\n{examples_banner}\n\nType wenum -h for \
further information or --help for advanced usage.""")

options = header_usage + f"""

Options:
\t-h                        : This help
\t--help                    : Advanced help
\t--version                 : wenum version details
\t-e <type>                 : List of available encoders/iterators/printers/scripts
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
\t--debug-log             : Save runtime information to a file, such as which seeds have been thrown.
\t-w wordlist               : Specify a wordlist file.
\t-X method                 : Specify an HTTP method for the request, ie. HEAD or FUZZ
\t
\t-b cookie                 : Specify a cookie for the requests
\t-d postdata               : Use post data (ex: "id=FUZZ&catalogue=1")
\t-H header                 : Use header (ex:"Cookie:id=1312321&user=FUZZ")
\t
\t--hc/hl/hw/hh N[,N]+      : Hide responses with the specified code/lines/words/chars
\t--sc/sl/sw/sh N[,N]+      : Show responses with the specified code/lines/words/chars
\t--ss/hs regex             : Show/Hide responses with the specified regex within the content
\t--auto-filter             : Activate automatic runtime filtering on responses. If a response repeats itself too often, it will get filtered out of postprocessing.
"""

all_options = options + """

Advanced options:

\t--filter-help             : Filter language specification
\t--dump-config <filename>  : Prints specified options in dedicated format that can later be imported
\t--recipe <filename>       : Reads options from a recipe. Repeat for various recipes.
\t--dry-run                 : Test run without actually making any HTTP request.
\t--limit-requests          : Limit recursions. Once 20000 requests are sent, recursions will be deactivated
\t--ip host:port            : Specify an IP to connect to instead of relying on the DNS response for the URL's host. Format ip:port. This can help if you want to force connecting to a specific IP and still present a host name in the SNI, which will remain the URL's host.
\t-Z                        : Disable Scan mode (Connection errors will cause the script to exit).
\t--req-delay N             : Sets the maximum time in seconds the request is allowed to take (CURLOPT_TIMEOUT). Default 90.
\t--conn-delay N            : Sets the maximum time in seconds the connection phase to the server to take (CURLOPT_CONNECTTIMEOUT). Default 90.
\t
\t-A                        : Alias for -v and --script=default
\t--script=<plugins>        : Runs script's scan. <plugins> is a comma separated list of plugin-files or plugin-categories
\t--script-help=<plugins>   : Show help about scripts.
\t--script-args n1=v1,...   : Provide arguments to scripts. ie. --script-args grep.regex=\"<A href=\\\"(.*?)\\\">\"
\t
\t-m iterator               : Specify an iterator for combining wordlists (product by default)


\t--filter <filter>         : Show/hide responses using the specified filter expression
\t--hard-filter             : Change the filter to not only hide the responses, but also prevent post processing of them.
\t--prefilter <filter>      : Filter items before fuzzing using the specified expression. Repeat for concatenating filters.

"""

usage = options

verbose_usage = all_options


class Term:
    """Class designed to handle terminal matters. Provides convenience functions."""
    def __init__(self, options):
        if options.colorless:
            self.reset = self.bright = self.dim = self.underscore = self.blink = self.reverse = self.hidden \
                = self.fgBlack = self.fgRed = self.fgGreen = self.fgYellow = self.fgBlue = \
                self.fgMagenta = self.fgCyan = self.fgWhite = self.bgBlack = self.bgRed = self.bgGreen \
                = self.bgYellow = self.bgBlue = self.bgMagenta = self.bgCyan = self.bgWhite = ""
        else:
            self.reset = "\x1b[0m"
            self.bright = "\x1b[1m"
            self.dim = "\x1b[2m"
            self.underscore = "\x1b[4m"
            self.blink = "\x1b[5m"
            self.reverse = "\x1b[7m"
            self.hidden = "\x1b[8m"

            self.fgBlack = "\x1b[30m"
            self.fgRed = "\x1b[31m"
            self.fgGreen = "\x1b[32m"
            self.fgYellow = "\x1b[33m"
            self.fgBlue = "\x1b[34m"
            self.fgMagenta = "\x1b[35m"
            self.fgCyan = "\x1b[36m"
            self.fgWhite = "\x1b[37m"

            self.bgBlack = "\x1b[40m"
            self.bgRed = "\x1b[41m"
            self.bgGreen = "\x1b[42m"
            self.bgYellow = "\x1b[43m"
            self.bgBlue = "\x1b[44m"
            self.bgMagenta = "\x1b[45m"
            self.bgCyan = "\x1b[46m"
            self.bgWhite = "\x1b[47m"

        self.delete = "\x1b[0K"
        self.oneup = "\x1b[1A"
        self.noColour = ""

    def get_colour(self, code: int) -> str:
        """Return appropriate color based on the response's  status code"""
        if code == 0:
            cc = self.fgYellow
        elif 400 <= code < 500:
            cc = self.fgRed
        elif 300 <= code < 400:
            cc = self.fgBlue
        elif 200 <= code < 300:
            cc = self.fgGreen
        else:
            cc = self.fgMagenta

        return cc

    @staticmethod
    def set_colour(colour):
        """Directly prints the color to the terminal."""
        sys.stdout.write(colour)

    def colour_string(self, colour: str, text: str) -> str:
        """
        Return supplied string with supplied colour (ANSI Escapes).
        Useful when supplied string is not to be immediately printed
        """
        return colour + text + self.reset

    def erase_lines(self, lines: int) -> None:
        """Erases the amount of lines specified from the terminal"""
        for i in range(lines - 1):
            sys.stdout.write("\r" + self.delete)
            sys.stdout.write(self.oneup)

        sys.stdout.write("\r" + self.delete)


class UncolouredTerm(Term):
    reset = bright = dim = underscore = blink = reverse = hidden = fgBlack = fgRed = fgGreen = fgYellow = fgBlue =\
        fgMagenta = fgCyan = fgWhite = bgBlack = bgRed = bgGreen = bgYellow = bgBlue = bgMagenta = bgCyan = bgWhite = ""

    @staticmethod
    def get_colour(code: int) -> str:
        return ""

    @staticmethod
    def colour_string(colour: str, text: str) -> str:
        return text
