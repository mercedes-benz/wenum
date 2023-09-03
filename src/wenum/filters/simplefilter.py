from typing import Optional

from ..exception import FuzzExceptBadOptions
from wenum.filters.base_filter import BaseFilter

import re


class FuzzResSimpleFilter(BaseFilter):
    """
    Filter class triggered when options such as --hc 404 are used on the cli.
    """
    def __init__(self):
        super().__init__()
        self.show_identifier: Optional[bool] = None
        self.hide_identifier: Optional[bool] = None
        self.show_regex: Optional[bool] = None
        self.hide_regex: Optional[bool] = None
        self.codes: list[int] = []
        self.words: list[int] = []
        self.lines: list[int] = []
        self.chars: list[int] = []
        # Previously referred to as "chars"
        self.size: list[int] = []
        self.regex: Optional[re.Pattern] = None

    def is_filtered(self, fuzz_result):
        # Check if the response should be filtered according to the identifiers (hide words, show lines, etc.)
        if self.show_identifier:
            # Filter out if not in show identifiers
            if (
                    fuzz_result.code in self.codes
                    or fuzz_result.lines in self.lines
                    or fuzz_result.words in self.words
                    or fuzz_result.chars in self.size
            ):
                filtered_via_identifier = False
            else:
                filtered_via_identifier = True
        elif self.hide_identifier:
            # Filter out if in hide identifiers
            if (
                    fuzz_result.code in self.codes
                    or fuzz_result.lines in self.lines
                    or fuzz_result.words in self.words
                    or fuzz_result.chars in self.size
            ):
                filtered_via_identifier = True
            else:
                filtered_via_identifier = False
        else:
            filtered_via_identifier = False

        if self.show_regex:
            # Filter if not found in regex
            if self.regex.search(fuzz_result.history.content):
                filtered_via_regex = False
            else:
                filtered_via_regex = True
        elif self.hide_regex:
            # Filter if found in regex
            if self.regex.search(fuzz_result.history.content):
                filtered_via_regex = True
            else:
                filtered_via_regex = False
        else:
            filtered_via_regex = False

        return filtered_via_identifier or filtered_via_regex

    @staticmethod
    def from_options(session):
        """
        Builds Filter from user options.

        Returns None if no filter options have been set.
        """
        ffilter = FuzzResSimpleFilter()

        try:
            if session.options.sr:
                ffilter.show_regex = True
                ffilter.regex = re.compile(
                    session.options.sr, re.MULTILINE | re.DOTALL
                )

            elif session.options.hr:
                ffilter.hide_regex = True
                ffilter.regex = re.compile(
                    session.options.hr, re.MULTILINE | re.DOTALL
                )
        except Exception as e:
            raise FuzzExceptBadOptions(
                "Invalid regex expression used in filter: %s" % str(e)
            )

        if session.options.sc_list or session.options.sw_list or session.options.ss_list or session.options.sl_list:
            ffilter.show_identifier = True
            ffilter.codes = session.options.sc_list
            ffilter.words = session.options.sw_list
            ffilter.lines = session.options.sl_list
            ffilter.size = session.options.ss_list
        elif session.options.hc_list or session.options.hw_list or session.options.hs_list or session.options.hl_list:
            ffilter.hide_identifier = True
            ffilter.codes = session.options.hc_list
            ffilter.words = session.options.hw_list
            ffilter.lines = session.options.hl_list
            ffilter.size = session.options.hs_list

        if ffilter.show_regex or ffilter.hide_regex or ffilter.show_identifier or ffilter.hide_identifier:
            return ffilter
        else:
            return None
