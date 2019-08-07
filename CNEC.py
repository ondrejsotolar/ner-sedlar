#! /usr/bin/env python
# vim: set encoding=utf-8

"""
This module provides stream sink for output to evaluate precision and recall on
CNEC.
"""

import Streams


def emit(pos, text, typ='W'):
    """Print entity at given position."""
    if text:
        print ('%d\t%d\t%s\t%s' % (pos, len(text), typ, text)).encode('utf8')


def emit_person(entity):
    """Emit person entity with subentities."""
    name_parts = entity.word.split(' ')
    offset = 0

    emit(entity.position, entity.word)

    if len(name_parts) == 1 and name_parts[0] == entity.word:
        return

    i = 0
    while i < len(name_parts):
        step = 1
        if i < len(name_parts) - 1 and name_parts[i+1] == '.':
            name_parts[i] += ' .'
            step += 1
        else:
            j = 0
            while name_parts[i + j].islower():
                name_parts[i] += ' ' + name_parts[i + j + 1]
                j += 1
            step += j
        if name_parts[i] != ',':
            emit(entity.position + offset, name_parts[i], typ='P')
        offset += len(name_parts[i]) + 1
        i += step


def emit_address(entity):
    """Address components will be emitted as partial entities."""
    pos = entity.position
    emit(pos, entity.word)
    attrs = ['street', 'house', 'zip_code', 'town', 'country']
    for attr in attrs:
        key = 'ner:addr:'+attr
        if key in entity.attrs:
            val = entity.attrs[key]
            offset = entity.word.find(val)
            if offset >= 0:
                emit(pos + offset, val, typ='P')


def emit_date(entity):
    """Components of date will be emitted as partial entities."""
    pos = entity.position
    parts = entity.word.split(' ')
    emit(pos, entity.word)
    offset = 0
    i = 0
    while i < len(parts):
        step = 1
        if i < len(parts) - 1 and parts[i+1] == '.':
            parts[i] += ' .'
            step += 1
            if i < len(parts) - 2 and parts[i+2] == '':
                parts[i] += ' '
                step += 1
        emit(pos + offset, parts[i], typ='P')
        offset += len(parts[i]) + 1
        i += step


def emit_measure(entity):
    """Emit each space separated part as a regular entity."""
    parts = entity.word.split(' ')
    offset = 0
    for part in parts:
        emit(entity.position + offset, part)
        offset += len(part) + 1


def emit_law(entity):
    """Law number components will be emitted as partial entities."""
    emit(entity.position, entity.word)
    for attr in {'paragraph', 'section', 'letter', 'number', 'collection'}:
        k = 'law_' + attr
        if k in entity.attrs and entity.attrs[k]:
            val = entity.attrs[k]
            offset = entity.word.find(val)
            if offset >= 0:
                emit(entity.position + offset, val, typ='P')
    if 'Sb' in entity.word:
        offset = entity.word.find('Sb')
        emit(entity.position + offset, entity.word[offset:], typ='P')


def emit_org(entity):
    """If organisation name starts with abbr, emit abbr separately."""
    emit(entity.position, entity.word)
    words = entity.word.split(' ')
    if all(c.isupper() for c in words[0]):
        emit(entity.position, words[0], typ='P')


def sink(inp):
    """
    Print list of entities to stdout in format suitable for processing with
    scripts from CNEC.
    """

    for entity in Streams.collector_filter(inp):
        if '\n' in entity.word:
            continue
        pos = entity.position
        typ = entity.attrs['typ'] or ''
        if 'Cprice' in typ:
            space_idx = entity.word.find(' ')
            emit(pos + space_idx + 1, entity.word[space_idx + 1:])
        elif typ == 'CName':
            emit_person(entity)
        elif typ == 'CAddress':
            emit_address(entity)
        elif typ == 'Aevent Bdate':
            emit_date(entity)
        elif typ == 'Aevent Bperiod':
            y1, _, y2 = entity.word.split(' ')
            emit(pos, y1)
            emit(pos + 7, y2)
        elif 'Bpercent' in typ:
            pass
        elif 'Cmeasurement' in typ:
            emit_measure(entity)
        elif typ == 'CLawNo':
            emit_law(entity)
        elif typ == 'COrganisation':
            emit_org(entity)
        else:
            emit(pos, entity.word)
