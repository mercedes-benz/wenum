#!/usr/bin/env python
from __future__ import annotations

import datetime
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from wfuzz.options import FuzzSession
import sys
import warnings
import traceback
import logging

from .core import Fuzzer
from .facade import Facade
from .exception import FuzzException, FuzzExceptBadInstall
from .ui.console.mvc import Controller, KeyPress
from .ui.console.common import (
    help_banner2,
    wfpayload_usage, Term, UncolouredTerm,
)
from .ui.console.clparser import CLParser

from .fuzzobjects import FuzzWordType, FuzzStats


def main():
    """
    Executing core wfuzz
    """
    keypress: Optional[KeyPress] = None
    fuzzer: Optional[Fuzzer] = None
    session_options: Optional[FuzzSession] = None
    logger = None
    term = None

    try:
        # parse command line
        session_options: FuzzSession = CLParser(sys.argv).parse_cl().compile()

        fuzzer = Fuzzer(session_options)

        if session_options["interactive"]:
            # initialise controller
            try:
                keypress = KeyPress()
            except ImportError as e:
                raise FuzzExceptBadInstall(
                    "Error importing necessary modules for interactive mode: %s"
                    % str(e)
                )
            else:
                Controller(fuzzer, keypress)
                keypress.start()

        if session_options["colour"]:
            term = Term()
        else:
            term = UncolouredTerm()

        logger = logging.getLogger("runtime_log")
        # Logging startup options on startup
        logger.info(f"""Runtime options:
{session_options.export_active_options_dict()}""")

        # This loop causes the main loop of wfuzz to execute
        for res in fuzzer:
            pass

    except FuzzException as e:
        warnings.warn("Fatal exception: {}".format(str(e)))
    except KeyboardInterrupt:
        if term:
            text = term.colour_string(term.fgYellow, "Finishing pending requests...")
            (term.colour_string(term.fgYellow, "Finishing pending requests..."))
        else:
            text = "Finishing pending requests..."
        warnings.warn(text)
        if fuzzer:
            fuzzer.cancel_job()
    except NotImplementedError as e:
        exception_message = "Fatal exception: Error importing wfuzz extensions: {}".format(str(e))
        if logger:
            logger.exception(exception_message)
        warnings.warn(exception_message)
    except Exception as e:
        exception_message = "Unhandled exception: {}".format(str(e))
        if logger:
            logger.exception(exception_message)
        warnings.warn(exception_message)
        traceback.print_exc()
    finally:
        if session_options:
            if logger:
                _log_runtime_stats(logger, session_options["compiled_stats"])
            session_options.close()
        if keypress:
            keypress.cancel_job()
        Facade().settings.save()


def _log_runtime_stats(logger: logging.Logger, stats: FuzzStats):
    total_time = time.time() - stats.starttime
    time_formatted = datetime.timedelta(seconds=int(total_time))
    frequent_hits = _filter_subdirectory_hits(stats)
    runtime_info = f"""
# Processed Requests: {stats.processed()}
# Generated Plugin Requests: {stats.backfeed()}
# Filtered Requests: {stats.filtered()}
# Amount of Seeds: {len(stats.seed_list)}

# Seed List:
{stats.seed_list}

# Big subdirectories:
{frequent_hits}
# Total Time: {str(time_formatted)}"""
    logger.info(runtime_info)


def _filter_subdirectory_hits(stats: FuzzStats) -> str:
    """
    stats keeps a record of the hit count within each subdirectory. This function is called to do some processing.
    It's only considered relevant for the user to know if there are at least x amount of hits within a subdir
    """
    # Order alphabetically
    sorted_hits = dict(sorted(stats.subdir_hits.items()))
    line_separated_dirs = ""
    # Only count those that have a minimum amount of hits
    for subdir, hits in sorted_hits.items():
        if hits > 50:
            line_separated_dirs += subdir + ": " + str(hits) + "\n"

    return line_separated_dirs


def main_filter():
    """
    (Probably) executing wfpayload
    """

    from .api import fuzz

    try:
        short_opts = "hvce:z:f:w:o:A"
        long_opts = [
            "efield=",
            "ee=",
            "zE=",
            "zD=",
            "field=",
            "slice=",
            "zP=",
            "oF=",
            "recipe=",
            "dump-recipe=",
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
            "prefilter=",
            "filter=",
            "help",
            "version",
            "script-help=",
            "script=",
            "script-args=",
            "prev",
            "AA",
        ]
        session_options = CLParser(
            sys.argv,
            short_opts,
            long_opts,
            help_banner2,
            wfpayload_usage,
            wfpayload_usage,
            wfpayload_usage,
        ).parse_cl()
        session_options["transport"] = "payload"
        session_options["url"] = "FUZZ"

        session_options.compile_dictio()
        payload_type = session_options["compiled_dictio"].payloads()[0].get_type()

        for res in fuzz(**session_options):
            if payload_type == FuzzWordType.WORD:
                print(res.description)
            elif payload_type == FuzzWordType.FUZZRES and session_options["show_field"]:
                field_to_print = res._field("\n")
                if field_to_print:
                    print(field_to_print)

    except KeyboardInterrupt:
        pass
    except FuzzException as e:
        warnings.warn(("Fatal exception: %s" % str(e)))
    except Exception as e:
        warnings.warn(("Unhandled exception: %s" % str(e)))


def main_encoder():
    """
    (Probably) executing wfencode
    """
    def usage():
        print(help_banner2)
        print("Usage:")
        print("\n\twfencode --help This help")
        print("\twfencode -d decoder_name string_to_decode")
        print("\twfencode -e encoder_name string_to_encode")
        print("\twfencode -e encoder_name -i <<stdin>>")
        print()

    from .api import encode, decode
    import getopt

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hie:d:", ["help"])
    except getopt.GetoptError as err:
        warnings.warn(str(err))
        usage()
        sys.exit(2)

    arg_keys = [i for i, j in opts]

    if len(args) == 0 and "-i" not in arg_keys:
        usage()
        sys.exit()

    try:
        for o, value in opts:
            if o == "-e":
                if "-i" in arg_keys:
                    for std in sys.stdin:
                        print(encode(value, std.strip()))
                else:
                    print(encode(value, args[0]))
            elif o == "-d":
                if "-i" in arg_keys:
                    for std in sys.stdin:
                        print(decode(value, std.strip()))
                else:
                    print(decode(value, args[0]))
            elif o in ("-h", "--help"):
                usage()
                sys.exit()
    except IndexError as e:
        usage()
        warnings.warn(
            "\nFatal exception: Specify a string to encode or decode.{}\n".format(
                str(e)
            )
        )
        sys.exit()
    except AttributeError as e:
        warnings.warn(
            "\nEncoder plugin missing encode or decode functionality. {}".format(str(e))
        )
    except FuzzException as e:
        warnings.warn(("\nFatal exception: %s" % str(e)))
    except Exception as e:
        warnings.warn(("Unhandled exception: %s" % str(e)))
