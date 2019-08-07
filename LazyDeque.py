#! /usr/bin/env python
# vim: set encoding=utf-8

"""
LazyDeque is a buffer-like wrapper for any iterable object. It allows for a
limited lookahead by caching some elements from the original source.
"""

from collections import deque


class LazyDeque(object):
    """
    Wrapper around collections.deque that loads data from source only when
    needed. This makes it possible to work with input of unknown length.
    """
    def __init__(self, iterable, maxlen):
        """
        Create new LazyDeque.
        """
        self.source = iterable
        self.maxlen = maxlen
        self.items = deque(list(), maxlen)

        for item in iterable:
            self.append(item)
            if len(self.items) == maxlen:
                break

    def __len__(self):
        return len(self.items)

    def append(self, item):
        """Add an element to the end of the deque."""
        self.items.append(item)

    def popmany(self, n):
        """Pop `n` tokens from the deque and return a list."""
        return [next(self) for _ in range(n)]

    def __getitem__(self, idx):
        if isinstance(idx, int):
            return self.items[idx]
        if isinstance(idx, slice):
            toks = []
            for i in range(idx.start or 0,
                           idx.stop or len(self.items),
                           idx.step or 1):
                toks.append(self.items[i])
            return toks
        raise TypeError('__getitem__ expected integer or slice, got %s'
                        % type(idx))

    def __iter__(self):
        return iter(self.items)

    def next(self):
        """Get first element from the deque or raise StopIteration."""
        if len(self.items) == 0:
            raise StopIteration
        popped = self.items.popleft()
        try:
            self.append(next(self.source))
        except StopIteration:
            pass
        return popped

    def has_word(self, word):
        """Check if there is a given word already cached."""
        return len([1 for i in self.items if i.word == word]) != 0
