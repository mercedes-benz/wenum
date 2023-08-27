from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wenum.options import FuzzSession
from .fuzzobjects import FuzzType

from .myqueues import MyPriorityQueue, QueueManager
from .fuzzqueues import (
    SeedQueue,
    FilePrinterQ,
    RoutingQ,
    FilterQ,
    PluginQueue,
    RecursiveQ,
    DryRunQ,
    HttpQueue,
    CLIPrinterQ,
    PassPayloadQ,
    AutofilterQ,
    RedirectQ
)


class Fuzzer:
    def __init__(self, options: FuzzSession):
        """
        Create queues. Usually
        genReq ---> seed_queue -> http_queue/dryrun -> [round_robin -> plugins_queue] * N
        -> [recursive_queue -> routing_queue] -> [filter_queue] -> [save_queue] -> [printer_queue] ---> results
        The order is dictated simply by the order in which they get added to the qmanager object
        """

        self.options: FuzzSession = options
        self.qmanager: QueueManager = QueueManager(options)
        self.results_queue: MyPriorityQueue = MyPriorityQueue()
        self.logger = logging.getLogger("runtime_log")

        self.qmanager.add("seed_queue", SeedQueue(options))

        if options.dry_run:
            self.qmanager.add("transport_queue", DryRunQ(options))
        else:
            self.qmanager.add("transport_queue", HttpQueue(options))

        if options.location:
            self.qmanager.add("redirects_queue", RedirectQ(options))

        if options.auto_filter:
            self.qmanager.add(
                "autofilter_queue", AutofilterQ(options)
            )

        if options.plugins_list:
            self.qmanager.add("plugins_queue", PluginQueue(options))

        if options.recursion:
            self.qmanager.add("recursive_queue", RecursiveQ(options))

        if (options.plugins_list or options.recursion) and not options.dry_run:
            rq = RoutingQ(
                options,
                {
                    FuzzType.SEED: self.qmanager["seed_queue"],
                    FuzzType.BACKFEED: self.qmanager["transport_queue"],
                },
            )

            self.qmanager.add("routing_queue", rq)

        if options.compiled_filter.is_active():
            self.qmanager.add(
                "filter_queue", FilterQ(options, options.compiled_filter)
            )

        if options.compiled_simple_filter.is_active():
            self.qmanager.add(
                "simple_filter_queue",
                FilterQ(options, options.compiled_simple_filter),
            )

        if options.hard_filter:
            """
            This will push the plugins in the list after the FilterQ
            """
            queues_after_filter = ["plugins_queue", "recursive_queue", "routing_queue"]
            for queue in queues_after_filter:
                try:
                    self.qmanager.move_to_end(queue)
                # KeyError will be raised if it tries to push a queue that is inactive. Can be ignored
                except KeyError:
                    continue

        if options.compiled_printer:
            self.qmanager.add("printer_queue", FilePrinterQ(options))

        self.qmanager.add("printer_cli", CLIPrinterQ(options))

        self.qmanager.bind(self.results_queue)

        # initial seed request
        self.qmanager.start()

    def __iter__(self):
        return self

    def __next__(self):
        """
        This function is called by the for loop in the main function when going over it
        """
        # http://bugs.python.org/issue1360
        fuzz_result = self.results_queue.get()
        self.results_queue.task_done()

        # done! (None sent has gone through all queues).
        if not fuzz_result:
            raise StopIteration
        elif fuzz_result.item_type == FuzzType.ERROR:
            raise fuzz_result.exception

        return fuzz_result

    def stats(self):
        return dict(
            list(self.qmanager.get_stats().items())
            + list(self.qmanager["transport_queue"].http_pool.job_stats().items())
            + list(self.options.compiled_stats.get_runtime_stats().items())
        )

    def cancel_job(self):
        self.qmanager.cancel()

    def pause_job(self):
        self.qmanager["transport_queue"].pause.clear()

    def resume_job(self):
        self.qmanager["transport_queue"].pause.set()
