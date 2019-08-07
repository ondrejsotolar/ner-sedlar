#!/bin/bash

set -e

LOGFILE=libtrie-install.log
> $LOGFILE
exec >  >(tee $LOGFILE)
exec 2> >(tee $LOGFILE >&2)

LATEST=0.2

CUR_DIR=$(pwd)
PREFIX=$CUR_DIR/$(dirname $0)/../lib/trie

run()
{
    echo "$*"
    $*
}

cd /tmp
wget https://github.com/lubomir/libtrie/releases/download/v$LATEST/libtrie-$LATEST.tar.xz
tar xf libtrie-$LATEST.tar.xz
cd libtrie-$LATEST
run ./configure --prefix=$PREFIX
run make
run make install
cd $CUR_DIR
rm -r /tmp/libtrie-$LATEST /tmp/libtrie-$LATEST.tar.xz

echo -e "\n\tSUCCESS\n"
