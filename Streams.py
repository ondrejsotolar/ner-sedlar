#! /usr/bin/env python
# vim: set encoding=utf-8

"""
This module exports various functions that deal with streams of tokens and
entities.
"""

import logging
import sys
import detectors.base as ner
from LazyDeque import LazyDeque


def markable_sink(inp):
    """
    Consume tokens from stream and print them to standard output. Named
    entities will be printed as markable SGML output.
    """
    for t in inp:
        sys.stdout.write(t.to_markable().encode('utf8'))


def collector_filter(inp):
    """
    Filter stream to only yield entities.
    """
    for t in inp:
        if isinstance(t, ner.NamedEntity):
            yield t


def html_sink(inp, escape):
    """
    Create HTML document from input tokens. The second argument should be a
    function that HTML escapes the strings.
    """
    return ''.join([t.to_html(escape) for t in inp])


def unitok_sink(inp):
    """
    Print one token one a line with glue iff token has no preceding whitespace.
    """
    first = True
    for t in inp:
        if not first and not t.whitespace:
            print '<g/>'
            first = False
        print t.word


def json_sink(inp):
    """
    Create a JSON list with each entity as an object. Returns a UTF-8 encoded
    string.
    """
    return '[\n%s\n]' % ',\n'.join(t.to_json() for t in collector_filter(inp))


def take_current(streams, pos):
    """Take first item from each stream, if its position is pos."""

    def can_take(it):
        """Return True iff first item in iterator starts at pos."""
        return len(it) > 0 and it[0].position == pos

    found = enumerate([it.next() if can_take(it) else None for it in streams])
    return [p for p in found if p[1]]


def merge(iterables, level=logging.WARNING):
    """
    Merge streams from detectors into a single stream. On each position, the
    longest entity available is taken. However, it is not optimal in that if
    there is a two token entity preceding a longer one in another stream, the
    first one will be taken.

        + + + + + + +
        + --- + + + +   <- taken
        + + ------- +   <- skipped

    """

    def order_entity_key(pair):
        """Longest entity first, then prefer ones with lemmata."""
        return len(pair[1].word), pair[1].weight, pair[1].attrs['lemma']

    logger = logging.getLogger('Streams.merge')
    logger.setLevel(level)
    buffered = [LazyDeque(it, 1) for it in iterables]
    current_pos = 0

    while any(len(it) > 0 for it in buffered):
        logger.debug('Current position: %d', current_pos)
        current = take_current(buffered, current_pos)
        logger.debug('Got tuple %r', current)
        if len(current) == 0:
            current_pos += 1
            continue
        entities = [t for t in current
                    if isinstance(t[1], ner.NamedEntity)]
        if len(entities) == 0:
            logger.debug('No entity here')
            yield current[0][1]
            current_pos = current[0][1].position + len(current[0][1].word)
        else:
            longest = max(entities, key=order_entity_key)
            logger.debug('Longest is %s', longest)
            end_pos = longest[1].position + len(longest[1].word)
            logger.debug('End position is %d', end_pos)
            for (idx, it) in enumerate(buffered):
                if idx == longest[0]:
                    continue
                logger.debug('Skipping in stream %d', idx)
                while len(it) > 0 and it[0].position < end_pos:
                    item = next(it)
                    logger.debug('Skipping an item %r', item)
            yield longest[1]
            current_pos = end_pos
