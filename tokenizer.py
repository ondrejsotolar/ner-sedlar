#! /usr/bin/env python
# vim: set encoding=utf-8

"""
This program is adapted from unitok.py by Jan Pomikálek. It works as a Python
module that can be used to read separate tokens and it does not lose any
whitespace information.

It only supports Czech language.

When run directly as a program, it should output exactly the data it read
from standard input.
"""

import sys
import re

from Token import Token

SGML_TAG = ur"""
    (?:                         # make enclosing parantheses non-grouping
    <!-- .*? -->                # XML/SGML comment
    |                           # -- OR --
    <[!?/]?(?!\d)\w[-\.:\w]*    # Start of tag/directive
    (?:                         # Attributes
        [^>'"]*                 # - attribute name (+whitespace +equal sign)
        (?:'[^']*'|"[^"]*")     # - attribute value
    )*
    \s*                         # Spaces at the end
    /?                          # Forward slash at the end of singleton tags
    \s*                         # More spaces at the end
    >                           # +End of tag/directive
    )"""
SGML_TAG_RE = re.compile(SGML_TAG, re.UNICODE | re.VERBOSE | re.DOTALL)

SGML_END_TAG = ur"</(?!\d)\w[-\.:\w]*>"
SGML_END_TAG_RE = re.compile(SGML_END_TAG, re.UNICODE)

CLITICS_RE = re.compile(ur"""
            (?:
                (?<=\w)     # only consider clictics preceded by a letter
                -li
            )
            (?!\w)          # clictics should not be followed by a letter
            """, re.UNICODE | re.VERBOSE | re.IGNORECASE)
WORD_RE = re.compile(ur"(?:(?![\d])[-\u2010\w])+", re.UNICODE)
WHITESPACE_RE = re.compile(ur"\s+")

TIME = ur'''
    (?:(?:(?:\d|1\d|2[0-3])[:.][0-6]\d)|(?:24[:.]00))   # Hours:minutes
    (?:[:.][0-5]\d)?    # Optionally followed by :seconds
    (?!\d)              # Not followed by another number
    '''
TIME_RE = re.compile(TIME, re.VERBOSE)

DAY = ur'(?:[1-9]|[12][0-9]|3[0-1])'
DAY_RE = re.compile(DAY)
MONTH = ur'(?:[1-9]|1[0-2])'
MONTH_RE = re.compile(MONTH)
YEAR = ur'\d{4}'
YEAR_RE = re.compile(YEAR)

ZIP = ur'(?<!\d)\d{3}\s?\d{2}(?!\d)'
ZIP_RE = re.compile(ZIP)


# Note that the [  ] sequence allows either normal or nonbreakable space.
PHONE_NUM = ur'''
    (?:\+\d[  ]?\d{0,3}[  ]*\d{3}[  ]*\d{3}[  ]*\d{3})
    |
    (?:\d{3}[  ]\d{3}[  ]\d{3})
    '''
PHONE_NUM_RE = re.compile(PHONE_NUM, re.VERBOSE)

DATE = ur'%s\.%s\.%s' % (DAY, MONTH, YEAR)
DATE_RE = re.compile(DATE)

ISBN = ur'ISBN(-13)?((:?\s+)|:)(\d[ -]?){9}((\d[ -]?){3})?(\d|[xX])'
ISBN_RE = re.compile(ISBN)

IP_ADDRESS = ur"(?:[0-9]{1,3}\.){3}[0-9]{1,3}"
IP_ADDRESS_RE = re.compile(IP_ADDRESS)

DNS_HOST = ur"""
    (?:
        [-a-z0-9]+\.                # Host name
        (?:[-a-z0-9]+\.)*           # Intermediate domains
                                    # And top level domain below
        (?:
        com|edu|gov|int|mil|net|org|            # Common historical TLDs
        biz|info|name|pro|aero|coop|museum|     # Added TLDs
        arts|firm|info|nom|rec|shop|web|        # ICANN tests...
        asia|cat|jobs|mail|mobi|post|tel|
        travel|xxx|
        glue|indy|geek|null|oss|parody|bbs|     # OpenNIC
        localdomain|                            # Default 127.0.0.0

        # And here the country TLDs
        ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|
        ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|
        ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|
        de|dj|dk|dm|do|dz|
        ec|ee|eg|eh|er|es|et|
        fi|fj|fk|fm|fo|fr|
        ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|
        hk|hm|hn|hr|ht|hu|
        id|ie|il|im|in|io|iq|ir|is|it|
        je|jm|jo|jp|
        ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|
        la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|
        ma|mc|md|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|
        na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|
        om|
        pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|
        qa|
        re|ro|ru|rw|
        sa|sb|sc|sd|se|sg|sh|si|sj|sk|sl|sm|sn|so|sr|st|sv|sy|sz|
        tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|
        ua|ug|uk|um|us|uy|uz|
        va|vc|ve|vg|vi|vn|vu|
        wf|ws|
        ye|yt|yu|
        za|zm|zw
        )

        |

        localhost
    )"""
DNS_HOST_RE = re.compile(DNS_HOST, re.VERBOSE | re.IGNORECASE)

URL = ur"""
    (?:

    # Scheme part
    (?:ftp|https?|gopher|mailto|news|nntp|telnet|wais|file|prospero)://

    # User authentication (optional)
    (?:[-a-z0-9_;?&=](?::[-a-z0-9_;?&=]*)?@)?

    # "www" without the scheme part
    |(?:www|web)\.

    )

    # DNS host / IP
    (?:
        """ + DNS_HOST + ur"""
        |
        """ + IP_ADDRESS + ur"""
    )

    # Port specification (optional)
    (?::[0-9]+)?

    # Scheme specific extension (optional)
    (?:/[-\w;/?:@=&\$_.+!*'(~#%,]*)?
"""
URL_RE = re.compile(URL, re.VERBOSE | re.IGNORECASE | re.UNICODE)

EMAIL = ur"[-a-z0-9._']+(?:@|\(at\))" + DNS_HOST
EMAIL_RE = re.compile(EMAIL, re.VERBOSE | re.IGNORECASE)

NUMBER_INTEGER_PART = ur"""
    (?:
        0
        |
        [1-9][0-9]{0,2}(?:[ ,.][0-9]{3})+  # with thousand separators
        |
        [1-9][0-9]*
    )"""
NUMBER_DECIMAL_PART = ur"""
    (?:
        [.,]
        [0-9]+
        (?:[eE][-\u2212+]?[0-9]+)?
    )"""
NUMBER = ur"""
    (?:(?:\A|(?<=\s))[-\u2212+])?
    (?:
        %(integer)s %(decimal)s?
        |
        %(decimal)s
    )""" % {'integer': NUMBER_INTEGER_PART, 'decimal': NUMBER_DECIMAL_PART}

NUMBER_RE = re.compile(NUMBER, re.UNICODE | re.VERBOSE)

# also matches initials
ACRONYM = ur"""
    (?<!\w)     # should not be preceded by a letter
    # sequence of single letter followed by . (e.g. U.S.)
    (?:
        (?![\d_])\w     # alphabetic character
        \.
    )+
    # optionaly followed by a single letter (e.g. U.S.A)
    (?:
        (?![\d_])\w     # alphabetic character
        (?!\w)          # we don't want any more letters to follow
                        # we only want to match U.S. in U.S.Army (not U.S.A)
    )?
"""
ACRONYM_RE = re.compile(ACRONYM, re.UNICODE | re.VERBOSE)

MULTICHAR_PUNCTUATION = ur"(?:[?!]+|``|'')"
MULTICHAR_PUNCTUATION_RE = re.compile(MULTICHAR_PUNCTUATION, re.VERBOSE)

# These punctuation marks should be tokenised to single characters
# even if a sequence of the same characters is found. For example,
# tokenise '(((' as ['(', '(', '('] rather than ['((('].
OPEN_CLOSE_PUNCTUATION = ur"""
    [
        \u00AB \u2018 \u201C \u2039 \u00BB \u2019 \u201D \u203A \u0028 \u005B
        \u007B \u0F3A \u0F3C \u169B \u2045 \u207D \u208D \u2329 \u23B4 \u2768
        \u276A \u276C \u276E \u2770 \u2772 \u2774 \u27E6 \u27E8 \u27EA \u2983
        \u2985 \u2987 \u2989 \u298B \u298D \u298F \u2991 \u2993 \u2995 \u2997
        \u29D8 \u29DA \u29FC \u3008 \u300A \u300C \u300E \u3010 \u3014 \u3016
        \u3018 \u301A \u301D \uFD3E \uFE35 \uFE37 \uFE39 \uFE3B \uFE3D \uFE3F
        \uFE41 \uFE43 \uFE47 \uFE59 \uFE5B \uFE5D \uFF08 \uFF3B \uFF5B \uFF5F
        \uFF62 \u0029 \u005D \u007D \u0F3B \u0F3D \u169C \u2046 \u207E \u208E
        \u232A \u23B5 \u2769 \u276B \u276D \u276F \u2771 \u2773 \u2775 \u27E7
        \u27E9 \u27EB \u2984 \u2986 \u2988 \u298A \u298C \u298E \u2990 \u2992
        \u2994 \u2996 \u2998 \u29D9 \u29DB \u29FD \u3009 \u300B \u300D \u300F
        \u3011 \u3015 \u3017 \u3019 \u301B \u301E \u301F \uFD3F \uFE36 \uFE38
        \uFE3A \uFE3C \uFE3E \uFE40 \uFE42 \uFE44 \uFE48 \uFE5A \uFE5C \uFE5E
        \uFF09 \uFF3D \uFF5D \uFF60 \uFF63
    ]
"""
OPEN_CLOSE_PUNCTUATION_RE = re.compile(OPEN_CLOSE_PUNCTUATION,
                                       re.UNICODE | re.VERBOSE)

COORDINATES = ur'\d?\d°\s*\d?\d\'(?:\s*\d?\d(?:[.,]\d+)?")?[NESW]'
COORDINATES_RE = re.compile(COORDINATES, re.VERBOSE)

RATIO = ur'\d+[  ]:[  ]\d+'
RATIO_RE = re.compile(RATIO)

ANY_SEQUENCE = ur"(.)\1*"
ANY_SEQUENCE_RE = re.compile(ANY_SEQUENCE)

RE_LIST = [(SGML_TAG_RE, Token.SGML_TAG),
           (CLITICS_RE, Token.CLITICS),
           (ISBN_RE, Token.ISBN),
           (PHONE_NUM_RE, Token.PHONE_NUM),
           (COORDINATES_RE, Token.COORDINATES),
           (ZIP_RE, Token.ZIP_CODE),
           (RATIO_RE, Token.RATIO),
           (WHITESPACE_RE, Token.WHITESPACE),
           (URL_RE, Token.URL),
           (EMAIL_RE, Token.EMAIL),
           (IP_ADDRESS_RE, Token.IP_ADDRESS),
           (TIME_RE, Token.TIME),
           (DATE_RE, Token.DATE),
           (NUMBER_RE, Token.NUMBER),
           (ACRONYM_RE, Token.ACRONYM),
           (WORD_RE, Token.WORD),
           (MULTICHAR_PUNCTUATION_RE, Token.ANY),
           (OPEN_CLOSE_PUNCTUATION_RE, Token.ANY),
           (ANY_SEQUENCE_RE, Token.ANY)]


def tokenize_recursively(text, re_list, depth=0):
    """
    This function takes regular expression from re_list. Then it splits the
    text on matches of the expression. Each shorter part is then processed
    recursively with shorter list of expressions.
    """
    if depth >= len(re_list):
        return [text]
    tokens = []
    pos = 0
    regex, typ = re_list[depth]
    while pos < len(text):
        m = regex.search(text, pos)
        if not m:
            tokens.extend(tokenize_recursively(text[pos:], re_list, depth+1))
            break
        else:
            startpos, endpos = m.span()
            if startpos > pos:
                tokens.extend(tokenize_recursively(text[pos:startpos],
                                                   re_list, depth+1))
            tokens.append((text[startpos:endpos], typ))
            pos = endpos
    return tokens


class Tokenizer(object):
    """
    DO NOT USE this class directly from outside the module. Use `tokenize()` or
    `tokenize_string()` functions.

    Internal class implementing the tokenizer. It encapsulates the parsing
    state so that data can be fed to in chunks using the `feed_data()` method.

    When all data has been fed to the tokenizer, caller MUST call the
    `finalize()` method so that trailing whitespace may be emitted as well.
    """
    def __init__(self):
        self.whitespace = u''
        self.position = 0

    def feed_data(self, string):
        """
        Pass more data to the tokenizer. This method yields the parsed tokens.
        """
        tokens = tokenize_recursively(string, RE_LIST)
        for (token, typ) in tokens:
            if typ == Token.WHITESPACE:
                self.whitespace += token
            else:
                yield Token(token, self.whitespace or u'',
                            position=self.position, typ=typ)
                self.whitespace = u''
            self.position += len(token)

    def finalize(self):
        """
        After all data was fed to the tokenizer, this method returns the token
        representing the trailing whitespace (or None if there was none).
        """
        if self.whitespace:
            return Token('', self.whitespace,
                         typ=Token.WHITESPACE, position=self.position)
        return None


def tokenize(fp):
    """
    Read data from file handle `fp`. This function yields Tokens. The last
    Token yielded may contain empty string as word. This means that there was
    whitespace at the end of the stream.
    """

    tokenizer = Tokenizer()

    for (lineno, line) in enumerate(fp):
        try:
            line = line.decode('utf8')
        except UnicodeDecodeError as detail:
            print >>sys.stderr, "failed to decode line %i: %s" % (lineno+1,
                                                                  detail)
            line = line.decode('utf8', 'replace')

        # This should use "yield from ..." (new in Python 3.3)
        for t in tokenizer.feed_data(line):
            yield t
    last = tokenizer.finalize()
    if last:
        yield last


def tokenize_string(string):
    """
    Tokenize string provided as argument. Apart from that, the function works
    exactly the same as `tokenize`.
    """
    tokenizer = Tokenizer()
    # This should use "yield from ..." (new in Python 3.3)
    for t in tokenizer.feed_data(string):
        yield t
    last = tokenizer.finalize()
    if last:
        yield last


if __name__ == '__main__':
    if '--debug' in sys.argv:
        for tok in tokenize(sys.stdin):
            print repr(tok)
    else:
        for tok in tokenize(sys.stdin):
            if not tok.word:
                continue
            if not tok.whitespace:
                print '<g/>'
            print tok.word.encode('utf8')
