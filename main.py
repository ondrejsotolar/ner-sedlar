#! /usr/bin/env python
# vim: set encoding=utf-8

"""
Main entry point of the whole system.
"""

import detectors
import tokenizer
import Streams
import CategoryTagger
import CNEC

import argparse
import cgi
import sys
import logging
import itertools


# Values of this dict should be unary functions expecting input stream.
FORMATS = {'markable': Streams.markable_sink,
           'html': lambda x: encode_print(Streams.html_sink(x, cgi.escape)),
           'cnec': CNEC.sink,
           'json': lambda x: encode_print(Streams.json_sink(x)),
           'unitok': Streams.unitok_sink}


def encode_print(data):
    """Encode data to UTF-8 and print it."""
    print data.encode('utf8')


def list_detectors(out):
    """List available detectors to supplied stream."""
    out.write('Available detectors:\n')
    for (nam, desc) in detectors.list_detectors():
        out.write('%s: %s\n' % (nam, desc))


def list_formats():
    """List available output formats."""
    for fmt in sorted(FORMATS.keys()):
        print fmt


def handle_listing(args):
    """If the program should list something, this method does it and exits."""
    if args.list_detectors:
        list_detectors(sys.stdout)
        sys.exit(0)
    if args.list_formats:
        list_formats()
        sys.exit(0)


def main():
    """
    Parse argument and run the program.
    """
    parser = argparse.ArgumentParser(description='Named Entity Extractor')
    parser.add_argument('-v', '--verbose',
                        help='print verbose output of what is happening',
                        action='store_true')
    parser.add_argument('-l', '--list-detectors',
                        help='list available detectors',
                        action='store_true')
    parser.add_argument('detector', metavar='DETECTOR', type=str, nargs='*',
                        help='which detectors to run')
    parser.add_argument('-f', '--format', metavar='FORMAT', type=str,
                        default='markable', help='select output format',
                        choices=FORMATS)
    parser.add_argument('--list-formats',
                        help='list available output formats',
                        action='store_true')
    parser.add_argument('-s', '--skip-freebase',
                        help='skip category tagging via Freebase',
                        action='store_true')

    args = parser.parse_args()

    handle_listing(args)        # May exit the program

    if not args.detector:
        sys.stderr.write('No detector selected\n')
        list_detectors(sys.stderr)
        sys.exit(1)

    if args.detector == ['all']:
        procs = detectors.create_all()
    else:
        procs = [detectors.create_detector(det) for det in args.detector]

    tagger = CategoryTagger.CategoryTagger()

    logging.basicConfig()
    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.DEBUG
        tagger.set_log_level(logging.DEBUG)
        for proc in procs:
            proc.set_log_level(logging.DEBUG)

    input_stream = tokenizer.tokenize(sys.stdin)
    input_streams = itertools.tee(input_stream, len(procs))
    procs = [p.run(x) for (p, x) in zip(procs, input_streams)]

    joined = Streams.merge(procs, level=log_level)
    if not args.skip_freebase:
        joined = tagger.tag(joined)

    FORMATS[args.format](joined)


if __name__ == '__main__':
    main()
