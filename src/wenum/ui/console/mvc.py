import datetime
import shutil
import sys
import time
from collections import defaultdict
import threading

import rich.console

from wenum.factories.fuzzresfactory import resfactory

from itertools import zip_longest

from wenum.fuzzobjects import FuzzWordType, FuzzResult, FuzzStats
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.console import Console
from rich.table import Row

from .term import Term
from wenum import __version__ as version
from wenum.plugin_api.urlutils import parse_url
import wenum.ui.console.kbhit as kbhit
from .output import wrap_always_list
from ...myqueues import FuzzQueue

usage = """\r\n
Interactive keyboard commands:\r\n
h: Show this help

p: Pause
s: Show stats
d: Show debug stats
r: Show all seeds/recursions that have been queued
"""


class SimpleEventDispatcher:
    """
    Class responsible for listening for an event (e.g. keypress)
    """

    def __init__(self):
        self.publisher = defaultdict(list)

    def create_event(self, msg):
        self.publisher[msg] = []

    def subscribe(self, func, msg, dynamic=False):
        if msg not in self.publisher and not dynamic:
            raise KeyError("subscribe. No such event: %s" % msg)
        else:
            self.publisher[msg].append(func)

    def notify(self, msg, **event):
        if msg not in self.publisher:
            raise KeyError("notify. Event not subscribed: %s" % msg)
        else:
            for functor in self.publisher[msg]:
                functor(**event)


class KeyPress(threading.Thread):
    """
    Class responsible for catching keyboard inputs during runtime
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self.inkey = kbhit.KBHit()
        self.name = "KeyPress"

        self.dispatcher = SimpleEventDispatcher()
        self.dispatcher.create_event("h")
        self.dispatcher.create_event("p")
        self.dispatcher.create_event("s")
        self.dispatcher.create_event("r")
        self.dispatcher.create_event("d")

        self.do_job = True

    def cancel_job(self):
        self.do_job = False

    def run(self):
        while self.do_job:
            if self.inkey.kbhit():
                pressed_char = self.inkey.getch()
                if pressed_char == "p":
                    self.dispatcher.notify("p", key="p")
                elif pressed_char == "s":
                    self.dispatcher.notify("s", key="s")
                elif pressed_char == "h":
                    self.dispatcher.notify("h", key="h")
                elif pressed_char == "r":
                    self.dispatcher.notify("r", key="r")
                elif pressed_char == "d":
                    self.dispatcher.notify("d", key="d")


class Controller:
    """
    Class responsible for converting caught keyboard inputs into execution of methods
    """

    def __init__(self, fuzzer, view: KeyPress):
        self.fuzzer = fuzzer
        self.printer_queue: FuzzQueue = self.fuzzer.qmanager["printer_cli"]
        self.view = view
        self.__paused = False
        self.stats: FuzzStats = fuzzer.session.compiled_stats

        self.view.dispatcher.subscribe(self.on_help, "h")
        self.view.dispatcher.subscribe(self.on_pause, "p")
        self.view.dispatcher.subscribe(self.on_stats, "s")
        self.view.dispatcher.subscribe(self.on_seeds, "r")
        self.view.dispatcher.subscribe(self.on_debug, "d")
        self.term = Term(fuzzer.session)

    def on_help(self, **event):
        message_fuzzresult: FuzzResult = resfactory.create("fuzzres_from_message", usage)
        self.printer_queue.put_important(message_fuzzresult)

    def on_pause(self, **event):
        self.__paused = not self.__paused
        if self.__paused:
            self.fuzzer.pause_job()
            self.fuzzer.session.console.print()
            message = self.term.color_string(self.term.fgYellow, "\nPausing requests. Already enqueued requests "
                                                                 "may still get printed out during pause.")
            message += "\nType h to see all options."
            message_fuzzresult: FuzzResult = resfactory.create("fuzzres_from_message", message)
            self.printer_queue.put_important(message_fuzzresult)
        else:
            message = self.term.color_string(self.term.fgGreen, "Resuming execution...")
            message_fuzzresult: FuzzResult = resfactory.create("fuzzres_from_message", message)
            self.printer_queue.put_important(message_fuzzresult)
            self.fuzzer.resume_job()

    def on_stats(self, **event):
        message = self.generate_stats()
        message_fuzzresult: FuzzResult = resfactory.create("fuzzres_from_message", message)
        self.printer_queue.put_important(message_fuzzresult)

    def on_debug(self, **event):
        message = self.generate_debug_stats()
        message_fuzzresult: FuzzResult = resfactory.create("fuzzres_from_message", message)
        self.printer_queue.put_important(message_fuzzresult)

    def on_seeds(self, **event):
        message_fuzzresult: FuzzResult = resfactory.create("fuzzres_from_message", self.generate_seed_message())
        self.printer_queue.put_important(message_fuzzresult)

    def generate_debug_stats(self):
        message = "\n=============== Debug ===================\n"
        stats = self.fuzzer.stats()
        for k, v in list(stats.items()):
            message += f"{k}: {v}\n"
        message += "\n=========================================\n"
        return message

    def generate_stats(self):
        pending_requests = self.stats.total_req - self.stats.processed()
        pending_seeds = self.stats.pending_seeds()
        stats = self.stats
        message = f"""\nRequests Per Seed: {str(stats.wordlist_req)}
Pending Requests: {str(pending_requests)}
Pending Seeds: {str(pending_seeds)}\n"""

        if stats.backfeed() > 0:
            message += f"""Total Backfed/Plugin Requests: {stats.backfeed()}
Processed Requests: {(str(stats.processed())[:8])}
Filtered Requests: {(str(stats.filtered())[:8])}\n"""
        totaltime = time.time() - stats.starttime
        req_sec = (stats.processed() / totaltime if totaltime > 0 else 0)
        totaltime_formatted = datetime.timedelta(seconds=int(totaltime))
        message += f"Total Time: {str(totaltime_formatted)}\n"
        if req_sec > 0:
            message += f"Requests/Sec.: {str(req_sec)[:8]}\n"
            eta = pending_requests / req_sec
            if eta > 60:
                message += f"ET Left Min.: {str(eta / 60)[:8]}\n"
            else:
                message += f"ET Left Sec.: {str(eta)[:8]}\n"
        return message

    def generate_seed_message(self):
        """Print information about currently queued seeds"""
        seed_list_len = str(len(self.stats.seed_list))
        colored_length = self.term.color_string(self.term.fgYellow, seed_list_len)
        seed_message = f"In total, {colored_length} seeds have been generated. List of seeds:\n"
        colored_url_list = "[ "
        parsed_initial_url = parse_url(self.stats.url)
        for seed_url in self.stats.seed_list:
            parsed_seed_url = parse_url(seed_url)
            seed_url = seed_url
            scheme = parsed_seed_url.scheme
            netloc = parsed_seed_url.netloc
            # Only color the scheme and netloc if they are different from the initial ones
            if scheme != parsed_initial_url.scheme:
                colored_scheme = self.term.color_string(self.term.fgYellow, scheme)
                seed_url.replace(parsed_seed_url.scheme, colored_scheme)
            if netloc != parsed_initial_url.netloc:
                colored_netloc = self.term.color_string(self.term.fgYellow, netloc)
                seed_url.replace(parsed_seed_url.netloc, colored_netloc)
            colored_path = self.term.color_string(self.term.fgYellow, parsed_seed_url.path)
            seed_url = seed_url.replace(parsed_seed_url.path, colored_path)
            # Imitating the look of a list when printed out. Reason for not simply using a list is because the terminal
            # does not properly handle the Colour codes when using lists
            colored_url_list += "'" + seed_url + "', "

        colored_url_list += "]"
        seed_message += colored_url_list
        return seed_message


class View:
    """
    Class handling the CLI output
    """
    # Result number, status code, lines, words, chars, method, url
    result_row_widths = [10, 8, 6, 8, 10, 6, shutil.get_terminal_size(fallback=(80, 25))[0] - 66]
    verbose_result_row_widths = [10, 10, 8, 8, 6, 9, 30, 30, shutil.get_terminal_size(fallback=(80, 25))[0] - 145]

    def __init__(self, session):
        self.last_discarded_result = None
        self.verbose = session.options.verbose
        self.term = Term(session)
        self.console: Console = session.console
        # Keeps track of the line count of the print for discarded responses (to then overwrite these lines with the
        # next print)
        self.printed_temp_lines = 0

        if not session.options.quiet:
            # Progress bar
            self.overall_progress: Progress = Progress(
                SpinnerColumn(),
                TextColumn("{task.fields[processed]}"),
                "/",
                TextColumn("{task.fields[total_req]}"), transient=True
            )
            self.filtered_progress: Progress = Progress(
                TextColumn("{task.fields[oldest]}"),
                TextColumn("{task.fields[middle]}"),
                TextColumn("{task.fields[recent]}")
            )
            self.overall_task = self.overall_progress.add_task("Press h for help", processed=0, total_req=0)
            #TODO Adjust for actual display of filtered responses
            self.oldest_filtered_task = self.filtered_progress.add_task("oldest", oldest="w", middle="1",
                                                                 recent="3")
            self.middle_filtered_task = self.filtered_progress.add_task("middle", oldest="e",
                                                                        middle="e", recent="2")
            self.recent_filtered_task = self.filtered_progress.add_task("recent", oldest="e", middle="e", recent="2")
            progress_table = Table.grid()
            progress_table.add_row(
                Panel.fit(
                    self.overall_progress, title="Press h for help", border_style="green", padding=(1, 1)
                ),
                Panel(
                    self.filtered_progress, title="Filtered responses", border_style="red", padding=(0, 0), expand=True
                )
            )
            self.live = Live(progress_table, auto_refresh=True, console=self.console)

    def update_status(self, stats):
        """
        Updates the progress bar's values
        """
        self.overall_progress.update(self.overall_task, total_req=stats.total_req, processed=stats.processed())

    def _print_result_verbose(self, fuzz_result: FuzzResult, print_nres=True):
        txt_color = self.term.noColour

        if fuzz_result.history.redirect_header:
            location = fuzz_result.history.full_redirect_url
            url_output = f"{fuzz_result.url} -> {location}"
        else:
            url_output = fuzz_result.url
            location = ""

        server = ""
        if "Server" in fuzz_result.history.headers.response:
            server = fuzz_result.history.headers.response["Server"]

        columns = [
            ("%09d:" % fuzz_result.result_number if print_nres else " |_", txt_color),
            ("%.3fs" % fuzz_result.timer, txt_color),
            (
                "%s" % str(fuzz_result.code) if not fuzz_result.exception else "XXX",
                self.term.get_color(fuzz_result.code),
            ),
            ("%d L" % fuzz_result.lines, txt_color),
            ("%d W" % fuzz_result.words, txt_color),
            ("%d Ch" % fuzz_result.chars, txt_color),
            (server, txt_color),
            (location, txt_color),
            (f'"{url_output}"' if not fuzz_result.exception else f'"{fuzz_result.url}"', txt_color),
        ]

        self.term.set_color(txt_color)
        printed_lines = self._print_line(columns, self.verbose_result_row_widths)
        if fuzz_result.discarded:
            self.printed_temp_lines += printed_lines

    def _print_header(self, columns, max_widths):
        self.console.print("=" * (3 * len(max_widths) + sum(max_widths[:-1]) + 10))
        self._print_line(columns, max_widths)
        self.console.print("=" * (3 * len(max_widths) + sum(max_widths[:-1]) + 10))
        self.console.print("")
        pass

    def _print_line(self, columns: list[tuple[str, str]], max_widths: list[int]) -> int:
        """
        Takes columns, which are tuples of message(0) and color_code(1), and a list of respective widths for
        the columns, prints them and returns the amount of lines printed.
        Function suitable any time there is a column separated line to be printed out. color_code(1) will
        color the entire column.
        Manually inserting ANSI color codes within message(0) will instead cause buggy behavior.
        """

        def wrap_columns(columns: list[tuple[str, str]], max_widths: list[int]) -> list[list[str]]:
            """Takes all columns and wraps them depending on their respective max_width value. Returns a list
            containing a list of the columns, whereas each inner list represents a full line.
            E.g. simplified, if one row was [ ('123456', ''), ('abc', '') ], the max_widths [ 3, 3 ] may wrap it
            to [ [ '123', 'abc' ], [ '456', '' ] ]"""
            wrapped_columns = [
                wrap_always_list(item[0], width) for item, width in zip(columns, max_widths)
            ]
            return [[substr or "" for substr in item] for item in zip_longest(*wrapped_columns)]

        def print_columns(column: list[str], columns: list[tuple[str, str]]):
            """Prints a line consisting of columns with the entries separated by a few whitespaces. Needs the
            columns object to access the color code attributed to the column to be printed out"""
            sys.stdout.write(
                "   ".join(
                    [
                        color + str.ljust(str(item), width) + self.term.reset
                        for (item, width, color) in zip(
                        column, max_widths, [color[1] for color in columns]
                    )
                    ]
                )
            )

        wrapped_columns = wrap_columns(columns, max_widths)

        for line in wrapped_columns:
            print_columns(line, columns)
            sys.stdout.write("\r\n")

        sys.stdout.flush()
        return len(wrapped_columns)

    def _print_result(self, fuzz_result: FuzzResult):
        """
        Function to print out the result by taking a FuzzResult. print_nres is a bool that indicates whether the
        result number should be added to the row.
        """
        if fuzz_result.history.redirect_header:
            location = fuzz_result.history.full_redirect_url
            url_output = f"{fuzz_result.url} -> {location}"
        else:
            url_output = fuzz_result.url
        no_colour = self.term.noColour

        # Each column consists of a tuple storing both the string and the associated color of the column
        columns = [
            ("%09d:" % fuzz_result.result_number, no_colour),
            ("%s" % str(fuzz_result.code) if not fuzz_result.exception else "XXX",
             self.term.get_color(fuzz_result.code)),
            ("%d L" % fuzz_result.lines, no_colour),
            ("%d W" % fuzz_result.words, no_colour),
            ("%d Ch" % fuzz_result.chars, no_colour),
            ('%s' % fuzz_result.history.method, no_colour),
            (f'"{url_output}"' if not fuzz_result.exception
             else f'"{fuzz_result.url}"', no_colour),
        ]

        self.term.set_color(no_colour)
        printed_lines = self._print_line(columns, self.result_row_widths)
        if fuzz_result.discarded:
            self.printed_temp_lines += printed_lines

    def header(self, summary):
        """
        Prints the wenum header
        TODO Refactor, and utilize the rich library for this
        """
        exec_banner = """********************************************************\r
* wenum {version} - A Web Fuzzer {align: <{width1}}*\r
********************************************************\r\n""".format(
            version=version, align=" ", width1=22 - len(version)
        )
        self.console.print(exec_banner)
        if summary:
            self.console.print(f"Target: {summary.url}")
            if summary.wordlist_req > 0:
                self.console.print(f"Total requests: {summary.wordlist_req}")
            else:
                self.console.print(f"Total requests: <<unknown>>")

        uncolored = self.term.noColour

        if self.verbose:
            columns = [
                ("ID", uncolored),
                ("C.Time", uncolored),
                ("Response", uncolored),
                ("Lines", uncolored),
                ("Word", uncolored),
                ("Chars", uncolored),
                ("Server", uncolored),
                ("Redirect", uncolored),
                ("URL", uncolored),
            ]

            widths = self.verbose_result_row_widths
        else:
            columns = [
                ("ID", uncolored),
                ("Response", uncolored),
                ("Lines", uncolored),
                ("Word", uncolored),
                ("Chars", uncolored),
                ("Method", uncolored),
                ("URL", uncolored),
            ]

            widths = self.result_row_widths

        self._print_header(columns, widths)

    def print_result(self, fuzz_result: FuzzResult):
        """Print the result to CLI"""
        if not fuzz_result.discarded:

            # Print result
            if self.verbose:
                self.verbose_result_row_widths = [10, 10, 8, 8, 6, 9, 30, 30,
                                                  shutil.get_terminal_size(fallback=(80, 25))[0] - 145]
                self._print_result_verbose(fuzz_result)
            else:
                self.result_row_widths = [10, 8, 6, 8, 10, 6, shutil.get_terminal_size(fallback=(80, 25))[0] - 66]
                self._print_result(fuzz_result)

            # Print plugin results
            if fuzz_result.plugins_res:
                for plugin_res in fuzz_result.plugins_res:
                    if not plugin_res.is_visible() and not self.verbose:
                        continue
                    self.console.print(f" |_  {plugin_res.message}")

            if fuzz_result.exception:
                self.console.print(f" |_ ERROR: {fuzz_result.exception}")
        else:
            self.last_discarded_result = fuzz_result

    def print_result_new(self, fuzz_result: FuzzResult):
        """
        @TODO Replace the original func with this
        """
        if fuzz_result.discarded:
            return
        grid = Table.grid(pad_edge=True, padding=(0, 1), collapse_padding=False)
        grid.add_column("HTTP Code", min_width=3, max_width=3, no_wrap=False, overflow="fold")
        grid.add_column("Lines", min_width=6, max_width=6, no_wrap=False, overflow="fold", justify="right")
        grid.add_column("Words", min_width=8, max_width=8, no_wrap=False, overflow="fold", justify="right")
        grid.add_column("Bytes", min_width=10, max_width=10, no_wrap=False, overflow="fold", justify="right")
        grid.add_column("HTTP Method", min_width=7, max_width=7, no_wrap=False, overflow="fold")
        grid.add_column("URL", no_wrap=False, overflow="fold")
        grid.columns[0].style = self.get_response_code_color(fuzz_result.code)
        grid.columns[1].style = "magenta"
        grid.columns[2].style = "cyan"
        grid.columns[3].style = "yellow"
        grid.columns[4].style = "slate_blue1"

        if fuzz_result.history.redirect_header:
            location = fuzz_result.history.full_redirect_url
            link = location
            url_output = f"{fuzz_result.url} -> {location}"
        else:
            url_output = fuzz_result.url
            link = url_output

        grid.add_row(str(fuzz_result.code), str(fuzz_result.lines) + " L", str(fuzz_result.words) + " W",
                     str(fuzz_result.chars) + " B", fuzz_result.history.method, url_output + f"[link={link}]")

        # Add plugin results
        #TODO "Plugin" messages from the core are added as Plugin blabla, that should be nicer
        #TODO For better clarity, every second plugin should be visually marked e.g. styled dim
        if fuzz_result.plugins_res:
            plugin_grid = Table.grid(pad_edge=True, padding=(0, 1), collapse_padding=False)
            plugin_grid.add_column("Plugin name", max_width=25, min_width=25, no_wrap=False, overflow="fold")
            plugin_grid.add_column("Plugin message", no_wrap=False, overflow="fold")
            for plugin_res in fuzz_result.plugins_res:
                if not plugin_res.is_visible() and not self.verbose:
                    continue
                plugin_grid.add_row(f"  Plugin [i]{plugin_res.name}[/i]:", plugin_res.message)

        if fuzz_result.plugins_res:
            self.console.rule(f"Response number {fuzz_result.result_number}", style="dim green")
            self.console.print(grid, plugin_grid)
        else:
            self.console.rule(f"Response number {fuzz_result.result_number}", style="dim green")
            self.console.print(grid)

        if fuzz_result.exception:
            self.console.print(f" [b]ERROR[/b]: {fuzz_result.exception}")

    @staticmethod
    def get_response_code_color(code: int):
        """
        Takes an HTTP response code (e.g. 302) and returns the color that it should be printed with on the CLI
        """
        # informational until 200, successful until 300
        if 100 <= code < 300:
            color = "green"
        # redirects
        elif 300 <= code < 400:
            color = "blue"
        # client errors until 500, server errors until 600
        elif 400 <= code < 600:
            color = "red"
        # undefined otherwise
        else:
            color = "white"

        return color

    def footer(self, summary):
        """Function called when ending the runtime, prints a summary"""
        self.console.print("")

        self.console.print(summary)
