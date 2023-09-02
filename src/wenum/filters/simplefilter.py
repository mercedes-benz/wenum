from ..exception import FuzzExceptBadOptions
from wenum.filters.base_filter import BaseFilter

import re
import collections


class FuzzResSimpleFilter(BaseFilter):
    """
    Filter class triggered when options such as --hc 404 are used on the cli.
    """
    def __init__(self, ffilter=None):
        self.hideparams = dict(
            regex_show=None,
            codes_show=None,
            codes=[],
            words=[],
            lines=[],
            chars=[],
            regex=None,
        )

        if ffilter is not None:
            self.hideparams = ffilter

        self.stack = []

        self._cache = collections.defaultdict(set)

    def is_active(self):
        return any(
            [
                self.hideparams["regex_show"] is not None,
                self.hideparams["codes_show"] is not None,
            ]
        )

    def is_visible(self, res):
        if self.hideparams["codes_show"] is None:
            cond1 = True
        else:
            cond1 = not self.hideparams["codes_show"]

        if self.hideparams["regex_show"] is None:
            cond2 = True
        else:
            cond2 = not self.hideparams["regex_show"]

        if (
            res.code in self.hideparams["codes"]
            or res.lines in self.hideparams["lines"]
            or res.words in self.hideparams["words"]
            or res.chars in self.hideparams["chars"]
        ):
            cond1 = self.hideparams["codes_show"]

        if self.hideparams["regex"]:
            if self.hideparams["regex"].search(res.history.content):
                cond2 = self.hideparams["regex_show"]

        return cond1 and cond2

    @staticmethod
    def from_options(session):
        ffilter = FuzzResSimpleFilter()

        try:
            if session.options.sr is not None:
                ffilter.hideparams["regex_show"] = True
                ffilter.hideparams["regex"] = re.compile(
                    session.options.sr, re.MULTILINE | re.DOTALL
                )

            elif session.options.hr is not None:
                ffilter.hideparams["regex_show"] = False
                ffilter.hideparams["regex"] = re.compile(
                    session.options.hr, re.MULTILINE | re.DOTALL
                )
        except Exception as e:
            raise FuzzExceptBadOptions(
                "Invalid regex expression used in filter: %s" % str(e)
            )

        if session.options.sc_list or session.options.sw_list or session.options.ss_list or session.options.sl_list:
            ffilter.hideparams["codes_show"] = True
            ffilter.hideparams["codes"] = session.options.sc_list
            ffilter.hideparams["words"] = session.options.sw_list
            ffilter.hideparams["lines"] = session.options.sl_list
            ffilter.hideparams["chars"] = session.options.ss_list
        elif session.options.hc_list or session.options.hw_list or session.options.hs_list or session.options.hl_list:
            ffilter.hideparams["codes_show"] = False
            ffilter.hideparams["codes"] = session.options.hc_list
            ffilter.hideparams["words"] = session.options.hw_list
            ffilter.hideparams["lines"] = session.options.hl_list
            ffilter.hideparams["chars"] = session.options.hs_list

        return ffilter
