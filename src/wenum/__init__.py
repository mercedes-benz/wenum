__title__ = "wenum"
__version__ = "0.1"

import logging
import sys

import warnings

#TODO Refactor this file

# define a logging Handler
console = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%d.%m.%Y %H:%M:%S")
console.setLevel(logging.WARNING)
#formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
console.setFormatter(formatter)
logging.getLogger("runtime_log").addHandler(console)


# define warnings format
def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return " %s:%s: %s:%s\n" % (filename, lineno, category.__name__, message)


warnings.formatwarning = warning_on_one_line


try:
    import pycurl

    if "openssl".lower() not in pycurl.version.lower():
        warnings.warn(
            "Pycurl is not compiled against Openssl. wenum might not work correctly when fuzzing SSL sites. Check Wfuzz's documentation for more information."
        )

    if not hasattr(pycurl, "CONNECT_TO"):
        warnings.warn(
            "Pycurl and/or libcurl version is old. CONNECT_TO option is missing. wenum --ip option will not be available."
        )

except ImportError:
    warnings.warn(
        "fuzz needs pycurl to run. Pycurl could be installed using the following command: $ pip install pycurl"
    )

    sys.exit(1)

from .options import FuzzSession
from .api import fuzz, encode, decode, payload, get_session
