from abc import ABC, abstractmethod


class BaseFilter(ABC):
    """
    Base class for Filters
    """

    def __init__(self):
        pass

    @abstractmethod
    def is_active(self):
        """
        Returns the currently active filter condition
        """
        raise NotImplementedError

    @abstractmethod
    def is_visible(self, fuzz_result):
        """
        Check if the fuzz_result should be filtered out
        """
        raise NotImplementedError
