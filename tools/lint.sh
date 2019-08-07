#!/bin/bash

export PYTHONPATH=$(dirname $0)/../lib/trie/lib/python2.7/site-packages

FILES="WLTStorage.py tokenizer.py utils.py WordSet.py LazyDeque.py main.py
       detectors Token.py Majka.py  web-ui/*.py  Streams.py Freebase.py
       CategoryTagger.py StreamItem.py CNEC.py"

pylint --rcfile=$(dirname $0)/../.pylintrc $FILES
pep8 $FILES
pyflakes $FILES
