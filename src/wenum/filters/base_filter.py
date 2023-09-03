from abc import ABC, abstractmethod


class BaseFilter(ABC):
    """
    Base class for Filters
    """

    def __init__(self):
        pass

    @abstractmethod
    def is_filtered(self, fuzz_result) -> bool:
        """
        Check if the fuzz_result should be filtered out.

        Returns True if it should be, and False if not.
        """
        raise NotImplementedError
