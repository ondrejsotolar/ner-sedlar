#!/bin/bash

set -e
set -o pipefail

LIST_FILE="$1"
LEMMA_FILE="$2"

BASEDIR="$(dirname $0)"
MAJKA="/nlp/projekty/ajka/bin/majka -f /nlp/projekty/ajka/lib/majka.l-wt"
DECLENSION="python /nlp/projekty/declension/declension.py"
FIX_DETERMINERS="python $(dirname $0)/fix-movies.py"

TMP=$(mktemp)
MAJKA_LIST=$(mktemp)
MAJKA_LEMMA=$(mktemp)
DECL_LIST=$(mktemp)
DECL_LEMMA=$(mktemp)

echo "            List       \t\tLemma"
echo "Majka:      $MAJKA_LIST\t\t$MAJKA_LEMMA"
echo "Declension: $DECL_LIST\t\t$DECL_LEMMA"
echo ""

cleanup()
{
    pkill -P $$
    rm -f "$TMP" "$MAJKA_LIST" "$MAJKA_LEMMA" "$DECL_LIST" "$DECL_LEMMA"
}

trap cleanup SIGINT SIGTERM EXIT

(
echo 'Starting majka generator'
cut -d\| -f1 < "$LIST_FILE" \
        | egrep -v '^.*[ .,#$!?"/\()–—-].*$' \
        | egrep -v '^[0123456789]+$' \
        | while read LEMMA; do
    echo "$LEMMA" | $MAJKA >"$TMP"
    awk -F: '{print $1"|"}' >>"$MAJKA_LIST" <"$TMP"
    ESCAPED=$(sed 's/"/\\"/g' <<<"$LEMMA")
    awk -F: "{print \$1\"|$ESCAPED\"}" >>"$MAJKA_LEMMA" <"$TMP"
done
echo 'Finished majka generator'
) &

(
echo 'Starting declension generator'
cut -d\| -f1 <"$LIST_FILE" \
        | egrep -v '^[01234567890]+$' \
        | egrep '^[^ ]* [^ ]*( [^ ]*)?$' \
        | $FIX_DETERMINERS \
        | while read LEMMA; do
    for C in $(seq 2 7); do
        FORM=$($DECLENSION c1 c$C nS "$LEMMA" 2>/dev/null || true)
        if [ -z "$FORM" ]; then
            continue
        fi
        echo "$FORM|" >>"$DECL_LIST"
        echo "$FORM|$LEMMA" >>"$DECL_LEMMA"
    done
done
echo 'Finished declension generator'
) &

finish_file()
{
    mv "$1" "$1.old"
    cat "$1.old" "$2" "$3" \
        | sort | uniq >"$1"
}

wait

finish_file "$LIST_FILE" "$MAJKA_LIST" "$DECL_LIST"
finish_file "$LEMMA_FILE" "$MAJKA_LEMMA" "$DECL_LEMMA"
