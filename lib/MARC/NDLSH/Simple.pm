package MARC::NDLSH::Simple;

use 5.008008;
use strict;
use warnings;
use MARC::NDLSH;

require Exporter;
our @EXPORT_OK = qw(NDLSH SimmularTerms RelatedTerms BroaderTerms NallowTerms);
our @ISA = qw(Exporter);
our $VERSION = '0.02';

=pod

=head1 NAME

MARC::NDLSH::Simple -国会図書館件名標目(NDLSH)から簡単に情報を取り出す

=head1 SYNOPSIS

  use MARC::NDLSH::Simple;

  # 件名標目形を出力
  my @sh = MARC::NDLSH::Simple::NDLSH($any_term)
  print join " / ", @sh;

  # 類似語(リンクしている件名標目形と参照形)を出力
  my @st = MARC::NDLSH::Simple::SimmularTerms($any_term)
  print join " / ", @st;

  # 関連語を出力
  my @rt = MARC::NDLSH::Simple::RelatedTerms($any_term)
  print join " / ", @rh;

  # 上位語を出力
  my @bt = MARC::NDLSH::Simple::BroaderTerms($any_term)
  print join " / ", @bt;

  # 下位語を出力
  my @nt = MARC::NDLSH::Simple::NallowerTerms($any_term)
  print join " / ", @nt;

=head1 DESCRIPTION

国会図書館の件名標目を扱うPerlモジュール"MARC::NDLSH"に対し、
より簡単な関数型のインターフェイスを提供します。

=over

=head2 FUNCTIONS

=over 4

=item MARC::NDLSH::Simple::NDLSH(I<$any_term>)

国会図書館件名標目の件名標目形を得る。結果は語彙の配列である。

=cut

sub NDLSH {
    my $input = shift;
    my $obj = new MARC::NDLSH;
    my @node_objs = $obj->set_word($input);
    my @all_ndlsh;
    if (scalar @node_objs > 0) {
         # 件名標目形
         foreach my $node (@node_objs) {
             push @all_ndlsh, $node->as_NDLSH;
        }
        return @all_ndlsh;
    }
    return undef;
}

=pod

=item MARC::NDLSH::Simple::SimmularTerms(I<$any_term>)

類義語を得る。結果は語彙の配列である。

=cut

sub SimmularTerms {
	my $input = shift;
    my $obj = new MARC::NDLSH;
    my @node_objs = $obj->set_word($input);
    if (scalar @node_objs > 0) {
         my %relation = ();
         foreach my $node (@node_objs) {
             foreach my $term ($node->simular) {
                 $relation{$term}++
                    unless $input eq $term;
             }
         }
         return keys %relation;
    }
    return undef;
}

=pod

=item MARC::NDLSH::Simple::RelatedTerms(I<$any_term>)

関連語を得る。結果は語彙の配列である。

=cut

sub RelatedTerms {
    my $input = shift;
    my $obj = new MARC::NDLSH;
    my @node_objs = $obj->set_word($input);
    if (scalar @node_objs > 0) {
        my %relation = ();
        foreach my $node (@node_objs) {
            foreach my $t ($node->RT) {
                my $term =  $t->as_NDLSH;
                $relation{$term}++ unless $input eq $term;
            }
        }
        return keys %relation;
    }
    return undef;
}

=pod

=item MARC::NDLSH::Simple::BroaderTerms(I<$any_term>)

上位語を得る。結果は語彙の配列である。

=cut

sub BroaderTerms {
    my $input = shift;
	my $obj = new MARC::NDLSH;
    my @node_objs = $obj->set_word($input);
    if (scalar @node_objs > 0) {
        my %relation = ();
        foreach my $node (@node_objs) {
            foreach my $t ($node->BT) {
                my $term =  $t->as_NDLSH;
                $relation{$term}++ unless $input eq $term;
            }
        }
        return keys %relation;
    }
    return undef;
}

=pod

=item MARC::NDLSH::Simple::NallowerTerms(I<$any_term>)

下位語を得る。結果は語彙の配列である。

=cut

sub NallowerTerms {
    my $input = shift;
	my $obj = new MARC::NDLSH;
    my @node_objs = $obj->set_word($input);
    if (scalar @node_objs > 0) {
        my %relation = ();
        foreach my $node (@node_objs) {
            foreach my $t ($node->NT) {
                my $term =  $t->as_NDLSH;
                $relation{$term}++ unless $input eq $term;
            }
        }
        return keys %relation;
    }
    return undef;
}

=head2 EXPORT

次の関数がEXPORT可能です。

=over 8

=item NDLSH()

=item SimmularTerms()

=item RelatedTerms()

=item BroaderTerms()

=item NallowTerms()

=head1 SEE ALSO

MARC::NDLSH

=head1 AUTHOR

Akira MaedaE<lt>maeda@lib.u-tokyo.ac.jpE<gt>

=head1 COPYRIGHT AND LICENSE

Copyright (C) 2009 by Akira Maeda

This library is free software; you can redistribute it and/or modify
it under the same terms as Perl itself, either Perl version 5.8.8 or,
at your option, any later version of Perl 5 you may have available.

=cut

1;
