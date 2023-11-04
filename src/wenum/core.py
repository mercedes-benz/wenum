from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from typing import Optional
from threading import RLock

if TYPE_CHECKING:
    from wenum.runtime_session import FuzzSession
from .fuzzobjects import FuzzType, FuzzItem

import collections
from itertools import zip_longest

from .myqueues import MyPriorityQueue, FuzzQueue, MonitorQueue
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
        fuzz_item: FuzzItem = self.last_queue.get()
        self.last_queue.task_done()

        # STOP item may come from the monitorqueue. Raise an according exception in that case
        if fuzz_item.item_type == FuzzType.STOP:
            self.logger.debug("core.py: Stopping the queues")
            raise StopIteration

        elif fuzz_item.item_type == FuzzType.ERROR:
            raise fuzz_item.exception

        return fuzz_item

    def stats(self) -> dict:
        return dict(
            list(self.qmanager.get_stats().items())
            + list(self.qmanager["transport_queue"].http_pool.job_stats().items())
            + list(self.session.compiled_stats.get_runtime_stats().items())
        )

    def cancel_job(self) -> None:
        """
        Method called when an exception of some sort is catched by the main loop.
        If no requests are left or if the user sends an interrupt, it also ends up throwing an exception that
        leads to the execution of this method.
        """
        self.qmanager.stop_queues()

    def pause_job(self):
        self.qmanager["transport_queue"].pause.clear()

    def resume_job(self):
        self.qmanager["transport_queue"].pause.set()


class QueueManager:
    """
    Class responsible for keeping track of all the active queues and managing them
    """
    def __init__(self, session):
        self._queues: collections.OrderedDict[str, FuzzQueue] = collections.OrderedDict()
        # Queue at the end of the chain to e.g. check if all requests are done
        self.monitor_queue: Optional[MonitorQueue] = None
        # Queue receiving information from monitor_queue; last_queue items will be pulled by the main thread
        self.last_queue: Optional[MyPriorityQueue] = None
        self._mutex = RLock()
        self.logger = logging.getLogger("debug_log")

        self.session = session

    def add(self, name, queue):
        """
        Add another Queue to the manager
        """
        self._queues[name] = queue

    def move_to_end(self, key, last=True):
        """
        Execute move_to_end function of OrderedDict
        """
        try:
            self._queues.move_to_end(key, last)
        except KeyError:
            raise

    def get_stats(self):
        stat_list = []

        for queue in list(self._queues.values()):
            stat_list = stat_list + list(queue.get_stats().items())

        return dict(stat_list)

    def bind(self, last_queue: MyPriorityQueue):
        """Set all the correct output queues."""
        with self._mutex:
            self.last_queue = last_queue

            queue_list: list[FuzzQueue] = list(self._queues.values())

            self.monitor_queue: MonitorQueue = MonitorQueue(self.session, last_queue)

            # Set the next queue for each queue
            for index, (first, second) in enumerate(zip_longest(queue_list[0:-1], queue_list[1:])):
                first.next_queue(second)
                first.set_syncq(self.monitor_queue)
                # Check for the remaining next queues if they are processing discarded fuzzresults
                for next_one in queue_list[index + 1:]:
                    if next_one.process_discarded:
                        first.queue_discard = next_one
                        break
                # If none of the remaining queues intend to process discarded results,
                # set the sync as the discard queue
                if not first.queue_discard:
                    first.queue_discard = self.monitor_queue

            # The last queue receives the monitor queue as it's next queue
            queue_list[-1].next_queue(self.monitor_queue)
            queue_list[-1].set_syncq(self.monitor_queue)
            queue_list[-1].queue_discard = self.monitor_queue

    def __getitem__(self, key):
        return self._queues[key]

    def start(self):
        """
        Starting method called by the core
        """
        with self._mutex:
            if self._queues:
                self.monitor_queue.qstart()
                for queue in list(self._queues.values()):
                    queue.qstart()

                list(self._queues.values())[0].put_important(FuzzItem(FuzzType.STARTSEED))

    def stop_queues(self):
        """
        Called to stop all active queues.

        This is a 2-step process of first stopping all the queues' main loop and only after every queue confirmed
        having stopped will they actually start closing. This prevents racing conditions.
        If each queue immediately tried to close right after being ready to do so themselves, they may get stuck
        because they may receive an item from another queue in the very last moment before joining.
        The aforementioned 2-step process ensures that such a scenario will not happen, because after the stopped
        event is set, the queue promises not to meddle with other queues anymore.
        """
        with self._mutex:
            if self._queues:
                self.logger.debug("QueueManager: Closing all queues")
                # Send signal to all queues to stop their main loop
                for active_queue in list(self._queues.values()):
                    active_queue.cancel()
                    active_queue.put_important(FuzzItem(FuzzType.STOP))
                    self.logger.debug(f"QueueManager: Sent stop signal to {active_queue.get_name()}")
                self.monitor_queue.put_important(FuzzItem(FuzzType.STOP))
                self.logger.debug(f"QueueManager: Sent stop signal to {self.monitor_queue.name}")

                # Wait until all queues confirmed that they have stopped their main loop
                for active_queue in list(self._queues.values()):
                    active_queue.stopped.wait()
                self.monitor_queue.stopped.wait()
                self.logger.debug(f"QueueManager: All queues have stopped")

                # Send signal to all queues to allow them to finish and join
                for active_queue in list(self._queues.values()):
                    active_queue.close.set()
                self.monitor_queue.close.set()

                # Close all queue threads
                for active_queue in list(self._queues.values()):
                    self.logger.debug(f"QueueManager joining queue {active_queue.get_name()}")
                    active_queue.join()
                self.logger.debug(f"QueueManager joining queue {self.monitor_queue.name}")
                self.monitor_queue.join()

                self.logger.debug(f"QueueManager: joining LastQueue")

                # Finally stop the last queue
                while self.last_queue.qsize() > 0:
                    self.last_queue.get()
                    self.last_queue.task_done()
                self.last_queue.join()

                self.logger.debug("QueueManager: All queues have joined")
