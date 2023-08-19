import pickle as pickle
import gzip

from wenum.externals.moduleman.plugin import moduleman_plugin
from wenum.exception import FuzzExceptBadFile
from wenum.fuzzobjects import FuzzResult, FuzzWordType
from wenum.plugin_api.base import BasePayload
from wenum.helpers.obj_dyn import rgetattr


@moduleman_plugin
class wenump(BasePayload):
    name = "wenump"
    author = ("Xavi Mendez (@xmendez)",)
    version = "0.2"
    description = (
        "This payload uses pickle.",
        "Warning: The pickle module is not intended to be secure against erroneous or maliciously constructed data.",
        "Never unpickle data received from an untrusted or unauthenticated source.",
        "See: https://blog.nelhage.com/2011/03/exploiting-pickle/",
    )
    summary = "Returns fuzz results' URL from a previous stored wenum session."
    category = ["default"]
    priority = 99

    parameters = (
        ("fn", "", True, "Filename of a valid wenum result file."),
        (
            "attr",
            None,
            False,
            "Attribute of fuzzresult to return. If not specified the whole object is returned.",
        ),
    )

    default_parameter = "fn"

    def __init__(self, params):
        BasePayload.__init__(self, params)

        self.__max = -1
        self.attr = self.params["attr"]
        self._it = self._gen_wenum(self.params["fn"])

    def count(self):
        return self.__max

    def get_next(self):
        next_item = next(self._it)

        return next_item if not self.attr else rgetattr(next_item, self.attr)

    def get_type(self):
        return FuzzWordType.FUZZRES if not self.attr else FuzzWordType.WORD

    def _gen_wenum(self, output_fn):
        try:
            with gzip.open(self.find_file(output_fn), "r+b") as output:
                while 1:
                    item = pickle.load(output)
                    if not isinstance(item, FuzzResult):
                        raise FuzzExceptBadFile(
                            "Wrong wenum payload format, the object read is not a valid fuzz result."
                        )

                    yield item
        except IOError as e:
            raise FuzzExceptBadFile("Error opening wenum payload file. %s" % str(e))
        except EOFError:
            return
