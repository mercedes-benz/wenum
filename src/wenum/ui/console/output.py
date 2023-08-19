from __future__ import print_function

import math
import string
import operator
from functools import reduce

from six import StringIO

from itertools import zip_longest


def indent(
        rows,
        hasHeader=False,
        headerChar="-",
        delim=" | ",
        justify="left",
        separateRows=False,
        prefix="",
        postfix="",
        wrapfunc=lambda x: x,
):
    """
    @author http://code.activestate.com/recipes/267662-table-indentation/

    Indents a table by column.
    - rows: A sequence of sequences of items, one sequence per row.
    - hasHeader: True if the first row consists of the columns' names.
    - headerChar: Character to be used for the row separator line
        (if hasHeader==True or separateRows==True).
    - delim: The column delimiter.
    - justify: Determines how are data justified in their column.
        Valid values are 'left','right' and 'center'.
    - separateRows: True if rows are to be separated by a line
        of 'headerChar's.
    - prefix: A string prepended to each printed row.
    - postfix: A string appended to each printed row.
    - wrapfunc: A function f(text) for wrapping text; each element in
        the table is first wrapped by this function."""

    # closure for breaking logical rows to physical, using wrapfunc
    def rowWrapper(row):
        newRows = [wrapfunc(item).split("\n") for item in row]
        return [[substr or "" for substr in item] for item in zip_longest(*newRows)]

    # break each logical row into one or more physical ones
    logicalRows = [rowWrapper(row) for row in rows]
    # columns of physical rows
    columns = zip_longest(*reduce(operator.add, logicalRows))
    # get the maximum of each column by the string length of its items
    maxWidths = [max([len(str(item)) for item in column]) for column in columns]
    rowSeparator = headerChar * (
            len(prefix) + len(postfix) + sum(maxWidths) + len(delim) * (len(maxWidths) - 1)
    )
    # select the appropriate justify method
    justify = {"center": str.center, "right": str.rjust, "left": str.ljust}[
        justify.lower()
    ]
    output = StringIO()
    if separateRows:
        print(rowSeparator, file=output)
    for physicalRows in logicalRows:
        for row in physicalRows:
            print(
                prefix
                + delim.join(
                    [justify(str(item), width) for (item, width) in zip(row, maxWidths)]
                )
                + postfix,
                file=output,
            )
        if separateRows or hasHeader:
            print(rowSeparator, file=output)
            hasHeader = False
    return output.getvalue()


def wrap_always(text, width):
    """A simple word-wrap function that wraps text on exactly width characters.
    It doesn't split the text in words."""
    return "\n".join(
        [
            text[width * i: width * (i + 1)]
            for i in range(int(math.ceil(1.0 * len(text) / width)))
        ]
    )


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


def table_print(rows, width=80):
    print(
        indent(
            rows,
            hasHeader=True,
            separateRows=False,
            prefix="  ",
            postfix="  ",
            wrapfunc=lambda x: wrap_always(x, width),
        )
    )
