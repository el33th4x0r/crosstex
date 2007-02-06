#!/bin/sh

for name in "$@"; do
  sed -e '/^ *}/a \\' $name.bib | ./dbfetch-post.pl > $name.xtx
done
