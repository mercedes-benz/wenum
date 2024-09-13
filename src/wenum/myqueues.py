from __future__ import annotations

import logging
import queue
import time
from typing import TYPE_CHECKING

from typing import Optional

from .exception import FuzzHangError

if TYPE_CHECKING:
    from .runtime_session import FuzzSession
from abc import ABC, abstractmethod

from queue import PriorityQueue
from threading import Lock, Thread, Event, Timer
from .fuzzobjects import FuzzError, FuzzType, FuzzItem, FuzzStats


class FuzzPriorityQueue(PriorityQueue):
    """
    PriorityQueue with respecting priorities without actually returning the priority when getting items.
    Is designed to work with FuzzItem objects only.
    """
    def __init__(self, maxsize=0):
        PriorityQueue.__init__(self, maxsize)

        self.max_prio = 0

    def _put_priority(self, prio, item: FuzzItem, block, timeout=None):
        # max_prio gets updated every time this is called, to track the highest value (which is the lowest prio)
        self.max_prio = max(prio, self.max_prio)
        PriorityQueue.put(self, (prio, item), block, timeout=timeout)

    def put(self, item: FuzzItem, block=True, timeout=None):
        self._put_priority(item.priority, item, block, timeout)

    def put_important(self, item: FuzzItem, block=True):
        """
        Enqueue with the highest priority
        """
        self._put_priority(0, item, block)

    def put_unimportant(self, item: FuzzItem, block=True):
        """
        Enqueue with least priority
        """
        self._put_priority(self.max_prio + 1, item, block)

    def put_unimportant_within_seed(self, item: FuzzItem, block=True):
        """
        Put into the queue with the least priority within the same seed. New seeds go in steps of 10.
        Meaning: Seed 1 -> Prio 10. Seed 2 -> Prio 20
        """
        self._put_priority(item.priority + 9, item, block)

    def get(self, block=True, timeout=None):
        prio, item = PriorityQueue.get(self, block=block, timeout=timeout)

        return item


class FuzzQueue(FuzzPriorityQueue, Thread, ABC):
    def __init__(self, session: FuzzSession, queue_out=None, maxsize=0):
        FuzzPriorityQueue.__init__(self, maxsize)
        self.queue_out: Optional[FuzzQueue] = queue_out
        # Next queue in line that intends to process discarded fuzz_results
        self.queue_discard: Optional[FuzzQueue] = None
        self.child_queue: bool = False
        self.syncqueue: Optional[MonitorQueue] = None
        # Indicates whether the queue wants to process discarded fuzzresults
        self.process_discarded: bool = False

        self.stats: FuzzStats = session.compiled_stats
        self.session: FuzzSession = session
        self.logger = logging.getLogger("debug_log")
        # Signals to the QueueManager that a stop event has been registered by the queue
        self.stopped: Event = Event()
        self.stopped.clear()

        # Signals to the QueueManager that the queue has finished processing all items
        self.ended: Event = Event()
        self.ended.clear()
        # Event after which the queue will end once registered
        self.close: Event = Event()

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
        Override if needed. Will be called by the queue right before \
        signalling to the main thread that it stopped processing items.
        """
        pass

    def cleanup(self):
        """
        This will be called by the queue after it stopped, either due to a cancelling during runtime (e.g. CTRL + C)
        or simply because everything is done.
        """
        pass

    def pre_start(self):
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
        self.pre_start()
        self.start()

    def send_important(self, item):
        """
        Send with the highest priority
        """
        self.queue_out.put_important(item)

    def send_unimportant(self, item):
        """
        Send with the lowest priority
        """
        self.queue_out.put_unimportant(item)

    def send_unimportant_within_seed(self, item):
        """
        Send with the lowest priority within the same seed's priority
        """
        self.queue_out.put_unimportant_within_seed(item)

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
        FuzzPriorityQueue.join(self)

    def _throw(self, exception_message):
        self.logger.error(f"Exception thrown: {exception_message}")
        self.syncqueue.put_important(FuzzError(exception_message))

    def get_stats(self) -> dict:
        """Returns a dict with the queue name and the amount of items in it"""
        return {self.get_name(): self.qsize()}

    def run(self):
        """
        This is the main loop for most queues, which will call the process()-function
        for payloads that should be processed
        """

        while 1:
            # Items are designated to always be FuzzItems
            item: FuzzItem = self.get()
            try:
                if item.item_type == FuzzType.STOP:
                    self.cancel()
                    self.stopped.set()
                    self.logger.debug(f"{self.name} stopped")
                    self.close.wait()
                    break
                elif item.item_type == FuzzType.STARTSEED:
                    self.stats.mark_start()
                elif item.item_type == FuzzType.ENDSEED:
                    if not self.child_queue:
                        self.send_unimportant_within_seed(item)
                    self.task_done()
                    continue
                if (not hasattr(item, 'exception') or item.exception is None) and item.item_type in self.items_to_process():
                    self.process(item)
                # Send the item without processing
                else:
                    self.send(item)
                self.task_done()
            except Exception as e:
                self.task_done()
                self._throw(e)
        self.empty_queue()
        self.cleanup()
        # The last task done should be sent after cleaning up, to ensure QueueManager only
        # joins after the cleanup is finished
        self.task_done()

    def empty_queue(self):
        """
        Empties the queued items right before stopping the runtime
        """
        while self.qsize() > 0:
            self.get()
            self.task_done()


class MonitorQueue(FuzzQueue):
    """
    Queue which is close to last destination of every fuzzitem,
    always present when wenum runs. Tracks processing of requests/responses and monitors when to end the runtime
    """
    def __init__(self, session, queue_out):
        super().__init__(session, queue_out)
        self.process_discarded = True
        self.hang_timer = None
        self.mutex_timer = Lock()

    def get_name(self):
        return "MonitorQueue"

    def process(self, item):
        pass

    def _throw(self, exception_message):
        self.logger.error(f"Exception thrown: {exception_message}")
        self.queue_out.put_important(FuzzError(exception_message))

    def reset_timer(self):
        with self.mutex_timer:
            if self.hang_timer is not None:
                self.hang_timer.cancel()
            self.hang_timer = Timer(60, self._throw, args=[FuzzHangError("Queue hang detected. Stopping runtime")])
            self.hang_timer.start()

    def run(self):

        while 1:
            item = self.get()
            self.reset_timer()

            try:
                if item.item_type == FuzzType.STOP:
                    self.hang_timer.cancel()
                    self.logger.debug(f"MonitorQueue: Stopping")
                    self.stopped.set()
                    self.close.wait()
                    break

                elif item.item_type == FuzzType.ERROR:
                    self.send_important(item)
                    self.task_done()
                    continue

                if item.item_type == FuzzType.RESULT and not item.discarded:
                    self.stats.update_subdirectory_hits(fuzz_result=item)
                    self.send(item)

                if item.item_type == FuzzType.ENDSEED:
                    # Only dec pending seeds if not already ended
                    if not self.ended.is_set():
                        self.ended.set()
                        self.stats.pending_seeds.dec()
                elif item.item_type == FuzzType.RESULT:
                    self.stats.processed.inc()
                    self.stats.pending_fuzz.dec()
                    if item.discarded:
                        self.stats.filtered.inc()

                # If no requests are left, trigger the ending routine
                if self.stats.pending_fuzz() <= 0 and self.stats.pending_seeds() <= 0:
                    self.send_important(FuzzItem(FuzzType.STOP))
                    self.logger.debug("MonitorQueue - No remaining requests left. Sending a stop item")
                self.task_done()

            except Exception as e:
                self.task_done()
                self._throw(e)
        self.empty_queue()
        self.cleanup()
        # The last task done should be sent after cleaning up, to ensure QueueManager only
        # joins after the cleanup is finished
        self.task_done()


class FuzzListQueue(FuzzQueue, ABC):
    """
    Queue with a list of output queues.
    Instead of the "parent" A sending every item to the queue_out Z like an ordinary FuzzQueue,
    it may choose to send items to all their children [B, C, D],
    or randomly to one of their children, e.g. only to C.
    The children respectively have queue_out Z as their next queue.
    The children are not managed by QueueManager. FuzzListQueue needs to cascade information to them instead.

    If the FuzzListQueue doesn't need to process discarded items but its children should do so, the parent should
    forward the items in the process() method with send_to_any()/send_to_all(), depending on the current use case.
    """
    def __init__(self, session, queues_out: list[FuzzQueue], maxsize=0):
        super().__init__(session=session, maxsize=maxsize)
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
            q.pre_start()
            q.start()
        self.start()

    def run(self):
        """
        This is the main loop for most queues, which will call the process()-function
        for payloads that should be processed
        """

        while 1:
            item: FuzzItem = self.get()
            try:
                if item.item_type == FuzzType.STOP:
                    # Propagate stopping the main loop to children
                    for child in self.queues_out:
                        child.cancel()
                    self.send_important_to_all(FuzzItem(FuzzType.STOP))
                    for child in self.queues_out:
                        child.stopped.wait()
                    self.logger.debug(f"{self.name} stopped")
                    self.stopped.set()

                    self.close.wait()
                    # Join all children
                    for child in self.queues_out:
                        child.close.set()
                    for child in self.queues_out:
                        child.join()

                    break
                elif item.item_type == FuzzType.STARTSEED:
                    self.stats.mark_start()
                elif item.item_type == FuzzType.ENDSEED:
                    self.send_unimportant_within_seed_to_all(item)
                    self.send_unimportant(item)
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
        self.empty_queue()
        self.cleanup()
        # The last task done should be sent after cleaning up, to ensure QueueManager only
        # joins after the cleanup is finished
        self.task_done()

    def send_important_to_all(self, item):
        """
        Send to all children with the highest priority
        """
        for q in self.queues_out:
            q.put_important(item)

    def send_unimportant_to_all(self, item):
        """
        Send to all children with the least priority
        """
        for q in self.queues_out:
            q.put_unimportant(item)

    def send_unimportant_within_seed_to_all(self, item):
        """
        Send to all children with the least priority within the seed priority
        """
        for q in self.queues_out:
            q.put_unimportant_within_seed(item)

    def send_to_all(self, item):
        """
        Send to all children
        """
        for q in self.queues_out:
            q.put(item)

    def send_to_any(self, item):
        """
        Randomly send to one in the list
        """
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

    def next_queue(self, nextq):
        """
        Set the queue_out for the parent and the outlist to nextq
        """
        self.queue_out = nextq
        for queue_out in self.queues_out:
            queue_out.next_queue(nextq)

    def set_next_discard_queue(self, next_discard_queue):
        """
        Set the queue_discard for the parent and
        """
        self.queue_discard = next_discard_queue
        for child in self.queues_out:
            child.queue_discard = next_discard_queue

    def get_stats(self) -> dict:
        """
        Creating stats for the queue itself, and it's list of out queues. Returns a dict with the key being the name
        of the queue and value the amount of items in the queue.
        """
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

