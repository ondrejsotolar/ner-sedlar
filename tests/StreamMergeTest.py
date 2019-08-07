#! /usr/bin/env python
# vim: set encoding=utf-8

import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')

from Streams import merge
from Token import Token
from detectors.base import NamedEntity


def main(verbosity):
    """Try to merge two streams, result must contain all tokens."""
    e1 = NamedEntity("a b c", None, None, None)
    e1.set_position(1)

    e2 = NamedEntity("a b", None, None, None)
    e2.set_position(1)

    e3 = NamedEntity('d e f', None, None, None)
    e3.whitespace = ' '
    e3.set_position(7)

    e4 = NamedEntity('c d e f', None, None, None)
    e4.whitespace = ' '
    e4.set_position(5)

    e5 = NamedEntity('g h i j k l', None, None, None)
    e5.whitespace = ' '
    e5.set_position(13)

    t1 = Token('KONEC', ' ', 25)

    s1 = [e1, e3, e5, t1]
    s2 = [e2, e4, e5, t1]

    expected = 'a b c d e f g h i j k l KONEC'
    result = []

    for t in merge((iter(s1), iter(s2)), level=verbosity):
        result.append(t.word)

    if ' '.join(result) != expected:
        print 'FAIL'
    else:
        print 'OK'

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main(logging.DEBUG if '-v' in sys.argv else logging.WARNING)
