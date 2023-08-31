from .iterators import BaseIterator


class TupleIt(BaseIterator):
    def __init__(self, parent):
        self.parent = parent

    def count(self):
        return self.parent.count()

    def width(self):
        return 1

    def payloads(self):
        return [self.parent]

    def next_word(self):
        return (next(self.parent),)

    def __next__(self):
        return self.next_word()
