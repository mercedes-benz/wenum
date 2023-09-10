from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wenum.runtime_session import FuzzSession
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
    AutofilterQ,
    RedirectQ
)


class Fuzzer:
    def __init__(self, session: FuzzSession):
        """
        Create queues. Usually
        genReq ---> seed_queue -> http_queue/dryrun -> [round_robin -> plugins_queue] * N
        -> [recursive_queue -> routing_queue] -> [filter_queue] -> [save_queue] -> [printer_queue] ---> results
        The order is dictated simply by the order in which they get added to the qmanager object
        """

        self.session: FuzzSession = session
        self.qmanager: QueueManager = QueueManager(session)
        self.last_queue: MyPriorityQueue = MyPriorityQueue()
        self.logger = logging.getLogger("debug_log")

        self.qmanager.add("seed_queue", SeedQueue(session))

        if session.options.dry_run:
            self.qmanager.add("transport_queue", DryRunQ(session))
        else:
            self.qmanager.add("transport_queue", HttpQueue(session))

        if session.options.location:
            self.qmanager.add("redirects_queue", RedirectQ(session))

        if session.options.auto_filter:
            self.qmanager.add(
                "autofilter_queue", AutofilterQ(session)
            )

        if session.options.plugins_list:
            self.qmanager.add("plugins_queue", PluginQueue(session))

        if session.options.recursion:
            self.qmanager.add("recursive_queue", RecursiveQ(session))

        if (session.options.plugins_list or session.options.recursion) and not session.options.dry_run:
            rq = RoutingQ(
                session,
                {
                    FuzzType.SEED: self.qmanager["seed_queue"],
                    FuzzType.BACKFEED: self.qmanager["transport_queue"],
                },
            )

            self.qmanager.add("routing_queue", rq)

        if session.compiled_filter:
            self.qmanager.add(
                "filter_queue", FilterQ(session, session.compiled_filter)
            )

        if session.compiled_simple_filter:
            self.qmanager.add(
                "simple_filter_queue",
                FilterQ(session, session.compiled_simple_filter),
            )

        if session.options.hard_filter:
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

        if session.compiled_printer_list:
            self.qmanager.add("printer_queue", FilePrinterQ(session))

        self.qmanager.add("printer_cli", CLIPrinterQ(session))

        self.qmanager.bind(self.last_queue)

        # initial seed request
        self.qmanager.start()

    def __iter__(self):
        return self

    def __next__(self):
        """
        This function is called by the for loop in the main function when going over it
        """
        # http://bugs.python.org/issue1360
        print("getting")
        fuzz_result = self.last_queue.get()
        print("got")
        self.last_queue.task_done()

        # done!
        if not fuzz_result:
            raise StopIteration
        elif fuzz_result.item_type == FuzzType.ERROR:
            for i in range(10):
                print(fuzz_result.exception)
                print(fuzz_result.item_type)
            raise fuzz_result.exception

        return fuzz_result

    def stats(self):
        return dict(
            list(self.qmanager.get_stats().items())
            + list(self.qmanager["transport_queue"].http_pool.job_stats().items())
            + list(self.session.compiled_stats.get_runtime_stats().items())
        )

    def cancel_job(self):
        self.qmanager.cancel()

    def pause_job(self):
        self.qmanager["transport_queue"].pause.clear()

    def resume_job(self):
        self.qmanager["transport_queue"].pause.set()
