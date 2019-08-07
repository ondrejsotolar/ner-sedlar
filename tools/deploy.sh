#!/bin/bash

set -e

TGT_DIR=$(dirname $0)/../
cd "$TGT_DIR"

echo 'Updating main codebase...'
rsync -avz --exclude 'web-ui/' --exclude 'lib' --exclude '*.swp' \
    --exclude '*.pyc' --exclude '.todo' --exclude 'cache/*' \
    --exclude './*.txt' --exclude '%.prev_result' --exclude 'data/backup' \
    --exclude '*.log' \
    ./ aurora:/nlp/projekty/ner/v2

echo 'Updating web interface...'
rsync -avz --exclude '*.swp' --exclude '*.pyc' \
    web-ui/ aurora:/nlp/projekty/ner/public_html/v2

git tag -f $(date +'deployed-%Y-%m-%d')
