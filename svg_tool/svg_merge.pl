#!/usr/bin/perl
########################################################################
#SVG merging tool v0.2
#Copyright 2011,2016 Elliot Wolk
#
#Very simple tool for smooshing SVG files together.
#
########################################################################
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.
########################################################################

use strict;
use warnings;

sub parseXml($);
sub modifyIds($$);

sub main(@){
  die "Usage: $0 SVG_OUT_FILE SVG_IN_FILE [SVG_IN_FILE]\n" if @_ < 2;

  my ($destFile, @srcFiles) = shift;
  my @inFiles = @_;

  my ($firstPrefix, $firstSuffix);
  my $newContents = "";
  my $count = 0;
  for my $file(@inFiles){
    open FH, "< $file" or die "Could not read file: $file\n$!\n";
    my $xml = join '', <FH>;
    close FH;

    my ($prefix, $contents, $suffix) = parseXml $xml;
    $firstPrefix = $prefix if not defined $firstPrefix;
    $firstSuffix = $suffix if not defined $firstSuffix;

    $count++;

    $contents = modifyIds $contents, "file${count}_";

    my $fileName = $file;
    $fileName =~ s/.*\///;
    $fileName =~ s/[^a-zA-Z0-9]+/_/g;
    $newContents .= ""
      . "\n"
      . "<!-- START: file$count: $fileName -->\n"
      . "$contents\n"
      . "<!-- END: file$count: $fileName -->\n"
      . "\n"
      ;
  }
  $newContents = $firstPrefix . $newContents . $firstSuffix;

  open FH, "> $destFile" or die "Could not write file: $destFile\n$!\n";
  print FH $newContents;
  close FH;
}

sub parseXml($){
  my $xml = shift;

  my $xmlAttRegex = qr/(?:
    \s*
    [a-zA-Z0-9_\-:]+
    \s* = \s*
    (?:
      "
        (?: [^"\\]* | \\" )*
      "
      |
      \'
        (?: [^'\\]* | \\' )*
      \'
    )
    \s*
  )/sx;

  if($xml !~ /
    ^
    (.*)                         #before svg tag
    (< \s* svg $xmlAttRegex* >)  #svg open tag
    (.*)                         #content
    (< \s* \/ \s* svg \s* >)     #svg close tag
    (.*)                         #after svg close tag
    $
    /sx){
    die "SVG file is (probably?) malformed";
  }

  return ("$1$2", $3, "$4$5");
}

sub modifyIds($$){
  my ($xml, $idPrefix) = @_;
  my @ids = $xml =~ /\sid="(linearGradient\d+)"/g;

  my %okIds = map {$_ => 1} @ids;
  @ids = sort keys %okIds;

  for my $id(@ids){
    my $oldId = $id;
    my $newId = "$idPrefix$id";
    $xml =~ s/"$oldId"/"$newId"/g;
    $xml =~ s/"#$oldId"/"#$newId"/g;
    $xml =~ s/\($oldId\)/\($newId\)/g;
    $xml =~ s/\(#$oldId\)/\(#$newId\)/g;
  }
  return $xml;
}

&main(@ARGV);
