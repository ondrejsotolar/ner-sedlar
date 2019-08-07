#! /usr/bin/env python
# vim: set encoding=utf-8

"""
Extract entities from CNEC and output a file with each entity on a single line.

Run the output through
    $ sed -e '/\tP\t/d' -e 's/\tW\t/\t?\t/'
to keep only whole entities and replace categories with ?.
"""

import re
import sys
import logging

'''
ENT := '<' CAT CONTENT '>'
CAT := (ALPHA | '_')+
CONTENT := ENT | STRING
'''

def is_category_char(c):
    '''Check if `c` is a character allowed in category.'''
    return c.isalpha() or c == '_' or c == '?'

collected_entities = set()


def emit_entity(pos, typ, text):
    string = '%d\t%d\t%s\t%s' % (pos, len(text), typ, text)
    collected_entities.add(string)


def parse_ent(text, pos, typ='W'):
    """
    Assuming `text` starts with a possibly nested entity, parse it and return
    a tuple (match, offset in text where match starts).
    """
    logging.debug('parse_ent(%s, %d, %s)', text, pos, typ)
    if text[0] != '<':
        raise UserWarning('Entity does not start with "<"')
    idx = 1
    while is_category_char(text[idx]):
        logging.debug('Skipping category [%c]', text[idx])
        idx += 1
    logging.debug('After category skip: %d', idx)

    # Skip space
    if text[idx] == ' ':
        logging.debug('Skipping space after category')
        idx += 1
    match = u''
    this_level = 0

    while text[idx] != '>':
        logging.debug('Examining %d [%c]', idx, text[idx])
        if text[idx] == '<':
            sub, sl = parse_ent(text[idx:], pos + len(match), 'P')
            match += sub
            idx += sl + 1
        else:
            match += text[idx]
            idx += 1
            this_level += 1
    logging.debug('Found end at %d', idx)

    emit_entity(pos, typ, match)
    logging.debug('return [%s], %d', match, idx)
    return match, idx


def process_match(text, pos):
    """
    Parse a top level entity. The `text` is the inside of the entity without
    delimiting <>.
    """
    m, _ = parse_ent('<' + text + '>', pos - len(text))
    return len(text) - len(m) + 2


def extract_line(line, pos):
    """
    Extract all entities from a given line. The second argument determines the
    start of line.
    """
    found = u''
    depth = 0
    offset = 0
    for c in line:
        if c == '<':
            depth += 1
        elif c == '>':
            depth -= 1
            if depth == 0:
                pos -= process_match(found[1:], pos + offset)
                found = u''

        if depth > 0:
            found += c

        offset += 1
    return pos + offset


def cmp_strings(a):
    parts = a.split('\t')
    return (int(parts[0]), 0 if parts[2] == 'W' else 1)


def main():
    logging.basicConfig(level=logging.WARNING)
    pos = 0
    for line in sys.stdin:
        line = line.decode('utf8')
        # Add dot at the end of line if not already there.
        if not re.search('\.>*$', line):
            line = line[:-1] + '.\n'

        pos = extract_line(line, pos)

    for s in sorted(list(collected_entities), key=cmp_strings):
        logging.debug('Considering printing [%s]', s)
        if '\tW\t' in s or s.replace('\tP\t', '\tW\t') not in collected_entities:
            print s.encode('utf8')

if __name__ == '__main__':
    main()
