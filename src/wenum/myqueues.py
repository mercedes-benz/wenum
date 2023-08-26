from __future__ import annotations

import logging
import queue
import time
from typing import TYPE_CHECKING

from typing import Optional

from .ui.console.common import Term

if TYPE_CHECKING:
    from .options import FuzzSession
import collections
from itertools import zip_longest
from abc import ABC, abstractmethod

from queue import PriorityQueue
from threading import Thread, RLock
from .fuzzobjects import FuzzError, FuzzType, FuzzItem, FuzzStats


class MyPriorityQueue(PriorityQueue):
    def __init__(self, maxsize=0):
        PriorityQueue.__init__(self, maxsize)

        self.max_prio = 0

    def _put_priority(self, prio, item: FuzzItem, block, timeout=None):
        # max_prio gets updated every time this is called, to track the highest value (which is the lowest prio)
        self.max_prio = max(prio, self.max_prio)
        PriorityQueue.put(self, (prio, item), block, timeout=timeout)

    def put(self, item: FuzzItem, block=True, timeout=None):
        self._put_priority(item.priority, item, block, timeout)

    def put_first(self, item: FuzzItem, block=True):
        """
        Enqueue with highest priority
        """
        self._put_priority(0, item, block)

    def put_last(self, item: FuzzItem, block=True):
        """
        Enqueue with least priority
        """
        self._put_priority(self.max_prio + 1, item, block)

    def put_last_within_seed(self, item: FuzzItem, block=True):
        """
        Put into the queue with the least priority within the same seed. New seeds go in steps of 10.
        Meaning: Seed 1 -> Prio 10. Seed 2 -> Prio 20
        """
        self._put_priority(item.priority + 9, item, block)

    def get(self, block=True, timeout=None):
        prio, item = PriorityQueue.get(self, block=block, timeout=timeout)

        return item


class FuzzQueue(MyPriorityQueue, Thread, ABC):
    def __init__(self, options: FuzzSession, queue_out=None, maxsize=0):
        MyPriorityQueue.__init__(self, maxsize)
        self.queue_out: Optional[FuzzQueue] = queue_out
        # Next queue in line that intends to process discarded fuzz_results
        self.queue_discard: Optional[FuzzQueue] = None
        self.child_queue: bool = False
        self.syncqueue = None
        # Indicates whether the queue wants to process discarded fuzzresults
        self.process_discarded = False

        self.stats: FuzzStats = options.get("compiled_stats")
        self.options: FuzzSession = options
        self.logger = logging.getLogger("runtime_log")
        self.term = Term(options)

        Thread.__init__(self)
        self.name = self.get_name()

    def next_queue(self, nextq):
        self.queue_out = nextq

    @abstractmethod
    def process(self, item):
        """
        Method responsible for the specific processing logic of the queue. Called by run()
        """
        raise NotImplementedError

    @abstractmethod
    def get_name(self):
        """
        Method to return the name of the queue
        """
        raise NotImplementedError

    def items_to_process(self):
        """
        Method that returns a certain type of FuzzItems, which indicates whether the queue should process the item
        """
        return [FuzzType.RESULT]

    def cancel(self):
        """
        This will be called when the runtime is interrupted, e.g. due to CTRL + C.
        """
        pass

    def mystart(self):
        """
        Override this method if needed. This will be called just before starting the job.
        """
        pass

    def set_syncq(self, sync_queue):
        self.syncqueue = sync_queue

    def qstart(self):
        """
        Called by QueueManager to start the queue
        """
        self.mystart()
        self.start()

    def send_first(self, item):
        """
        Send with highest priority
        """
        self.queue_out.put_first(item)

    def send_last(self, item):
        """
        Send with least priority
        """
        self.queue_out.put_last(item)

    def send_last_within_seed(self, item):
        """
        Send with least priority within the same seed's priority
        """
        self.queue_out.put_last_within_seed(item)

    def qout_join(self):
        self.queue_out.join()

    def send(self, item):
        """
        Put the item into the next one in the chain. Queues follow a rigid
        order of execution. Depending on the parameters used, specific queues will (or will not) be put into this
        ordered chain of queues.
        """
        if item and item.discarded:
            self.queue_discard.put(item)
        else:
            self.queue_out.put(item)

    def discard(self, item):
        """Set item to discarded and forward to next queue designated to handle discarded items"""
        item.discarded = True
        self.send(item)

    def join(self):
        MyPriorityQueue.join(self)

    def tjoin(self):
        Thread.join(self)

    def _cleanup(self):
        """
        This will be called when the queue stops, either due to a cancelling during runtime (e.g. CTRL + C)
        or simply because everything is done.
        """
        pass

    def _throw(self, exception_message):
        self.logger.error(f"Exception thrown: {exception_message}")
        self.syncqueue.put_first(FuzzError(exception_message))

    def get_stats(self) -> dict:
        """Returns a dict with the queue name and the amount of items in it"""
        return {self.get_name(): self.qsize()}

    def run(self):
        """
        qstart() triggers this function. It is the main loop for most queues, which will call the process()-function
        for payloads that should be processed
        """
        cancelling = False

        while 1:
            # Items are designated to always be FuzzItems
            item: FuzzItem = self.get()
            try:
                if item is None:
                    # Child queues don't need to propagate, as the FuzzListQueue as the parent already does so
                    if not self.child_queue:
                        self.send_last(None)
                    self.task_done()
                    break
                elif cancelling:
                    self.task_done()
                    continue
                elif item.item_type == FuzzType.STARTSEED:
                    self.stats.mark_start()
                elif item.item_type == FuzzType.ENDSEED:
                    if not self.child_queue:
                        self.send_last_within_seed(item)
                    self.task_done()
                    continue
                elif item.item_type == FuzzType.CANCEL:
                    cancelling = True
                    self.send_first(item)
                    self.task_done()
                    continue

                if item.item_type in self.items_to_process():
                    self.process(item)
                # Send the item without processing
                else:
                    self.send(item)

                self.task_done()
            except Exception as e:
                self.task_done()
                self._throw(e)
        self._cleanup()


class LastFuzzQueue(FuzzQueue):
    """
    Very last queue in the chain, always present when wenum runs
    """
    def __init__(self, options, queue_out=None, maxsize=0):
        super().__init__(options, queue_out, maxsize)
        self.process_discarded = True

    def get_name(self):
        return "LastFuzzQueue"

    def process(self, item):
        pass

    def _cleanup(self):
        pass

    def _throw(self, exception_message):
        self.logger.error(f"Exception thrown: {exception_message}")
        self.queue_out.put_first(FuzzError(exception_message))

    def run(self):
        cancelling = False

        while 1:
            item = self.get()

            try:
                self.task_done()

                # None will be put into the queue by the qmanager during qmanager.cleanup()
                if item is None:
                    break
                elif cancelling:
                    continue
                elif item.item_type == FuzzType.ERROR:
                    self.qmanager.cancel()
                    self.send_first(item)
                    continue
                elif item.item_type == FuzzType.CANCEL:
                    cancelling = True
                    continue

                if item.item_type == FuzzType.RESULT and not item.discarded:
                    self.stats.update_subdirectory_hits(fuzz_result=item)
                    self.send(item)

                if item.item_type == FuzzType.ENDSEED:
                    self.stats.pending_seeds.dec()
                elif item.item_type == FuzzType.RESULT:
                    self.stats.processed.inc()
                    self.stats.pending_fuzz.dec()
                    if item.discarded:
                        self.stats.filtered.inc()

                # If no requests are left
                if self.stats.pending_fuzz() == 0 and self.stats.pending_seeds() == 0:
                    self.qmanager.cleanup()

            except Exception as e:
                self._throw(e)
                self.qmanager.cancel()

        self._cleanup()


class FuzzListQueue(FuzzQueue, ABC):
    """Queue with a list of output queues.
    Instead of the "parent" A sending every item to the queue_out Z like an ordinary FuzzQueue,
    it may choose to send some items e.g. to all their children [B, C, D],
    or randomly to one of their children, e.g. only to C.

    If the FuzzListQueue doesn't need to process discarded items but its children should do so, the parent should
    forward the items in the process() method with send_to_any()/send_to_all(), depending on the current use case."""
    def __init__(self, options, queues_out: list[FuzzQueue], maxsize=0):
        super().__init__(options=options, maxsize=maxsize)
        # Tuple containing the outqueue and a bool indicating whether it is currently blocking
        self.queues_out: list[FuzzQueue] = queues_out

        for q in self.queues_out:
            q.child_queue = True

        # List of booleans tracking which queues have blocked when an item was sent to them
        self.blocking_list: list[bool] = []
        for i in queues_out:
            self.blocking_list.append(False)
        # Index that tracks which queue in the list of queues_out is pointed towards for the next send()
        self.current_index = 0
        self._next_queue = self._get_next_route()

    def set_syncq(self, sync_queue):
        for queue_out in self.queues_out:
            queue_out.syncqueue = sync_queue

    def qstart(self):
        for q in self.queues_out:
            q.mystart()
            q.start()
        self.start()

    def run(self):
        """
        qstart() triggers this function. It is the main loop for most queues, which will call the process()-function
        for payloads that should be processed
        """
        cancelling = False

        while 1:
            item: FuzzItem = self.get()
            try:
                if item is None:
                    self.send_last_to_all(None)
                    self.send_last(None)
                    self.task_done()
                    break
                elif cancelling:
                    self.task_done()
                    continue
                elif item.item_type == FuzzType.STARTSEED:
                    self.stats.mark_start()
                elif item.item_type == FuzzType.ENDSEED:
                    self.send_last_within_seed_to_all(item)
                    self.send_last(item)
                    self.task_done()
                    continue
                elif item.item_type == FuzzType.CANCEL:
                    cancelling = True
                    self.send_first_to_all(item)
                    self.send_first(item)
                    self.task_done()
                    continue

                if item.item_type in self.items_to_process():
                    self.process(item)
                else:
                    self.send(item)

                self.task_done()
            except Exception as e:
                self.task_done()
                self._throw(e)
        self._cleanup()

    def send_first_to_all(self, item):
        """Send to all in the list with the highest priority"""
        for q in self.queues_out:
            q.put_first(item)

    def send_last_to_all(self, item):
        """Send to all in the list with the least priority"""
        for q in self.queues_out:
            q.put_last(item)

    def send_last_within_seed_to_all(self, item):
        """Send to all in the list with the least priority within the seed priority"""
        for q in self.queues_out:
            q.put_last_within_seed(item)

    def send_to_all(self, item):
        """Send to all in the list"""
        for q in self.queues_out:
            q.put(item)

    def send_to_any(self, item):
        """Randomly send to one in the list"""
        next_queue: FuzzQueue = next(self._next_queue)
        try:
            next_queue.put(item, block=False)
            self.blocking_list[self.current_index] = False
        # If the queue is full, indicate the current queue as blocking, and call the function again.
        # Will pull the next queue, and try that out
        except queue.Full:
            self.blocking_list[self.current_index] = True
            # If every queue_out blocked, wait a little before trying again
            # (This is more performant than the timeout parameter of put(), as this only waits if *all* queue_outs
            # blocked, instead of always waiting for the timeout of a single offender)
            if False not in self.blocking_list:
                time.sleep(0.5)
            self.send(item)

    def _get_next_route(self):
        while 1:
            yield self.queues_out[self.current_index]
            self.current_index += 1
            self.current_index = self.current_index % len(self.queues_out)

    def qout_join(self):
        for q in self.queues_out:
            q.join()

    def join(self):
        self.qout_join()
        MyPriorityQueue.join(self)

    def next_queue(self, nextq):
        """Set the queue_out for the parent and the outlist to nextq"""
        self.queue_out = nextq
        for queue_out in self.queues_out:
            queue_out.next_queue(nextq)

    def set_next_discard_queue(self, next_discard_queue):
        """Set the queue_discard for the parent and"""
        self.queue_discard = next_discard_queue
        for child in self.queues_out:
            child.queue_discard = next_discard_queue

    def get_stats(self) -> dict:
        """Creating stats for the queue itself, and it's list of out queues. Returns a dict with the key being the name
        of the queue and value the amount of items in the queue."""
        stat_list: list[tuple[str, int]] = []

        stat_list = stat_list + list(FuzzQueue.get_stats(self).items())

        counter = 0
        for queue_out in self.queues_out:
            size_dict = queue_out.get_stats()
            # Each queue_out gets a unique name, indicated by the counter
            size_dict[f"{queue_out.get_name()}_{counter}"] = size_dict.pop(queue_out.get_name())
            stat_list = stat_list + list(size_dict.items())
            counter += 1

        return dict(stat_list)


class QueueManager:
    def __init__(self, options):
        self._queues = collections.OrderedDict()
        self._lastqueue = None
        self._syncq = None
        self._mutex = RLock()

        self.options = options

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

    def bind(self, lastq):
        """Set all the correct output queues."""
        with self._mutex:

            queue_list: list[FuzzQueue] = list(self._queues.values())
            self._lastqueue = lastq

            # The syncq connection isn't utilized much (yet), but it's a LastFuzzQueue that every queue gets a handle to
            self._syncq: LastFuzzQueue = LastFuzzQueue(self.options, lastq)
            self._syncq.qmanager = self

            # Set the next queue for each queue
            for index, (first, second) in enumerate(zip_longest(queue_list[0:-1], queue_list[1:])):
                first.next_queue(second)
                first.set_syncq(self._syncq)
                # Check for the remaining next queues if they are processing discarded fuzzresults
                for next_one in queue_list[index + 1:]:
                    if next_one.process_discarded:
                        first.queue_discard = next_one
                        break
                # If none of the remaining queues intend to, set the sync as the discard queue
                if not first.queue_discard:
                    first.queue_discard = self._syncq

            # The last queue receives the syncq as it's next queue
            queue_list[-1].next_queue(self._syncq)
            queue_list[-1].set_syncq(self._syncq)
            queue_list[-1].queue_discard = self._syncq

    def __getitem__(self, key):
        return self._queues[key]

    def join(self, remove=False):
        with self._mutex:
            for k, queue in list(self._queues.items()):
                queue.join()
                if remove:
                    del self._queues[k]

    def start(self):
        """
        Starting method called by the core
        """
        with self._mutex:
            if self._queues:
                self._syncq.qstart()
                for queue in list(self._queues.values()):
                    queue.qstart()

                list(self._queues.values())[0].put_first(FuzzItem(FuzzType.STARTSEED))

    def cleanup(self):
        """
        Called to end the runtime
        """
        with self._mutex:
            if self._queues:
                list(self._queues.values())[0].put_last(None)
                self.join(remove=True)
                self._lastqueue.put_last(None, block=False)

                self._queues = collections.OrderedDict()
                self._lastqueue = None

    def cancel(self):
        with self._mutex:
            if self._queues:
                # stop processing pending items
                for queue in list(self._queues.values()):
                    queue.cancel()
                    queue.put_first(FuzzItem(FuzzType.CANCEL))

                # wait for cancel to be processed
                self.join()

                # send None to stop (almost nicely)
                self.cleanup()

    def get_stats(self):
        stat_list = []

        for queue in list(self._queues.values()):
            stat_list = stat_list + list(queue.get_stats().items())

        return dict(stat_list)
