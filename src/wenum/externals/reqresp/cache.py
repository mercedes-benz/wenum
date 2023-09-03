from collections import defaultdict

from wenum.fuzzrequest import FuzzRequest


class HttpCache:
    """
    The cache keeps track of all the requests that have already been enqueued, to avoid doing it multiple times.
    """
    db = None

    def __init__(self):
        # cache control, a dictionary with URLs as keys and their values being lists full of the
        # categories that the queries were categorized as
        self.__cache_map = defaultdict(list)
        # This should be relevant for loading the cache from file. Needs to be documented more
        # thoroughly
        self.__object_map = defaultdict(list)

    def check_cache(self, url_key: str, cache_type: str = "processed", update: bool = True) -> bool:
        """
        Checks if the URL is in the cache, usually to avoid queueing the same URL a second time.

        The category of the request is relevant (default: "processed").
        If '/robots.txt, init_request' exists in the cache,
        the new request won't count as cached if it is checked against '/robots.txt, seed'.

        if the update bool is True (default), the function will also add the key to the cache if it did not exist yet.

        Returns True if it was in the cache.
        Returns False if it was not in the cache.
        """
        if url_key in self.__cache_map and cache_type in self.__cache_map[url_key]:
            cached = True
        else:
            cached = False
        if update:
            self.__cache_map[url_key].append(cache_type)
        return cached
