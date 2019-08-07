#!/bin/bash

set -eu
set -o pipefail

DECLENSION="python /nlp/projekty/declension/declension.py"

cut -d\| -f1 <data/osidleni.txt | while read LEMMA; do
    for C in $(seq 2 7); do
        FORM=$($DECLENSION c1 c$C nS "$LEMMA" 2>/dev/null || true)
        if [ -z "$FORM" ]; then
            continue
        fi
        echo "$FORM|" >>osidleni-tvary.txt
        echo "$FORM|$LEMMA" >>osidleni_lemma.txt
    done
done
