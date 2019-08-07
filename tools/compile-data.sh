#!/bin/bash

set -e

cd $(dirname $0)/../data
COMPILE=../lib/trie/bin/list-compile

for file in jmena.wlt prijmeni-sorted.wlt; do
    echo "Processing $file..."
    stripped=${file%.wlt}
    if [ $file -nt ${stripped}.trie ]; then
        sed 's/\r$//' $file | $COMPILE -d: /dev/stdin ${stripped%.txt}.trie
    else
        echo 'Skipping'
    fi
done

for file in phrase_categories.txt phrase_lemmas.txt; do
    echo "Processing $file..."
    if [ $file -nt ${file%.txt}.trie ]; then
        $COMPILE -d\| $file ${file%.txt}.trie
    else
        echo 'Skipping'
    fi
done

for file in osidleni.txt seznam_ulic.txt phrase_list.txt; do
    echo "Processing $file..."
    if [ $file -nt ${file%.txt}.trie ]; then
        $COMPILE -d\| -e $file ${file%.txt}.trie
    else
        echo 'Skipping'
    fi
done

for file in $(find lang-words/ -type f -name '*.txt'); do
    echo "Processing $file..."
    if [ $file -nt ${file%.txt}.trie ]; then
        $COMPILE -e $file ${file%.txt}.trie
    else
        echo 'Skipping'
    fi
done
