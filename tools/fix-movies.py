#! /usr/bin/env python
# vim: set encoding=utf-8

"""
If the movie name starts with a determiner, it is placed at the end of the
name. This script tries to fix that by actually moving the determiner to the
front.

The script reads movies from stdin one line at a time. If the name does not
need any fixing, it printed to stdout without any change. Otherwise both the
original name and the fixed one is printed.

The HTML entities are also replaced by the actual characters.
"""

import sys
import re

# Store suffixes and whether they should be followed by a space.
PREPS = [(u'al-', False), (u'A', True), (u'An', True), (u'An', True),
         (u'Das', True), (u'De', True), (u'Der', True), (u'Det', True),
         (u'Die', True), (u'El', True), (u'I', True), (u'Il', True),
         (u'L\'', False), (u'La', True), (u'Le', True), (u'Les', True),
         (u'Los', True), (u'The', True), (u'Un', True)]

ENTITIES = [('&amp;', '&'), ('&gt', '>'), ('&quot', '"')]

for line in sys.stdin:
    line = line.decode('utf8').strip()
    for (entity, replacement) in ENTITIES:
        line = line.replace(entity, replacement)
    print line.encode('utf8')
    for (prep, space) in PREPS:
        if re.search(u', %s$' % prep, line, re.UNICODE | re.IGNORECASE):
            parts = line.split(',')
            sep = ' ' if space else ''
            result = parts[-1] + sep + ','.join(parts[:-1])
            print result.strip().encode('utf8')
