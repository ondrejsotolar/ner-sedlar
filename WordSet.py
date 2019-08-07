#! /usr/bin/env python
# vim: set encoding=utf-8

"""
This modules exports the WordSet class and contains an example usage of it when
run as main.
"""


class WordSet(object):
    """
    WordSet is a wrapper around the Set standard object. It is created by
    loading its contents from a file. Each entry in the file can be modified by
    a filter function. This allows for e.g. case insensitive comparison.
    """

    def __init__(self, filename, encoding='utf8', filt=None):
        self.words = set()
        self.filt = filt if filt else lambda x: x
        self.load_words(filename, encoding)

    def load_words(self, filename, encoding):
        """
        Load words from given filename. Each word should be on a line on its
        own. Leading and trailing whitespace is stripped.
        """
        with open(filename, "r") as f:
            for line in f.readlines():
                line = line.decode(encoding)
                self.words.add(self.filt(line.strip()))

    def __contains__(self, word):
        return self.filt(word) in self.words

    def __iter__(self):
        return self.words.__iter__()


if __name__ == '__main__':
    def main():
        """Test main"""
        ws = WordSet("../data/ignored_abbr.txt", filt=lambda x: x.lower())

        def test(word, yesno):
            """Test utility"""
            if (word in ws) == yesno:
                print word, 'OK'
            else:
                print word, 'FAIL'
        for (w, b) in [(u'für', True), (u'si', True), (u'foo', False),
                       (u'FÜR', True)]:
            test(w, b)

    main()
