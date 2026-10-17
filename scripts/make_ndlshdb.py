#!/usr/bin/env python3
"""国立国会図書館件名標目表（NDLSH）の最新TAB区切りテキスト形式データから
SQLiteデータベースを作成するスクリプト。

データ元: Web NDL Authorities (https://id.ndl.go.jp/information/download/#anchor01)

使用例:
    # Web NDL Authorities から最新データを自動ダウンロードして作成
    python scripts/make_ndlshdb.py --download

    # ダウンロード済みの zip ファイルまたは解凍済み tsv ファイルから作成
    python scripts/make_ndlshdb.py ndlsh-tsv.zip
    python scripts/make_ndlshdb.py ndlsh-tsv.tsv

    # 出力先 DB を指定
    python scripts/make_ndlshdb.py ndlsh-tsv.zip --db my_ndlsh.db
"""

import argparse
import os
import sys
import time

# パッケージ未インストール時でも src から直接インポート可能にする
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(script_dir, "..", "src"))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from marc_ndlsh.db import build_ndlsh_db, get_default_db_path, WEB_NDL_AUTHORITIES_TSV_URL


def main():
    parser = argparse.ArgumentParser(
        description="Web NDL Authorities の TAB区切りテキスト形式データから NDLSH SQLite DB を作成します。"
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        help="入力TSVファイル、ZIPファイル、またはURL。省略時は --download 指定または最新ZIPを自動取得します。",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help=f"Web NDL Authorities ({WEB_NDL_AUTHORITIES_TSV_URL}) から最新データをダウンロードして作成します。",
    )
    parser.add_argument(
        "--db",
        default=None,
        help="出力先 SQLite DB ファイルパス（デフォルト: marc_ndlsh/data/ndlsh.db）",
    )

    args = parser.parse_args()

    source = args.source
    if args.download or source is None:
        source = WEB_NDL_AUTHORITIES_TSV_URL
        print(f"[*] Downloading latest NDLSH TSV data from: {WEB_NDL_AUTHORITIES_TSV_URL}")
    else:
        print(f"[*] Loading NDLSH data from: {source}")

    db_path = args.db or get_default_db_path()
    print(f"[*] Target SQLite DB: {db_path}")

    start_time = time.time()

    def on_progress(count: int):
        print(f"    ... processed {count:,} records", flush=True)

    try:
        out_path = build_ndlsh_db(
            source=source,
            db_path=db_path,
            progress_callback=on_progress,
        )
        elapsed = time.time() - start_time
        print(f"[+] Successfully built NDLSH database: {out_path} ({elapsed:.2f} seconds)")
    except Exception as e:
        print(f"[!] Error building database: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
