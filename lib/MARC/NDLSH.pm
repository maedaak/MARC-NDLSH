package MARC::NDLSH;

use 5.008008;
use strict;
use warnings;
use DBI;
use MARC::NDLSH::Node;

require Exporter;

our @ISA = qw(Exporter);

our $VERSION = '0.04';

# package costractor
sub new {
    my $proto = shift;
    my $class = ref($proto) || $proto;
    my $self = {};
    bless ($self, $class);
    return $self;
}

sub set_word {
    my $self = shift;
    my $word = shift;

    my $ndlshdb = $INC{"MARC/NDLSH.pm"};
    $ndlshdb =~ s/NDLSH.pm$/NDLSH\/data\/ndlsh.db/;
    my $dbh = DBI->connect(
        "dbi:SQLite:dbname=$ndlshdb","",""
    );
    if(!$dbh){
        print "$DBI::errstr \n";
        exit;
    }

    my $select = $dbh->prepare('select * from redirect where word=?');
    $select->execute($word);

    my @row;
    my @set_word;
    while(@row = $select->fetchrow_array) {
        my $obj = new MARC::NDLSH::Node $row[7];
        push @set_word, $obj;
    }
    return @set_word;

}

1;
__END__

=head1 NAME

MARC::NDLSH - 国会図書館件名標目表(NDLSH)にアクセスするPerlモジュール

=head1 SYNOPSIS

  use MARC::NDLSH;

  my $obj = new MARC::NDLSH;

  # フレーズ「医学」から件名標目を探す
  my @node_objs = $obj->set_word("医学");

  # set_wordで見つけた件名標目のIDを得る
  print $node_objs[0]->getid, "\n";

  # set_wordで見つけた件名標目の件名標目形を得る
  print $node_objs[0]->as_NDLSH, "\n";

  # set_wordで見つけた件名標目のSN(Scope Note)を得る
  print $node_objs[0]->SN, "\n";

  # set_wordで見つけた件名標目のSA(参照注記)を得る
  print $node_objs[0]->SA, "\n";

  # set_wordで見つけた件名標目の日本十進分類（第９版）を得る
  print $node_objs[0]->NDC9, "\n";

  # set_wordで見つけた件名標目の国会図書館分類(NDLC)を得る
  print $node_objs[0]->NDLC, "\n";

  # set_wordで見つけた件名標目の「読み」を得る
  print $node_objs[0]->yomi, "\n";


  # set_wordで見つけた件名標目のRT(関連語)を得る
  my @related_objs = $node_objs[0]->RT;
  foreach $obj (@related_objs) {
      print $obj->as_NDLSH, "\n";
  }

  # set_wordで見つけた件名標目のBT(上位語)を得る
  my @related_objs = $node_objs[0]->BT;
  foreach $obj (@related_objs) {
      print $obj->as_NDLSH, "\n";
  }

  # set_wordで見つけた件名標目のNT(下位語)を得る
  my @related_objs = $node_objs[0]->NT;
  foreach $obj (@related_objs) {
      print $obj->as_NDLSH, "\n";
  }

  # set_wordで見つけた件名標目の類義語(USE and USE FOR)を得る
  foreach my $word ($node_objs[0]->simular) {
      print $word, "\n";
  }

=cut

=head1 DESCRIPTION

国会図書館件名標目表(NDLSH)のデータにアクセスするためのPerlモジュールです。
国会図書館が配布するNDLSHは、タブ区切りテキストデータであり、そのままでは
Perlからアクセスすることができません。そこで、Perlからアクセスするための
モジュールを作成しました。

=over 4

=item * Perlのオブジェクトを使い件名標目のグラフ構造を表現しています

=item * 用語間の関連は件名標目のIDでリンクしていますが、それを隠蔽しています

=item * 用語間の関連を得る際は、件名標目形もその参照形も等価に扱います。
つまり、件名標目形とその参照形をグループ化しています。

=item * 現在のところ主標目にしか対応していません、また件名の後の限定(括弧書き）
にも未対応です。

=back

=head2 EXPORT

None by default.

=head1 SEE ALSO

国会図書館件名標目の情報とデータは次を参照ください。
http://www.ndl.go.jp/jp/library/data/ndl_ndlsh.html

=head1 AUTHOR

Akira MaedaE<lt>maeda@lib.u-tokyo.ac.jpE<gt>

=head1 COPYRIGHT AND LICENSE

Copyright (C) 2009 by Akira Maeda

This library is free software; you can redistribute it and/or modify
it under the same terms as Perl itself, either Perl version 5.8.8 or,
at your option, any later version of Perl 5 you may have available.


=cut
