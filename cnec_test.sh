#!/bin/bash

set -e
set -o pipefail

run_eval()
{
    awk '{print $0"."}' <../data/cnec2.0/${1}_no_markup.txt \
        | sed -e 's/\.\.$/\./' -e 's/^\.$//' \
        | time -f "Run time: %e s" ./run.sh all -f cnec --skip-freebase >${1}_output.txt

    ./tools/evaluate.py ../data/cnec2.0/$1.txt ${1}_output.txt
}

if [ $# -eq 0 ]; then
    echo "Required arguments: etest | dtest"
    exit 1
fi

run_eval $1
