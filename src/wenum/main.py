#!/usr/bin/env python
from __future__ import annotations

import datetime
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from wenum.runtime_session import FuzzSession
import warnings
import traceback
import logging

from .core import Fuzzer
from .exception import FuzzException, FuzzExceptBadInstall
from .ui.console.mvc import Controller, KeyPress
from .ui.console.term import Term
from .runtime_session import FuzzSession
from wenum.user_opts import Options

from .fuzzobjects import FuzzStats


def main():
    """
    Executing core wenum
    """
    keypress: Optional[KeyPress] = None
    fuzzer: Optional[Fuzzer] = None
    session: Optional[FuzzSession] = None
    logger = logging.getLogger("debug_log")
    term = None

    try:
        # parse command line
        options = Options()
        parsed_args = options.configure_parser().parse_args()
        options.read_args(parsed_args)
        session: FuzzSession = FuzzSession(options).compile()

        fuzzer = Fuzzer(session)

        if not session.options.noninteractive:
            # initialise controller
            keypress = KeyPress()
            Controller(fuzzer, keypress)
            keypress.start()

        term = Term(session)

        # Logging startup options on startup
        logger.info("Starting")

        # This loop causes the main loop of wenum to execute
        for res in fuzzer:
            pass

    except FuzzException as e:
        exception_message = "Fatal exception: {}".format(str(e))
        warnings.warn(exception_message)
        logger.exception(exception_message)
    except KeyboardInterrupt as e:
        user_message = "Keyboard interrupt registered."
        if term:
            text = term.color_string(term.fgYellow, user_message)
        else:
            text = "Keyboard interrupt registered."
        warnings.warn(text)
        logger.info(user_message)
        if fuzzer:
            fuzzer.cancel_job()
    except NotImplementedError as e:
        exception_message = "Fatal exception: Error importing wenum extensions: {}".format(str(e))
        logger.exception(exception_message)
        warnings.warn(exception_message)
    except Exception as e:
        exception_message = "Unhandled exception: {}".format(str(e))
        logger.exception(exception_message)
        warnings.warn(exception_message)
        traceback.print_exc()
    finally:
        if session:
            _log_runtime_stats(logger, session.compiled_stats)
            session.close()
        if keypress:
            keypress.cancel_job()


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
