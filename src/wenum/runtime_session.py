from typing import Optional

from .exception import (
    FuzzExceptBadOptions,
)

from .factories.fuzzresfactory import resfactory
from .factories.dictfactory import dictionary_factory
from .fuzzobjects import FuzzStats, FuzzResult
from .filters.ppfilter import FuzzResFilter
from .filters.simplefilter import FuzzResSimpleFilter

from .core import Fuzzer
from .iterators import BaseIterator
from .myhttp import HttpPool

from .externals.reqresp.cache import HttpCache
from .printers import JSON, BasePrinter
from wenum.user_opts import Options

# The priority moves in steps of 10 to allow a buffer zone for future finegrained control. This way, one group of
# requests (such as within a seed) has leverage over queuing with less prio than the other requests while being
# prioritized higher than the next group of requests (e.g. the next seed)
PRIORITY_STEP = 10


class FuzzSession:
    """Class designed to carry runtime information relevant for conditional decisions"""
    def __init__(self, options: Options):
        self.options: Options = options

        self.compiled_stats: Optional[FuzzStats] = None
        self.compiled_filter: Optional[FuzzResFilter] = None
        self.compiled_simple_filter: Optional[FuzzResSimpleFilter] = None
        self.compiled_seed: Optional[FuzzResult] = None
        self.compiled_printer: Optional[BasePrinter] = None
        self.compiled_iterator: Optional[BaseIterator] = None
        self.current_priority_level: int = PRIORITY_STEP

        self.cache: HttpCache = HttpCache()
        self.http_pool: Optional[HttpPool] = None

        #TODO Unused?
        self.stats = FuzzStats()

    def assign_next_priority_level(self):
        """
        Pulls current priority level, increases it and returns the value. Useful for assigning new level
        to new recursions
        """
        self.current_priority_level += PRIORITY_STEP
        return self.current_priority_level

    def fuzz(self, **kwargs):
        """Method used by the API"""
        #self.data.update(kwargs)

        fz = None
        try:
            fz = Fuzzer(self.compile())

            for f in fz:
                yield f

        finally:
            if fz:
                fz.cancel_job()
                self.stats.update(self.compiled_stats)

            if self.http_pool:
                self.http_pool.deregister()
                self.http_pool = None

    def __enter__(self):
        self.http_pool = HttpPool(self)
        self.http_pool.register()
        return self

    def __exit__(self, *args):
        self.close()

    def get_fuzz_words(self) -> set:
        """
        #TODO Verify this is polling the amount of FUZZ words supplied by the user
        """
        fuzz_words = self.compiled_filter.get_fuzz_words()

        if self.compiled_seed:
            fuzz_words += self.compiled_seed.payload_man.get_fuzz_words()

        return set(fuzz_words)

    def compile_iterator(self):
        self.compiled_iterator = dictionary_factory.create(
            "dictio_from_options", self
        )

    def compile_seeds(self):
        self.compiled_seed = resfactory.create("seed_from_options", self)

    def compile(self):
        """
        Sets some things before actually running
        """

        self.options.basic_validate()

        if self.options.output:
            self.compiled_printer = JSON(self.options.output, self.options.verbose)

        self.compile_seeds()
        self.compile_iterator()

        # filter options
        self.compiled_simple_filter = FuzzResSimpleFilter.from_options(self)
        self.compiled_filter = FuzzResFilter(self.options.filter)

        self.compiled_stats = FuzzStats.from_options(self)

        # Check payload num
        fuzz_words = self.get_fuzz_words()

        if self.compiled_iterator.width() != len(fuzz_words):
            raise FuzzExceptBadOptions("FUZZ words and number of payloads do not match!")

        if not self.http_pool:
            self.http_pool = HttpPool(self)
            self.http_pool.register()

        return self

    def close(self):
        """
        Actions to execute before shutting down the runtime.
        """
        if self.compiled_iterator:
            self.compiled_iterator.cleanup()

        if self.http_pool:
            self.http_pool.deregister()
            self.http_pool = None
