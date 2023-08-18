import os.path
import pickle
from collections import defaultdict

from wfuzz.fuzzrequest import FuzzRequest


class HttpCache:
    db = None

    def __init__(self):
        # cache control, a dictionary with URLs as keys and their values being lists full of the
        # categories that the queries were categorized as
        self.__cache_map = defaultdict(list)
        self.es = None
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

    def get_object_from_object_cache(self, fuzz_result, key=False):
        """
        Return entry in object_cache based on fuzzresult or key if provided (function for --cache-file option)
        """
        if key is False:
            key = fuzz_result.history.to_cache_key()
        if key in self.__object_map:
            return self.__object_map[key]
        if not self.db:
            return None
        res = self.db.get(key.encode("UTF-8"))
        if not res:
            return None
        obj = pickle.loads(res)

        return [obj]

    def load_cache_from_file(self, filename):
        """
        EXPERIMENTAL: Loading cache from a cache file on startup
        """
        if not os.path.isfile(filename):
            return

        with open(filename, "rb") as pkl_handle:
            self.__object_map = pickle.load(pkl_handle)
