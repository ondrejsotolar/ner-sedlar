#!/bin/bash

set -e

# There are 50 results on each page. For a given search query, only 20 pages
# will be served. To circumvent this limitation, the downloading is spread
# across the years of publishing of the movie. The year 1909 is the first with
# more than 1000 movies, so from that year on the process is split according
# to the review starting with equal steps of 25 per cent. From 1984 on the step
# decreases to 10, from 1999 it is only 5.

DESTDIR=../data/filmy

# This constant controls how many seconds will the program wait after
# downloading each page.
PAUSE=10

# Wrapper around actual downloading. This function needs two arguments. The
# first one is the URL to be downloaded, the other is the destination file.
get() {
    echo wget $1 -O $2
    wget -a wget.log -U 'Scraping list of all movies/wget' $1 -O $2
}

rm -f wget.log
mkdir -p page
mkdir -p filmy

# scrape FROM_YEAR TO_YEAR STEP
scrape()
{
    FROM_YEAR=$1
    TO_YEAR=$2
    STEP=$3
    for year in $(seq $FROM_YEAR $TO_YEAR); do
        mkdir -p $DESTDIR/page/year-$year/
        mkdir -p $DESTDIR/filmy/year-$year/
        echo "Doing year $year"
        for rating in $(seq 0 $STEP $((100-$STEP)) ); do
            mkdir -p $DESTDIR/page/year-$year/rating-$rating
            mkdir -p $DESTDIR/filmy/year-$year/rating-$rating
            echo "  Doing rating $rating - $(($rating + $STEP))"
            page=0
            while :; do
                page=$(($page + 1))

                destfile="page/year-$year/rating-$rating/pg-$page.html"

                if [ ! -r "$destfile" ]; then
                    echo "    Getting page $page"
                    if [ $page = 21 ]; then
                        echo 'TOO MANY PAGES'
                        exit 1
                    fi
                    # ALL THE THINGS
                    URL="http://www.csfd.cz/podrobne-vyhledavani/strana-$page/?genre%5Btype%5D=2&genre%5Binclude%5D%5B0%5D=&genre%5Bexclude%5D%5B0%5D=&origin%5Btype%5D=2&origin%5Binclude%5D%5B0%5D=&origin%5Bexclude%5D%5B0%5D=&year_from=$year&year_to=$(($year+1))&rating_from=$rating&rating_to=$(($rating+$STEP))&actor=&director=&composer=&screenwriter=&author=&cinematographer=&tag=&ok=Hledat&_form_=film"
                    get "$URL" "$destfile"
                    echo "    Waiting..."
                    sleep $PAUSE
                fi

                if grep -q 'žádné filmy neodpovídají zadaným podmínkám' $destfile; then
                    echo "    No match in page $page"
                    break
                fi

                echo -n "    Processing page $page ... "
                found=$(grep 'class="film' "$destfile" \
                    | cut -d'>' -f3 \
                    | cut -d'<' -f1 \
                    | grep -v '^$' \
                    | tee $DESTDIR/filmy/year-$year/rating-$rating/filmy-$page.txt \
                    | wc -l)
                echo "got $found movies"
                if [ "$found" -lt "50" ]; then
                    break
                fi
            done
        done
    done
}

scrape 1878 1908 100
scrape 1909 1983 25
scrape 1984 1998 10
scrape 1999 2005 5
scrape 2006 2015 2
