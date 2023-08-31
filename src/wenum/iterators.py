import itertools
from functools import reduce
from abc import ABC, abstractmethod

from builtins import zip as builtinzip


class BaseIterator(ABC):
    """Classes inheriting from this base class are supposed to provide different
    means of iterating through supplied FUZZ keywords"""
    @abstractmethod
    def count(self):
        raise NotImplementedError

    @abstractmethod
    def width(self) -> int:
        """
        Returns amount of FUZZ keywords the iterator consumes
        """
        raise NotImplementedError

    @abstractmethod
    def payloads(self):
        raise NotImplementedError

    def cleanup(self):
        """
        Called when runtime is shutting down
        """
        for payload in self.payloads():
            payload.close()


class Zip(BaseIterator):
    """Returns an iterator that aggregates elements from each of the iterables."""

    def __init__(self, *i):
        self._payload_list = i
        self.__width = len(i)
        self.__count = min([x.count() for x in i])
        self.it = builtinzip(*i)

    def count(self):
        return self.__count

    def width(self):
        return self.__width

    def payloads(self):
        return self._payload_list

    def __next__(self):
        return next(self.it)


class Product(BaseIterator):
    summary = "Returns an iterator cartesian product of input iterables."

    def __init__(self, *i):
        self._payload_list = i
        self.__width = len(i)
        self.__count = reduce(lambda x, y: x * y.count(), i[1:], i[0].count())
        self.it = itertools.product(*i)

    def count(self):
        return self.__count

    def width(self):
        return self.__width

    def payloads(self):
        return self._payload_list

    def __next__(self):
        return next(self.it)


class Chain(BaseIterator):
    summary = "Returns an iterator returns elements from the first iterable until it is exhausted, then proceeds to the next iterable, until all of the iterables are exhausted."

    def __init__(self, *i):
        self._payload_list = i
        self.__count = sum([x.count() for x in i])
        self.it = itertools.chain(*i)

    def count(self):
        return self.__count

    def width(self):
        return 1

    def payloads(self):
        return self._payload_list

    def __next__(self):
        return (next(self.it),)

