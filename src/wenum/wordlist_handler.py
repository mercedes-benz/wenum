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

    default_parameter = "fn"

    def __init__(self, params):
        self.params = params
        self.file_path = ""

        # default params
        if "default" in self.params:
            print("default")
            print(self.params)
            self.params[self.default_parameter] = self.params["default"]

            if not self.default_parameter:
                raise FuzzExceptBadOptions("Too many plugin parameters specified")

        # Check for allowed parameters
        if [
            k
            for k in list(self.params.keys())
            if k not in [x[0] for x in self.parameters]
               and k not in ["encoder", "default"]
        ]:
            raise FuzzExceptBadOptions("Plugin %s, unknown parameter specified!" % self.name)

        # check mandatory params, assign default values
        for name, default_value, required, description in self.parameters:
            if required and name not in self.params:
                raise FuzzExceptBadOptions("Plugin %s, missing parameter %s!" % (self.name, name))

            if name not in self.params:
                self.params[name] = default_value

        try:
            encoding = (
                self.params["encoding"]
                if self.params["encoding"].lower() != "auto"
                else None
            )
            self.f = FileDetOpener(self.find_file(self.params["fn"]), encoding)
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
