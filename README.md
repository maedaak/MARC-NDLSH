# MARC-NDLSH (Python 3版)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Perl%20Artistic%20%2F%20MIT-green.svg)](LICENSE)

国立国会図書館件名標目表（NDLSH: National Diet Library Subject Headings）を SQLite データベース化し、Python 3 から高速に検索・参照するためのライブラリです。

件名標目（優先語）だけでなく、同義語（非優先語／参照形）、上位語（BT）、下位語（NT）、関連語（RT）、分類記号（NDC第9版、NDC第10版、NDLC）、注記、読み、LCSH（米国議会図書館典拠番号）などのシソーラス構造・メタデータにアクセスできます。

---

## データの出典について

本パッケージで作成・利用する国立国会図書館件名標目表（NDLSH）のデータベースは、国立国会図書館の典拠データ検索・提供サービス**「[Web NDL Authorities](https://id.ndl.go.jp/information/download/#anchor01)」**にて配布されている最新の**「TAB区切りテキスト形式データ（ndlsh-tsv.zip）」**から生成しています。

- **データ提供元**: 国立国会図書館「Web NDL Authorities」
  - 一括ダウンロードページ: https://id.ndl.go.jp/information/download/#anchor01
  - 利用条件: https://id.ndl.go.jp/information/use/
- **ダウンロード対象データ**: NDLSH「TAB区切りテキスト形式データ」（日次更新）

> **Note**: 当データを利用した成果物を公表・配布する際には、Web NDL Authorities から取得したデータであることを明示してください。

---

## 主な機能

- **最新TSVフォーマット対応**: Web NDL Authorities の 18 カラム TSV 形式（UTF-8）を完全解析。
- **柔軟なDB構築**: 公式サイトからの自動ワンストップダウンロード＆ビルド、またはローカルの ZIP / TSV ファイルからの高速ビルド（約2万件を数秒でSQLite化）。
- **Perl版 MARC::NDLSH 完全互換**:
  - `NDLSH` クラス（`set_word`, `get_node` 等）
  - `NDLSHNode` クラス（`getid`, `as_NDLSH`, `SN`, `SA`, `NDC9`, `NDLC`, `yomi`, `RT`, `BT`, `NT`, `simular` 等）
  - `simple` 関数群（`NDLSH`, `SimmularTerms`, `RelatedTerms`, `BroaderTerms`, `NallowerTerms` 等）
- **Pythonicなインターフェイス**: プロパティアクセス（`node.id`, `node.ndlsh`, `node.ndc9`, `node.ndc10`, `node.lcsh`, `node.note` 等）やスネークケースメソッド（`node.related_terms()`, `simple.similar_terms()` 等）もサポート。

---

## インストール

```bash
git clone https://github.com/<username>/MARC-NDLSH.git
cd MARC-NDLSH
pip install -e .
```

---

## データベースの作成

NDLSH を検索するために、まず Web NDL Authorities のデータから SQLite データベースを作成します。

### 方法 1: Web NDL Authorities から自動ダウンロードして作成（推奨）

```bash
python scripts/make_ndlshdb.py --download
```
または引数なしで実行すると自動で最新データを取得します：
```bash
python scripts/make_ndlshdb.py
```

### 方法 2: 手動でダウンロードしたファイルから作成

1. [Web NDL Authorities ダウンロードページ](https://id.ndl.go.jp/information/download/#anchor01) から「TAB区切りテキスト形式データ」（`ndlsh-tsv.zip`）をダウンロードします。
2. スクリプトに ZIP ファイル（または解凍後の `ndlsh-tsv.tsv`）を指定して実行します：

```bash
# ZIP ファイルから直接作成
python scripts/make_ndlshdb.py ndlsh-tsv.zip

# または解凍した TSV ファイルから作成
python scripts/make_ndlshdb.py ndlsh-tsv.tsv
```

### 出力先の指定

デフォルトでは `src/marc_ndlsh/data/ndlsh.db` に作成されます。別の場所に出力したい場合は `--db` オプションを指定できます：

```bash
python scripts/make_ndlshdb.py --download --db /path/to/my_ndlsh.db
```

環境変数 `NDLSH_DB_PATH` を設定することで、Python ライブラリ側でも任意の DB パスを既定値として利用できます。

---

## 使い方

### 1. オブジェクト指向 API (`NDLSH`, `NDLSHNode`)

```python
from marc_ndlsh import NDLSH

# インスタンス作成（デフォルトのDBを参照）
client = NDLSH()

# フレーズやキーワードから件名標目を検索（同義語・参照形からも検索可能）
nodes = client.set_word("オフショア風力発電")

for node in nodes:
    print(f"ID: {node.getid()}")              # 例: 001092249
    print(f"件名標目: {node.as_NDLSH()}")     # 例: 洋上風力発電
    print(f"読み: {node.yomi()}")             # 例: ヨウジョウ フウリョク ハツデン
    print(f"NDC9: {node.NDC9()}")             # 例: 543.6
    print(f"NDC10: {node.NDC10()}")           # 例: 543.6
    print(f"NDLC: {node.NDLC()}")             # 例: DL231;ND158
    print(f"注記(SN): {node.SN()}")           # 例: 地理区分.
    print(f"LCSH: {node.LCSH()}")             # 例: sh2011004061

    # 上位語 (BT: Broader Terms)
    print("--- 上位語 (BT) ---")
    for bt in node.BT():
        print(f"  {bt.as_NDLSH()} ({bt.getid()})")

    # 下位語 (NT: Narrower Terms)
    print("--- 下位語 (NT) ---")
    for nt in node.NT():
        print(f"  {nt.as_NDLSH()} ({nt.getid()})")

    # 関連語 (RT: Related Terms)
    print("--- 関連語 (RT) ---")
    for rt in node.RT():
        print(f"  {rt.as_NDLSH()} ({rt.getid()})")

    # 類似語・同義語（標目形およびすべての参照形/USE・同義語）
    print("--- 類似語/同義語 ---")
    for term in node.simular():
        print(f"  {term}")
```

### 2. 関数型インターフェイス (`simple`)

Perl版 `MARC::NDLSH::Simple` と同様のシンプルな関数型呼び出しが可能です。

```python
from marc_ndlsh import simple

term = "洋上風力発電"

# 件名標目形を得る
print("標目形:", simple.NDLSH("オフショア風力発電"))
# => ['洋上風力発電']

# 類似語・同義語を得る（入力語自身は除外）
print("類似語:", simple.SimmularTerms(term))
# => ['オフショア風力発電', '海上風力発電', 'Offshore wind power plants']

# 上位語を得る
print("上位語:", simple.BroaderTerms(term))
# => ['風力発電']

# 関連語を得る
print("関連語:", simple.RelatedTerms(term))
# => ['海洋開発']

# 下位語を得る
print("下位語:", simple.NallowerTerms("風力発電"))
# => ['洋上風力発電', ...]
```

---

## データベーススキーマ

SQLite には以下の 3 つのテーブルと検索用インデックスが作成されます。

### `redirect` テーブル
キーワード（標目形・同義語）から件名標目 ID を引くためのテーブルです。
- `word`: 用語（限定語や細目を除去した主キーワード）
- `subdivision1`〜`subdivision4`: 細目（`--` で連結された細目）
- `limitation`: 限定語（末尾のカッコ書き）
- `yomi`: 読み
- `id`: NDLSH ID
- `is_ndlsh`: 標目自身の場合は `1`、同義語（参照形）の場合は `0`

### `SH` テーブル
件名標目の詳細メタデータを保持するメインテーブルです。
- `id`: NDLSH ID（主キー）
- `ndlsh`: 件名標目形
- `SN`: 注記（Scope Note）
- `SA`: 参照注記（See Also）
- `NDC9`: 日本十進分類法（第9版）
- `NDLC`: 国会図書館分類記号
- `yomi`: 標目読み
- `NDC10`: 日本十進分類法（第10版）
- `LCSH`: 米国議会図書館典拠番号
- `note`: 注記
- `created`: 新規作成日
- `modified`: 最終更新日

### `link` テーブル
用語間のリンク関係を管理するテーブルです。
- `from_id`: 起点 ID
- `to_id`: リンク先 ID
- `relation`: 関係種別（`BT`: 上位語, `NT`: 下位語, `RT`: 関連語）

---

## テストの実行

```bash
python -m unittest discover -s tests
```

---

## ライセンス・著作権

Copyright (C) 2009-2026 Akira Maeda.

This library is free software; you can redistribute it and/or modify it under the same terms as Perl itself (Artistic License or GPL), or under the MIT License.
