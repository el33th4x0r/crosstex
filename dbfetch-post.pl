#!/usr/bin/perl
#
# Pull out @proceedings entries to the bottom and make them unique.
#
use strict;
use warnings;

$/ = '';
my @lines = <>;
my $i;

$i = 1;
while ($i < @lines) {
  if ($lines[$i] !~ /^\@proceedings/) {
    print $lines[$i];
    splice @lines, $i, 1;
  } else {
    ++$i;
  }
}

exit; # Drop the @proceedings entries

@lines = sort @lines;

$i = 1;
while ($i < @lines) {
  if ($lines[$i] eq $lines[$i - 1]) {
    splice @lines, $i, 1;
  } else {
    ++$i;
  }
}

print @lines;
