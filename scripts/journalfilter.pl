#!/usr/bin/perl

sub trim
{
  local $_ = shift;
  s/^\s+//;
  s/\s+$//; 
  return $_
}

while (<>)
{
  next if /^\s*(#.*)?$/;

  my ($long, $short) = split /=/;
  my ($abbr, $comment) = split /;/, $short;

  $long = trim $long;
  $abbr = trim $abbr;

  my $key = $abbr;
  $key =~ s/\s+/_/g;
  $key =~ s/\W//g;
  $key = lc $key;

  print "\@journal{$key,\n\tname=\"$long\",\n";
  print "\tshortname=\"$abbr\",\n" if $abbr ne $long;
  print "}\n\n";
}
