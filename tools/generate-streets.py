#! /usr/bin/env python
# vim: set encoding=utf-8

import sys

PAIRS = {(u'nábř', u'nábřeží'), (u'nám', u'náměstí'), (u'zah', u'zahrady')}

for line in sys.stdin:
    line = line.decode('utf8').strip()
    print line.encode('utf8')

    for (s, l) in PAIRS:
        if line.lower().endswith(s + u'.'):
            stem = line[:-(len(s) + 1)]
            print (stem + l).encode('utf8')
            print (stem + l[0].upper() + l[1:]).encode('utf8')

        if line.lower().endswith(l):
            stem = line[:-len(l)]
            print (stem + s + u'.').encode('utf8')
            print (stem + s).encode('utf8')
            print (stem + s[0].upper() + s[1:] + u'.').encode('utf8')
            print (stem + s[0].upper() + s[1:]).encode('utf8')
