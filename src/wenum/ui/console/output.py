from __future__ import print_function

import math
import string
import operator
from functools import reduce

from six import StringIO

from itertools import zip_longest





def wrap_always_list(alltext: str, width: int) -> list[str]:
    """Function to format the text. Takes the current string with its newlines,
    and further splits the lines that have more characters than the width provided"""
    text_list = []
    # for each line of the text
    for text in alltext.splitlines():
        for subtext in [
            text[width * i: width * (i + 1)]
            # int(math.ceil(1.0 * len(text) / width)) returns the amount of lines needed to display the line
            for i in range(int(math.ceil(1.0 * len(text) / width)))
        ]:
            text_list.append(
                "".join(
                    [char if char in string.printable else "." for char in subtext])
            )
    return text_list
