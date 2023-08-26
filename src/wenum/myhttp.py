from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from urllib.parse import urlparse

if TYPE_CHECKING:
    from wenum.options import FuzzSession
import pycurl
from io import BytesIO
from threading import Thread, Lock
import itertools
from queue import Queue
import copy
import datetime
import pytz as pytz

from .exception import FuzzExceptBadOptions, FuzzExceptNetError
from .fuzzobjects import FuzzResult
from dateutil.parser import parse

from .factories.reqresp_factory import ReqRespRequestFactory

# See https://curl.haxx.se/libcurl/c/libcurl-errors.html
UNRECOVERABLE_PYCURL_EXCEPTIONS = [
    28,  # Operation timeout. The specified time-out period was reached according to the conditions.
    7,  # Failed to connect() to host or proxy.
    6,  # Couldn't resolve host. The given remote host was not resolved.
    5,  # Couldn't resolve proxy. The given proxy host could not be resolved.
]

# Other common pycurl exceptions:
# Exception in perform (35, 'error:0B07C065:x509 certificate routines:X509_STORE_add_cert:cert already in hash table')
# Exception in perform (18, 'SSL read: error:0B07C065:x509 certificate routines:X509_STORE_add_cert:cert already in hash table, errno 11')

MAX_AGE = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=30)


class HttpPool:
    newid = itertools.count(0)

    def __init__(self, options):
        self.processed = 0

        self.exit_job = False
        self.mutex_stats = Lock()

        # CurlMulti object to which active curl handles will be added to (and removed once done)
        self.curl_multi: Optional[pycurl.CurlMulti] = None
        # List of all the handle objects instances used during runtime (can be adjusted by -t option)
        self.handles: list[pycurl.Curl] = []
        # List of all the curl handles that are not actively used at the moment
        self.curlh_freelist: list[pycurl.Curl] = []
        # Queue object storing all the requests available for sending out. Maxsize avoids buffering tens of thousands of
        # requests beforehand, which would result in gigabytes of reserved memory
        self.request_queue: Queue = Queue(maxsize=options.get("concurrent"))

        # List containing the threads
        # TODO This list seems to only contain a single thread. Refactor into a single thread attribute?
        self.threads = None

        self.pool_map = {}

        self.options: FuzzSession = options
        self.cache = self.options.cache

        self._registered = 0
        # Amount of total requests that have been queued. This is not a "remaining" requests counter
        self.queued_requests = 0

    def _initialize(self):
        # pycurl Connection pool
        self.curl_multi = pycurl.CurlMulti()
        self.handles = []

        for i in range(self.options.get("concurrent")):
            curl_h = pycurl.Curl()
            self.handles.append(curl_h)
            self.curlh_freelist.append(curl_h)

        # create threads
        self.threads = []

        function_name = "_read_multi_stack"
        th = Thread(target=getattr(self, function_name))
        th.name = function_name
        self.threads.append(th)
        th.start()

    def job_stats(self):
        """
        Return stats
        """
        with self.mutex_stats:
            dic = {
                "Requests enqueued": self.queued_requests,
                "Responses received": self.processed,
            }
        return dic

    def iter_results(self, poolid):
        """
        Method to receive the next item in the queue storing the results of all the requests sent
        """
        queue_output = self.pool_map[poolid]["queue"].get()
        if not queue_output:
            return
        item = queue_output[0]
        requeue = queue_output[1]

        yield item, requeue

    def _new_pool(self):
        poolid = next(self.newid)
        self.pool_map[poolid] = {}
        # This queue stores the results of the requests sent
        self.pool_map[poolid]["queue"] = Queue()
        self.pool_map[poolid]["proxy"] = None

        if self.options.proxy_list:
            self.pool_map[poolid]["proxy"] = self._get_next_proxy(
                self.options.proxy_list
            )

        return poolid

    def _prepare_curl_h(self, curl_h, fuzzres, poolid):
        """
        Set up curl handle again for another request
        """
        new_curl_h = ReqRespRequestFactory.to_http_object(fuzzres.history, curl_h)
        new_curl_h = self._set_extra_options(new_curl_h, fuzzres, poolid)

        new_curl_h.response_queue = (BytesIO(), BytesIO(), fuzzres, poolid)
        new_curl_h.setopt(pycurl.WRITEFUNCTION, new_curl_h.response_queue[0].write)
        new_curl_h.setopt(pycurl.HEADERFUNCTION, new_curl_h.response_queue[1].write)

        return new_curl_h

    def enqueue(self, fuzz_result: FuzzResult, poolid):
        """
        This method is called by HttpQueue. Puts a request object into request_queue, which is processed by a
        separate thread actually sending and receiving the requests.
        It is important that enqueue is not called by the thread handling the requests, because it can deadlock if
        the queue is full while trying to append more.
        """
        if self.exit_job:
            return
        # Bool indicating whether the request should be queued for request again. Useful for exceptions
        requeue = False

        with self.mutex_stats:
            self.queued_requests += 1
        self.request_queue.put((fuzz_result, poolid))

    @staticmethod
    def _discard_cached(fuzzres: FuzzResult) -> str:
        """
        Method to evaluate detected endpoints. Returns string describing how to proceed with it
        """
        if fuzzres.history.code in [403, 404]:
            return 'discard'
        if fuzzres.history.code == 200:
            if fuzzres.history.date:
                date = parse(fuzzres.history.date)
                if date > MAX_AGE:
                    return "discard"
            return "queue"

        return "cache"

    def _stop_to_pools(self):
        for p in list(self.pool_map.keys()):
            self.pool_map[p]["queue"].put(None)

    def cleanup(self):
        self.exit_job = True
        for th in self.threads:
            th.join()

    def register(self):
        with self.mutex_stats:
            self._registered += 1

        if not self.pool_map:
            self._initialize()

        return self._new_pool()

    def deregister(self):
        with self.mutex_stats:
            self._registered -= 1

        if self._registered <= 0:
            self.cleanup()

    @staticmethod
    def _get_next_proxy(proxy_list):
        i = 0
        while 1:
            yield proxy_list[i]
            i += 1
            i = i % len(proxy_list)

    def _set_extra_options(self, c, fuzzres, poolid):
        if self.pool_map[poolid]["proxy"]:
            proxy = next(self.pool_map[poolid]["proxy"])

            parsed_proxy = urlparse(proxy)

            if parsed_proxy.scheme.lower() == "socks5":
                c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)
                c.setopt(pycurl.PROXY, parsed_proxy.netloc)
            elif parsed_proxy.scheme.lower() == "socks4":
                c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS4)
                c.setopt(pycurl.PROXY, parsed_proxy.netloc)
            else:
                c.setopt(pycurl.PROXY, parsed_proxy.netloc)
        else:
            c.setopt(pycurl.PROXY, "")

        mdelay = self.options.get("req_delay")
        if mdelay is not None:
            c.setopt(pycurl.TIMEOUT, mdelay)

        cdelay = self.options.get("conn_delay")
        if cdelay is not None:
            c.setopt(pycurl.CONNECTTIMEOUT, cdelay)

        return c

    def _process_curl_handle(self, curl_h: pycurl.Curl):
        buff_body, buff_header, res, poolid = curl_h.response_queue
        # Bool indicating whether the request should be queued for request again. Useful for exceptions
        requeue = False

        try:
            ReqRespRequestFactory.from_http_object(
                res.history,
                curl_h,
                buff_header.getvalue(),
                buff_body.getvalue(),
            )
        except Exception as e:
            self.pool_map[poolid]["queue"].put((res.update(exception=e), requeue))
        else:
            # reset type to result otherwise backfeed items will enter an infinite loop
            self.pool_map[poolid]["queue"].put((res.update(), requeue))

        with self.mutex_stats:
            self.processed += 1

    def _process_curl_should_retry(self, fuzz_result: FuzzResult, errno: int, poolid: int):
        """
        Queue failed request another time if it is not considered unrecoverable
        and has not exceeded the maximum retry amount
        """
        if errno in UNRECOVERABLE_PYCURL_EXCEPTIONS or fuzz_result.history.wf_retries >= self.options.get("retries"):
            return False
        # Bool indicating whether the request should be queued for request again. Useful for exceptions
        requeue = True

        fuzz_result.history.wf_retries += 1

        self.pool_map[poolid]["queue"].put((fuzz_result, requeue))
        return True

    def _process_curl_handle_error(self, fuzz_result: FuzzResult, errno, errmsg, poolid):
        """
        Handle unrecoverable failed request
        """
        # Bool indicating whether the request should be queued for request again. Useful for exceptions
        requeue = False
        e = FuzzExceptNetError("Pycurl error %d: %s" % (errno, errmsg))
        fuzz_result.history.totaltime = 0
        # Clearing the response. Otherwise, if the failed request is a recursive one, it would retain the response
        # data from the one before
        fuzz_result.history._request.response = None
        self.pool_map[poolid]["queue"].put((fuzz_result.update(exception=e), requeue))
        with self.mutex_stats:
            self.processed += 1

    def _read_multi_stack(self):
        """
        Check for curl objects which have terminated, and add them to the curlh_freelist
        """
        while not self.exit_job:
            while not self.exit_job:
                ret, num_handles = self.curl_multi.perform()
                if ret != pycurl.E_CALL_MULTI_PERFORM:
                    break

            num_q, ok_list, err_list = self.curl_multi.info_read()

            # Deal with curl handles that have returned successfully
            for curl_h in ok_list:
                self._process_curl_handle(curl_h)
                self.curl_multi.remove_handle(curl_h)
                self.curlh_freelist.append(curl_h)

            # Deal with curl handles that returned errors
            for curl_h, errno, errmsg in err_list:
                buff_body, buff_header, res, poolid = curl_h.response_queue

                if not self._process_curl_should_retry(res, errno, poolid):
                    self._process_curl_handle_error(res, errno, errmsg, poolid)

                self.curl_multi.remove_handle(curl_h)
                self.curlh_freelist.append(curl_h)

            # Put curl handles for sending out requests
            while self.curlh_freelist and not self.request_queue.empty():
                curl_h = self.curlh_freelist.pop()
                fuzzres, poolid = self.request_queue.get()

                self.curl_multi.add_handle(self._prepare_curl_h(curl_h, fuzzres, poolid))

        self._stop_to_pools()

        # cleanup multi stack
        for c in self.handles:
            c.close()
            self.curlh_freelist.append(c)
        self.curl_multi.close()
