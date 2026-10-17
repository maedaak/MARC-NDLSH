#!/usr/local/bin/perl

use strict;

# make_ndlshdb.pl ver 0.003 2009.08.07
#                 by Akira Maeda

use DBI;
use Encode;

my $ndlsh_data = $ARGV[0];

# Setp 1 Create DB #
my $ndlshdb = "lib/MARC/NDLSH/data/ndlsh.db";
unlink $ndlshdb;
my $dbh = DBI->connect(
  "dbi:SQLite:dbname=$ndlshdb","","",{PrintError=>0}
 );
if(!$dbh){
	print "$DBI::errstr \n";
	exit;
}

my $sql = "";

#　キーワードから件名標目データを得るテーブル
$sql = "
    create table redirect (
       word         text,
       subdivision1 text,
       subdivision2 text,
       subdivision3 text,
       subdivision4 text,
       limitation   text,
       yomi         text,
       id           text,
       is_ndlsh     integer
    )";
$dbh->do($sql);
if(!$dbh){
	print $dbh->errstr . "\n";
	exit;
}

#　Subject Heading (メイン)テーブル
$sql = "
    create table SH (
       id    text,
       ndlsh text,
       SN    text,
       SA    text,
       NDC9  text,
       NDLC  text,
       yomi  text
    )";
$dbh->do($sql);
if(!$dbh){
	print $dbh->errstr . "\n";
	exit;
}

#　リンクテーブル
$sql = "
    create table link (
       from_id  text,
       to_id    text,
       relation text
    )";
$dbh->do($sql);
if(!$dbh){
	print $dbh->errstr . "\n";
	exit;
}

# Step2 Load ndlsh.tsv to SQLite

open (NDLSH, $ndlsh_data) or die "No such NDLSH file \'${ndlsh_data}\'.\n";
my $rd_ins   = $dbh->prepare('insert into redirect values(?,?,?,?,?,?,?,?,?)'); 
my $SH_ins   = $dbh->prepare('insert into SH values(?,?,?,?,?,?,?)'); 
my $link_ins = $dbh->prepare('insert into link values(?,?,?)'); 
print STDERR "\'", $ndlsh_data, "\'", " laoding now. please wait.\n";

while (my $line = <NDLSH>) {
    chomp $line;
    Encode::from_to($line, "shift-jis", "utf8" );
    $line =~ s/\r$//;

    my @fields    = (split /\t/, $line);
    my $yomi      = shift @fields;
    my $word_data = shift @fields;
    my $use       = shift @fields;
    my $id;
    my $is_ndlsh;

    # Load redirect table
    if ($use =~ /^ID:\d+$/) {
        $is_ndlsh = 1;
        ($id) = $use =~ /^ID:(\d+)$/;
    }
    elsif ($use =~ /^USE:.+｛\d+｝/) {
        $is_ndlsh = 0;
        ($id) = $use =~ /^USE:.+｛(\d+)｝/;
    }
    my ($word,
        $subdivision1,
        $subdivision2,
        $subdivision3,
        $subdivision4) = (split /\s*\-\-\s*/, $word_data)[0,1,2,3,4];
    my $limitation;
    if ($word =~ /.+\(.+\)/) {
       ($limitation) = $word =~ /.+\((.+)\)$/;
       $word =~ s/\(.+\)$//;
    }
    $word =~ s/※//;
    $word =~ s/〈.+〉//;
    $word =~ s/^《//;
    $word =~ s/》//;

    $rd_ins->execute($word,
                     $subdivision1,
                     $subdivision2,
                     $subdivision3,
                     $subdivision4,
                     $limitation,
                     $yomi,
                     $id,
                     $is_ndlsh);

    next if $is_ndlsh == 0;

    my ($SN, $SA, $NDC9, $NDLC);
    my $relation;
    foreach my $field (@fields) {
        my ($tag) = $field =~ /^([\w|\(|\)|\d]+):/;
        $tag =~ s/^\s+//;
        ($SN)   = $field =~ /SN:(.+)/       if $tag eq "SN";
        ($SA)   = $field =~ /SA:(.+)/       if $tag eq "SA";
        ($NDC9) = $field =~ /NDC\(9\):(.+)/ if $tag eq "NDC(9)";
        ($NDLC) = $field =~ /NDLC:(.+)/     if $tag eq "NDLC";

       # Load link table
       if ($tag eq "RT" || $tag eq "BT" || $tag eq "NT") {
           foreach my $link (split /\s+\;\s+/, $field) {
               my ($to_id) = $link =~ /.+｛(\d+)｝/;
               $link_ins->execute($id, $to_id, $tag);
           }
       }
    }
    # Load SH table
    $word_data =~ s/※//;
    $word_data =~ s/〈.+〉//;
    $word_data =~ s/^《//;
    $word_data =~ s/》//;
    $SH_ins->execute($id,
                     $word_data,
                     $SN,
                     $SA,
                     $NDC9,
                     $NDLC,
                     $yomi);

}

# Step3 make index

$sql = "create index word_idx on redirect(word)";
$dbh->do($sql);

$sql = "create index subdivison1_idx on redirect(subdivision1)";
$dbh->do($sql);

$sql = "create index subdivison2_idx on redirect(subdivision2)";
$dbh->do($sql);

$sql = "create index subdivison3_idx on redirect(subdivision3)";
$dbh->do($sql);

$sql = "create index subdivison4_idx on redirect(subdivision4)";
$dbh->do($sql);

$sql = "create index limitation_idx on redirect(limiation)";
$dbh->do($sql);

$sql = "create index redirectid_idx on redirect(id)";
$dbh->do($sql);

$sql = "create index id_idx on SH(id)";
$dbh->do($sql);

$sql = "create index ndlsh_idx on SH(ndlsh)";

$dbh->do($sql);

$sql = "create index fromid_idx on link(from_id)";
$dbh->do($sql);

print STDERR "\'", $ndlsh_data, "\'", " laod complete.\n";
