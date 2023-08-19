from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from wfuzz.ui.console.common import Term, UncolouredTerm

if TYPE_CHECKING:
    from wfuzz.options import FuzzSession
    from queue import Queue
from wfuzz.fuzzobjects import FuzzWord, FuzzPlugin, FuzzResult, FuzzStats
from wfuzz.exception import (
    FuzzExceptBadFile,
    FuzzExceptBadOptions,
    FuzzExceptPluginError,
)
from wfuzz.facade import Facade
from wfuzz.factories.plugin_factory import plugin_factory
from wfuzz.helpers.file_func import find_file_in_paths
from wfuzz.externals.reqresp.cache import HttpCache

import sys
import os
from abc import abstractmethod
from distutils import util


class BasePlugin:
    """
    Base class for all other plugins that exist
    """

    def __init__(self, options):
        # Setting disabled to true will cause it not to execute for future requests anymore
        self.disabled = False
        # The results queue is the queue receiving all the plugin output. PluginExecutor will later read it
        self.results_queue: Optional[Queue] = None
        # Bool indicating whether plugin should only be run once. PluginExecutor will disable after first execution
        self.run_once = False
        # Plugins might adjust the FuzzResult object passed into them. This contains the original state
        self.base_fuzz_res: Optional[FuzzResult] = None
        self.cache = HttpCache()
        self.options: FuzzSession = options
        self.logger = logging.getLogger("runtime_log")
        self.term = Term() if options["colour"] else UncolouredTerm()

        # check mandatory params, assign default values
        for name, default_value, required, description in self.parameters:
            param_name = f"{self.name}.{name}"

            if required and param_name not in list(self.kbase.keys()):
                raise FuzzExceptBadOptions(
                    "Plugins, missing parameter %s!" % (param_name,)
                )

            if param_name not in list(self.kbase.keys()):
                self.kbase[param_name] = default_value

    def run(self, fuzz_result, control_queue: Queue, results_queue: Queue) -> None:
        """
        Will be triggered by PluginExecutor
        """
        try:
            self.results_queue = results_queue
            self.base_fuzz_res = fuzz_result
            self.process(fuzz_result)
        except Exception as e:
            self.logger.exception(f"An exception occured while running the plugin {self.name}")
            exception_plugin = plugin_factory.create("plugin_from_error", self.name, e)
            results_queue.put(exception_plugin)
        finally:
            # Signal back completion of execution
            control_queue.get()
            control_queue.task_done()
            return

    @abstractmethod
    def process(self, fuzz_result: FuzzResult) -> None:
        """
        This is where the plugin processing is done. Any wfuzz plugin must implement this method

        A kbase (get_kbase, has_kbase, add_kbase) is shared between all plugins. this can be used to store and
        retrieve relevant "collaborative" information.
        """
        raise NotImplementedError

    @abstractmethod
    def validate(self, fuzz_result: FuzzResult) -> bool:
        """
        Function to poll whether the plugin should be executed for the current result.
        PluginExecutor skips the plugin if it does not validate
        """
        raise FuzzExceptPluginError("Method count not implemented")

    def add_information(self, message: str, severity=FuzzPlugin.INFO) -> None:
        """
        Add some information to the result queue. It will be printed out for the user to see. Optionally specify
        severity
        """
        message = f"Plugin {self.name}: " + message
        self.results_queue.put(plugin_factory.create("plugin_from_finding", self.name, message, severity))

    def add_exception_information(self, exception: str) -> None:
        """
        Add some exception information to the result queue. It will be printed out for the user to see
        """
        self.logger.warning(f"The plugin {self.name} has added exception information: {exception}")
        self.results_queue.put(plugin_factory.create("plugin_from_error", self.name, exception))

    def queue_url(self, url: str, method: str = "GET") -> None:
        """
        Enqueue a new full URL. It will be processed by PluginExecutor, and if it is valid
        (not already in cache + in scope) will be queued to be sent by wfuzz
        """
        self.results_queue.put(plugin_factory.create(
                "backfeed_plugin", self.name, self.base_fuzz_res, url, method))

    def queue_seed(self, seeding_url):
        """
        Enqueue a new SEED (full recursion). It will be processed by PluginExecutor, and if
        it is valid will be queued to be sent by wfuzz
        Optionally takes seeding_url. Can be arbitrarily specified to use as a new FUZZ
        """
        # Stop queueing seeds if the limit is reached already
        if self.options['limitrequests'] and self.options.http_pool.queued_requests > \
                self.options["LIMITREQUESTS_THRESHOLD"]:
            return
        self.results_queue.put(plugin_factory.create(
                "seed_plugin", self.name, self.base_fuzz_res, seeding_url))

    def _bool(self, value) -> bool:
        return bool(util.strtobool(value))


class BasePrinter:
    def __init__(self, output):
        self.outputfile_handle = None
        # List containing every result information
        self.result_list = []
        if output:
            try:
                self.outputfile_handle = open(output, "w")
            except IOError as e:
                raise FuzzExceptBadFile("Error opening file. %s" % str(e))
        else:
            self.outputfile_handle = sys.stdout

        self.verbose = Facade().printers.kbase["verbose"]

    @abstractmethod
    def header(self, summary: FuzzStats):
        """
        Print at the beginning of the file
        """
        raise FuzzExceptPluginError("Method header not implemented")

    @abstractmethod
    def footer(self, summary: FuzzStats):
        """
        Print at the end of the file. Will also be called when runtime is done
        """
        raise FuzzExceptPluginError("Method footer not implemented")

    @abstractmethod
    def update_results(self, fuzz_result: FuzzResult, stats: FuzzStats):
        """
        Update the result list and return result information (response of request).
        """
        raise FuzzExceptPluginError("Method result not implemented")

    @abstractmethod
    def print_to_file(self, data_to_write):
        """
        Overwrite file contents with data
        """
        raise FuzzExceptPluginError("Method result not implemented")


class BasePayload:
    def __init__(self, params):
        self.params = params

        # default params
        if "default" in self.params:
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

    def get_type(self):
        raise FuzzExceptPluginError("Method get_type not implemented")

    def get_next(self):
        raise FuzzExceptPluginError("Method get_next not implemented")

    def __next__(self):
        return FuzzWord(self.get_next(), self.get_type())

    def count(self):
        raise FuzzExceptPluginError("Method count not implemented")

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
