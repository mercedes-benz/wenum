#!/usr/bin/env python
from __future__ import annotations

import datetime
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from wenum.options import FuzzSession
import warnings
import traceback
import logging

from .core import Fuzzer
from .facade import Facade
from .exception import FuzzException, FuzzExceptBadInstall
from .ui.console.mvc import Controller, KeyPress
from .ui.console.common import Term
from .ui.console.clparser import parse_args
from .options import FuzzSession

from .fuzzobjects import FuzzStats


def main():
    """
    Executing core wenum
    """
    keypress: Optional[KeyPress] = None
    fuzzer: Optional[Fuzzer] = None
    session_options: Optional[FuzzSession] = None
    logger = None
    term = None

    try:
        # parse command line
        arguments = parse_args()
        session_options: FuzzSession = FuzzSession(arguments).compile()

        fuzzer = Fuzzer(session_options)

        if not session_options.noninteractive:
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

        term = Term(session_options)

        logger = logging.getLogger("runtime_log")
        # Logging startup options on startup
        logger.info(f"""Runtime options:
{session_options.export_active_options_dict()}""")

        # This loop causes the main loop of wenum to execute
        for res in fuzzer:
            pass

    except FuzzException as e:
        warnings.warn("Fatal exception: {}".format(str(e)))
    except KeyboardInterrupt:
        if term:
            text = term.color_string(term.fgYellow, "Finishing pending requests...")
            (term.color_string(term.fgYellow, "Finishing pending requests..."))
        else:
            text = "Finishing pending requests..."
        warnings.warn(text)
        if fuzzer:
            fuzzer.cancel_job()
    except NotImplementedError as e:
        exception_message = "Fatal exception: Error importing wenum extensions: {}".format(str(e))
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
                _log_runtime_stats(logger, session_options.compiled_stats)
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
