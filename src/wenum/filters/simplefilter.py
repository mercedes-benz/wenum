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
    def from_options(options):
        ffilter = FuzzResSimpleFilter()

        try:
            if options.sr is not None:
                ffilter.hideparams["regex_show"] = True
                ffilter.hideparams["regex"] = re.compile(
                    options.sr, re.MULTILINE | re.DOTALL
                )

            elif options.hr is not None:
                ffilter.hideparams["regex_show"] = False
                ffilter.hideparams["regex"] = re.compile(
                    options.hr, re.MULTILINE | re.DOTALL
                )
        except Exception as e:
            raise FuzzExceptBadOptions(
                "Invalid regex expression used in filter: %s" % str(e)
            )

        if options.sc_list or options.sw_list or options.ss_list or options.sl_list:
            ffilter.hideparams["codes_show"] = True
            ffilter.hideparams["codes"] = options.sc_list
            ffilter.hideparams["words"] = options.sw_list
            ffilter.hideparams["lines"] = options.sl_list
            ffilter.hideparams["chars"] = options.ss_list
        elif options.hc_list or options.hw_list or options.hs_list or options.hl_list:
            ffilter.hideparams["codes_show"] = False
            ffilter.hideparams["codes"] = options.hc_list
            ffilter.hideparams["words"] = options.hw_list
            ffilter.hideparams["lines"] = options.hl_list
            ffilter.hideparams["chars"] = options.hs_list

        #if [x for x in ["sc", "sw", "sh", "sl"] if len(options[x]) > 0]:
        #    ffilter.hideparams["codes_show"] = True
        #    ffilter.hideparams["codes"] = options["sc"]
        #    ffilter.hideparams["words"] = options["sw"]
        #    ffilter.hideparams["lines"] = options["sl"]
        #    ffilter.hideparams["chars"] = options["sh"]
        #elif [x for x in ["hc", "hw", "hh", "hl"] if len(options[x]) > 0]:
        #    ffilter.hideparams["codes_show"] = False
        #    ffilter.hideparams["codes"] = options.hc_list
        #    ffilter.hideparams["words"] = options["hw"]
        #    ffilter.hideparams["lines"] = options["hl"]
        #    ffilter.hideparams["chars"] = options["hh"]

        return ffilter
