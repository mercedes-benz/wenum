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
    """Class responsible for reading the supplied wordlist in the commandline."""

    def __init__(self, file_path):
        self.file_path = file_path

        try:
            self.f = FileDetOpener(self.find_file(self.file_path))
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
        """Counts the amount of lines in the file"""

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
        """#TODO Verify and phase out, as os.path.isfile() should do this instead. No custom implementation where the stdlib suffices.
        Find file of the provided payload's file path in the file system"""
        if os.path.exists(name):
            return name

        for pa in Facade().settings.get("general", "lookup_dirs").split(","):
            fn = find_file_in_paths(name, pa)

            if fn is not None:
                return fn

        return name
