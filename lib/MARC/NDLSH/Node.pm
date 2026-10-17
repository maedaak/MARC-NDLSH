package MARC::NDLSH::Node;

use 5.008008;
use strict;
use warnings;

require Exporter;

our @ISA = qw(Exporter);
our $VERSION = '0.01';

# package costractor
sub new {
    my $proto = shift;
    my $id    = shift;
    my $class = ref($proto) || $proto;
    my $self = {};
    bless ($self, $class);
    $self->{"id"} = $id;
    my $ndlshdb = $INC{"MARC/NDLSH.pm"};
    $ndlshdb =~ s/NDLSH.pm$/NDLSH\/data\/ndlsh.db/;
    $self->{"db"} = $ndlshdb;
    return $self;
}

# NDLSHのID番号を返す
sub getid {
    my $self = shift;
    return $self->{"id"};
}

# NDLSHを返す
sub as_NDLSH {
    my $self = shift;
    return _get_SH($self, "ndlsh");
}

# SN (Scope Note)を返す
sub SN {
    my $self = shift;
    return _get_SH($self, "SN");
}

# SA (参照注記)を返す
sub SA {
    my $self = shift;
    return _get_SH($self, "SA");
}

# NDC第9版の分類を返す
sub NDC9 {
    my $self = shift;
    return _get_SH($self, "NDC9");
}

# NDLCの分類を返す
sub NDLC {
    my $self = shift;
    return _get_SH($self, "NDLC");
}

# 件名の「読み」を返す
sub yomi {
    my $self = shift;
    return _get_SH($self, "yomi");
}


# テーブルSHからデータを得る
sub _get_SH {
    my $self = shift;
    my $colm = shift;

    my %name2id = ("id"    => 0,
                   "ndlsh" => 1,
                   "SN"    => 2,
                   "SA"    => 3,
                   "NDC9"  => 4,
                   "NDLC"  => 5,
                   "yomi"  => 6);

    my $i = $name2id{$colm};

    my $ndlshdb = $self->{"db"};
    my $dbh = DBI->connect(
        "dbi:SQLite:dbname=$ndlshdb","",""
    );
    if(!$dbh){
        print "$DBI::errstr \n";
        exit;
    }

    my $select = $dbh->prepare('select * from SH where id=?');
    $select->execute($self->getid);

    my @row;
    @row = $select->fetchrow_array;
    return $row[$i];
}

# RT (関連語を返す)
sub RT {
    my $self = shift;
    return _get_link($self, "RT");
}

# BT (上位語を返す)
sub BT {
    my $self = shift;
    return _get_link($self, "BT");
}

# NT (下位語を返す)
sub NT {
    my $self = shift;
    return _get_link($self, "NT");
}

# テーブルlinkからデータを得る
sub _get_link {
    my $self     = shift;
    my $relation = shift;
    my $ndlshdb = $self->{"db"};
    my $dbh = DBI->connect(
        "dbi:SQLite:dbname=$ndlshdb","",""
    );
    if(!$dbh){
        print "$DBI::errstr \n";
        exit;
    }
    my $select = $dbh->prepare('select * from link where from_id=? and relation=?');
    $select->execute($self->getid, $relation);

    my @row;
    my @_get_link;
    while (@row = $select->fetchrow_array) {
        my $relation_obj = new MARC::NDLSH::Node $row[1];
        push @_get_link, $relation_obj;
    }
    return @_get_link;
}

# simular (USE, USE FORを返す))
sub simular {
    my $self = shift;
    my $ndlshdb = $self->{"db"};
    my $dbh = DBI->connect(
        "dbi:SQLite:dbname=$ndlshdb","",""
    );
    if(!$dbh){
        print "$DBI::errstr \n";
        exit;
    }
    my $select = $dbh->prepare('select * from redirect where id=?');
    $select->execute($self->getid);

    my @row;
    my @simular;
    while (@row = $select->fetchrow_array) {
        my $word = $row[0];
        if ($word =~ /^\w+$/) {
            if (defined $row[5]) { $word .= "(" . $row[5] . ")"; }
            if (defined $row[1]) { $word .= " -- " . $row[1]; }
            if (defined $row[2]) { $word .= " -- " . $row[2]; }
            if (defined $row[3]) { $word .= " -- " . $row[3]; }
            if (defined $row[4]) { $word .= " -- " . $row[4]; }
        }
        else {
            if (defined $row[5]) { $word .= "（" . $row[5] . "）"; }
            if (defined $row[1]) { $word .= "--" . $row[1]; }
            if (defined $row[2]) { $word .= "--" . $row[2]; }
            if (defined $row[3]) { $word .= "--" . $row[3]; }
            if (defined $row[4]) { $word .= "--" . $row[4]; }
        }
        push @simular, $word;
    }
    return @simular;
}

1;

=head1 AUTHOR

Akira Maeda<lt>maeda@lib.u-tokyo.ac.jpE<gt>

=head1 COPYRIGHT AND LICENSE

Copyright (C) 2009 by Akira Maeda

This library is free software; you can redistribute it and/or modify
it under the same terms as Perl itself, either Perl version 5.8.8 or,
at your option, any later version of Perl 5 you may have available.

=cut
