from wenum.fuzzobjects import FuzzWord
from wenum.helpers.file_func import FileDetOpener
from wenum.helpers.file_func import find_file_in_paths
import os
from wenum.facade import Facade
from wenum.fuzzobjects import FuzzWordType
from wenum.exception import (
    FuzzExceptBadFile,
    FuzzExceptBadOptions,
)


class File:
    """Class responsible for reading the supplied wordlist in the commandline.
    #TODO some methods may be unnecessarily complex, as this partially stems from
      times where these parsers were plugins, and they can be refactored at some point.
      """

    parameters = (
        ("fn", "", True, "Filename of a valid dictionary"),
        (
            "count",
            "True",
            False,
            "Indicates if the number of words in the file should be counted.",
        ),
        ("encoding", "Auto", False, "Indicates the file encoding."),
    )

    def __init__(self, params):
        self.params = params
        self.file_path = ""

        # default params
        if "default" in self.params:
            print("default")
            print(self.params)
            self.params["fn"] = self.params["default"]

        try:
            print(self.params["fn"])
            self.f = FileDetOpener(self.find_file(self.params["fn"]))
        except IOError as e:
            raise FuzzExceptBadFile("Error opening file. %s" % str(e))

        self.__count = None

    def get_type(self):
        return FuzzWordType.WORD

    def get_next(self):
        line = next(self.f)
        if not line:
            self.f.close()
            raise StopIteration
        return line.strip()

    def __next__(self):
        return FuzzWord(self.get_next(), self.get_type())

    def count(self):
        if self.params["count"].lower() == "false":
            return -1

        if self.__count is None:
            self.__count = len(list(self.f))
            self.f.reset()

        return self.__count

    def __iter__(self):
        return self

    def close(self):
        pass

    @staticmethod
    def find_file(name):
        if os.path.exists(name):
            return name

        for pa in Facade().settings.get("general", "lookup_dirs").split(","):
            fn = find_file_in_paths(name, pa)

            if fn is not None:
                return fn

        return name
