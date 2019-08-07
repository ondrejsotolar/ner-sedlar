#! /usr/bin/env python
# vim: set encoding=utf-8

"""
This module provides abstract class for all items in streams.
"""


class StreamItem(object):
    """Base class for all items in token/entity streams."""
    def __init__(self):
        self.should_tag = False
        self.word = ''
        self.whitespace = ''
        self.position = 0

    def taggable(self):
        """Whether a category can be added."""
        return self.should_tag
