#! /usr/bin/env python
# vim: set encoding=utf-8

"""
Web interface for Named Entity Recognizer.
"""

import cgitb
cgitb.enable(display=0)

import cgi
from string import Template
import logging
import sys
import os
import itertools
import urlparse

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../v2')

import detectors
import tokenizer
import Streams
import CategoryTagger


def load_template(name):
    """Load a template with given file."""
    with open('templates/%s.tpl.html' % name, 'r') as f:
        return Template(f.read().decode('utf8'))


def get_default_text():
    """Load default form text."""
    with open('templates/default_text.txt', 'r') as f:
        return f.read()


def run_main_template(data, warning=''):
    """Print main template with appropriate data filled in."""
    main_template = load_template('template')
    print main_template.substitute(data=data, warning=warning).encode('utf8')


def header_ok(mime='text/html'):
    """Send headers with 200 OK code."""
    print "Content-Type: %s; charset=utf-8" % mime
    print "Status: 200 OK\n"


def generate_form():
    """Create page with input form."""
    default = get_default_text().decode('utf8')
    form_html = load_template('form').substitute(default_text=default)
    header_ok()
    run_main_template(form_html)


def want_json():
    """Check if user requested results as a JSON."""
    query = os.environ['QUERY_STRING'] or ''
    pairs = urlparse.parse_qs(query)
    with open('log.log', 'w') as f:
        f.write('%r\n' % os.environ)
    if 'json' in pairs:
        if '1' in pairs['json']:
            return True
        if '0' in pairs['json']:
            return False
    return ('HTTP_X_REQUESTED_WITH' in os.environ and
            os.environ['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest')


def process_form(form):
    """Read data from form, process it and return nice HTML page."""
    logging.basicConfig()

    input_data = form.getfirst('text', get_default_text()).decode('utf8')

    warning = ''
    if len(input_data) > 1000:
        warning = u'Příliš mnoho dat. Pracuji pouze s prvními 1000 znaky.'
        input_data = input_data[:1000]

    tagger = CategoryTagger.CategoryTagger()
    input_stream = tokenizer.tokenize_string(input_data)
    procs = detectors.create_all()
    input_streams = itertools.tee(input_stream, len(procs))
    procs = [p.run(x) for (p, x) in zip(procs, input_streams)]

    result = tagger.tag(Streams.merge(procs))

    if want_json():
        header_ok('application/json')
        print '{'
        if warning:
            print '"warning": "%s",' % warning.encode('utf8')
        print '"data": %s' % Streams.json_sink(result).encode('utf8')
        print '}'
    else:
        result = Streams.html_sink(result, cgi.escape)
        header_ok('text/html')
        warn_tpl = load_template('warning')
        warning = warn_tpl.substitute(text=warning) if warning else ''
        run_main_template(load_template('results').substitute(results=result),
                          warning=warning)


def dispatch():
    """Determine which action to perform."""
    form = cgi.FieldStorage()
    if os.environ['REQUEST_METHOD'] != 'POST' and 'text' not in form:
        generate_form()
    else:
        process_form(form)


dispatch()
