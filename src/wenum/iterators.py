import itertools
from functools import reduce
from abc import ABC, abstractmethod

from builtins import zip as builtinzip


class BaseIterator(ABC):
    @abstractmethod
    def count(self):
        raise NotImplementedError

    @abstractmethod
    def width(self):
        raise NotImplementedError

    @abstractmethod
    def payloads(self):
        raise NotImplementedError

    def cleanup(self):
        for payload in self.payloads():
            payload.close()


class Zip(BaseIterator):
    name = "zip"
    summary = "Returns an iterator that aggregates elements from each of the iterables."

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

    def __iter__(self):
        return self


class Product(BaseIterator):
    name = "product"
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

    def __iter__(self):
        return self


class Chain(BaseIterator):
    name = "chain"
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

    def __iter__(self):
        return self
