import sys


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

    def get_color(self, code: int) -> str:
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
    def set_color(color):
        """Directly prints the color to the terminal."""
        sys.stdout.write(color)

    def color_string(self, color: str, text: str) -> str:
        """
        Return supplied string with supplied color (ANSI Escapes).
        Useful when supplied string is not to be immediately printed
        """
        return color + text + self.reset

    def erase_lines(self, lines: int) -> None:
        """Erases the amount of lines specified from the terminal"""
        for i in range(lines - 1):
            sys.stdout.write("\r" + self.delete)
            sys.stdout.write(self.oneup)

        sys.stdout.write("\r" + self.delete)
