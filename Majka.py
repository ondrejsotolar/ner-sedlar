#! /usr/bin/env python
# vim: set encoding=utf-8

"""
This module exports the wrapper around the morphological analyzer.
"""

import logging
import subprocess
import os.path


def get_cmd():
    """Find out where is majka binary and return a list with arguments."""
    if os.path.isfile('/nlp/projekty/ajka/bin/majka'):
        return ['/nlp/projekty/ajka/bin/majka', '-p']
    if os.path.isfile('../data/majka'):
        return ['../data/majka', '-p', '-f', '../data/majka.w-lt']
    raise UserWarning('No suitable Majka binary found')


def start_process():
    """Start new Majka process and return Popen object."""
    return subprocess.Popen(get_cmd(), stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE)


class Majka(object):
    """
    Class abstracting the majka binary. There is a cache shared among all
    instances of this class. That way, only one lookup for each word has to be
    done. This helps to speed it up by a lot.
    This module spawns one process per instance to which it sends the words to
    be analyzed.
    """

    cache = {}

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.proc = start_process()

    def split_line(self, line):
        """Parse oneline output of Majka, returning list of tuples."""
        parts = line.decode('utf8').split(':')[1:]
        if not parts:
            return []
        if len(parts) % 2 != 0:
            self.logger.warning('Majka returned unexpected data <%s>', line)
            return []
        return [tuple(parts[i:i+2]) for i in range(0, len(parts), 2)]

    def read_output(self, word):
        """Actually run the command and get its output as a list of lines."""
        try:
            self.proc.poll()
            if self.proc.returncode and self.proc.returncode < 0:
                self.logger.warning('Majka process crashed with %d',
                                    self.proc.returncode)
                self.proc = start_process()
            self.proc.stdin.write(word.encode('utf8') + '\n')
            line = self.proc.stdout.readline()
            return self.split_line(line.rstrip())
        except subprocess.CalledProcessError as err:
            self.logger.warning('Error running command: %s', err)
        except UnicodeDecodeError as err:
            self.logger.warning('Decoding failure: %s', err)
        except UnicodeEncodeError as err:
            self.logger.warning('Encoding failure: %s', err)
        return ""

    def get_lemma_tag(self, word):
        """
        For a given word, retrieve a list of pairs (lemma, tag). The results
        are caches, so asking for the same word multiple times is not big deal.
        """
        if word in Majka.cache:
            return Majka.cache[word]
        Majka.cache[word] = self.read_output(word)
        return Majka.cache[word]

    def set_log_level(self, level):
        """Set log level."""
        self.logger.setLevel(level)


if __name__ == '__main__':
    def main():
        """Testing main."""
        logging.basicConfig()
        m = Majka()
        m.set_log_level(logging.DEBUG)
        print m.get_lemma_tag(u'pes')

    main()
