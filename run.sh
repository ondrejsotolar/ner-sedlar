#!/bin/bash

DIR=$(dirname $0)
cd $DIR
exec python2.7 main.py $@
