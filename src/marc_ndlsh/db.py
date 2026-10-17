"""NDLSH SQLite データベースの構築・管理モジュール

Web NDL Authorities の「TAB区切りテキスト形式データ (ndlsh-tsv.zip / ndlsh-tsv.tsv)」
を読み込み、検索用のSQLiteデータベースを構築します。
"""

import io
import os
import re
import sqlite3
import urllib.request
import zipfile
from typing import Callable, Optional, Tuple, List, Union

WEB_NDL_AUTHORITIES_TSV_URL = "https://id.ndl.go.jp/auth/data/download/ndlsh-tsv.zip"


def get_default_db_path() -> str:
    """デフォルトの SQLite DB ファイルパスを返します。
    環境変数 NDLSH_DB_PATH が指定されている場合はそれを優先します。
    """
    env_path = os.environ.get("NDLSH_DB_PATH")
    if env_path:
        return env_path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "data", "ndlsh.db")


def clean_term(term: str) -> str:
    """用語文字列から不要な記号（※、〈...〉、先頭の《、末尾の》）を除去します。"""
    if not term:
        return ""
    t = term.strip()
    t = t.replace("※", "")
    t = re.sub(r"〈.*?〉", "", t)
    t = re.sub(r"^《", "", t)
    t = re.sub(r"》$", "", t)
    return t.strip()


def extract_limitation(term: str) -> Tuple[str, Optional[str]]:
    """用語末尾の限定語（カッコ書き）を抽出します。
    例: '防災教育 (学校)' -> ('防災教育', '学校')
        '洋上風力発電' -> ('洋上風力発電', None)
    """
    m = re.search(r"[\(（]([^\(\)（）]+)[\)）]\s*$", term)
    if m:
        limitation = m.group(1).strip()
        cleaned_term = term[:m.start()].strip()
        return cleaned_term, limitation
    return term, None


def split_subdivisions(term: str) -> Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """細目（-- 区切り）および主標目の限定語を分解します。
    戻り値: (word, sub1, sub2, sub3, sub4, limitation)
    """
    parts = re.split(r"\s*--\s*", term)
    main_part = clean_term(parts[0]) if parts else ""
    word, limitation = extract_limitation(main_part)

    subs: List[Optional[str]] = [None, None, None, None]
    for idx in range(1, min(len(parts), 5)):
        clean_sub = clean_term(parts[idx])
        subs[idx - 1] = clean_sub if clean_sub else None

    return word, subs[0], subs[1], subs[2], subs[3], limitation


def parse_synonyms(synonyms_text: str) -> List[Tuple[str, Optional[str]]]:
    """同義語フィールドを解析し、[(用語, 読み), ...] のリストを返します。
    例: 'オフショア風力発電[オフショア フウリョク ハツデン];海上風力発電[カイジョウ フウリョク ハツデン];Offshore wind power plants'
    """
    if not synonyms_text:
        return []
    results = []
    items = re.split(r"[;；]", synonyms_text)
    for item in items:
        item = item.strip()
        if not item:
            continue
        m = re.match(r"^(.*?)\[(.*?)\]$", item)
        if m:
            syn_term = m.group(1).strip()
            syn_yomi = m.group(2).strip() or None
            results.append((syn_term, syn_yomi))
        else:
            results.append((item, None))
    return results


def extract_links(link_field: str) -> List[str]:
    """上位語、下位語、関連語などのフィールドからリンク先 ID を抽出します。
    例: '建築士<00565615>;建築<00565563>' -> ['00565615', '00565563']
    """
    if not link_field:
        return []
    ids = []
    items = re.split(r"[;；]", link_field)
    for item in items:
        m = re.search(r"<(\d+)>", item)
        if m:
            ids.append(m.group(1))
    return ids


def init_db_schema(conn: sqlite3.Connection) -> None:
    """テーブルとインデックスを作成します。"""
    cursor = conn.cursor()

    cursor.executescript("""
    DROP TABLE IF EXISTS redirect;
    DROP TABLE IF EXISTS SH;
    DROP TABLE IF EXISTS link;

    -- キーワードから件名標目データを得るテーブル
    CREATE TABLE redirect (
        word         TEXT,
        subdivision1 TEXT,
        subdivision2 TEXT,
        subdivision3 TEXT,
        subdivision4 TEXT,
        limitation   TEXT,
        yomi         TEXT,
        id           TEXT,
        is_ndlsh     INTEGER
    );

    -- 件名標目 (メイン) テーブル
    CREATE TABLE SH (
        id       TEXT PRIMARY KEY,
        ndlsh    TEXT,
        SN       TEXT,
        SA       TEXT,
        NDC9     TEXT,
        NDLC     TEXT,
        yomi     TEXT,
        NDC10    TEXT,
        LCSH     TEXT,
        note     TEXT,
        created  TEXT,
        modified TEXT
    );

    -- リンクテーブル (BT, NT, RT)
    CREATE TABLE link (
        from_id  TEXT,
        to_id    TEXT,
        relation TEXT
    );
    """)
    conn.commit()


def create_indexes(conn: sqlite3.Connection) -> None:
    """インデックスを作成します。"""
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE INDEX IF NOT EXISTS word_idx ON redirect(word);
    CREATE INDEX IF NOT EXISTS subdivision1_idx ON redirect(subdivision1);
    CREATE INDEX IF NOT EXISTS subdivision2_idx ON redirect(subdivision2);
    CREATE INDEX IF NOT EXISTS subdivision3_idx ON redirect(subdivision3);
    CREATE INDEX IF NOT EXISTS subdivision4_idx ON redirect(subdivision4);
    CREATE INDEX IF NOT EXISTS limitation_idx ON redirect(limitation);
    CREATE INDEX IF NOT EXISTS redirectid_idx ON redirect(id);

    CREATE INDEX IF NOT EXISTS id_idx ON SH(id);
    CREATE INDEX IF NOT EXISTS ndlsh_idx ON SH(ndlsh);

    CREATE INDEX IF NOT EXISTS fromid_idx ON link(from_id);
    CREATE INDEX IF NOT EXISTS toid_idx ON link(to_id);
    """)
    conn.commit()


def open_tsv_stream(source: Optional[Union[str, io.IOBase]] = None):
    """入力ソース（URL, zipパス, tsvパス, None）からテキストストリームをオープンします。"""
    if source is None or source == "download" or (isinstance(source, str) and source.startswith("http")):
        url = source if (isinstance(source, str) and source.startswith("http")) else WEB_NDL_AUTHORITIES_TSV_URL
        req = urllib.request.Request(url, headers={"User-Agent": "MARC-NDLSH/0.1.0 (Python)"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            content = resp.read()
        z = zipfile.ZipFile(io.BytesIO(content))
        for name in z.namelist():
            if name.endswith(".tsv"):
                return io.TextIOWrapper(z.open(name), encoding="utf-8")
        raise ValueError(f"Zip archive from {url} does not contain any .tsv file")

    if isinstance(source, (str, bytes, os.PathLike)):
        path = str(source)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Input file not found: {path}")

        if path.lower().endswith(".zip"):
            z = zipfile.ZipFile(path)
            for name in z.namelist():
                if name.endswith(".tsv"):
                    return io.TextIOWrapper(z.open(name), encoding="utf-8")
            raise ValueError(f"Zip archive '{path}' does not contain any .tsv file")
        else:
            return open(path, "r", encoding="utf-8")

    if isinstance(source, io.IOBase):
        return source

    raise ValueError(f"Unsupported source type: {type(source)}")


def build_ndlsh_db(
    source: Optional[Union[str, io.IOBase]] = None,
    db_path: Optional[str] = None,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> str:
    """Web NDL Authorities の TSV データから SQLite データベースを構築します。

    Args:
        source: TSVファイルパス、ZIPファイルパス、URL、またはファイルストリーム。
                None の場合は公式 Web NDL Authorities より最新 zip をダウンロードします。
        db_path: 出力先 SQLite DB パス。None の場合はデフォルトパス。
        progress_callback: 進行状況コールバック (レコード数を引数に呼び出されます)。

    Returns:
        作成された SQLite DB の絶対パス。
    """
    if db_path is None:
        db_path = get_default_db_path()

    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    # 既存のDBファイルを削除または新規作成
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass

    conn = sqlite3.connect(db_path)
    init_db_schema(conn)

    stream = open_tsv_stream(source)

    redirect_records = []
    sh_records = []
    link_records = []

    count = 0
    header_skipped = False

    try:
        for line in stream:
            line = line.rstrip("\r\n")
            if not line:
                continue

            cols = line.split("\t")
            if not header_skipped:
                # 1行目がヘッダー（件名標目、標目よみ、ID...）ならスキップ
                header_skipped = True
                if cols[0] == "件名標目" or cols[2] == "ID":
                    continue

            # カラム数が足りない場合の安全策
            if len(cols) < 3:
                continue

            sh_term = cols[0].strip()
            sh_yomi = cols[1].strip() if len(cols) > 1 else ""
            sh_id = cols[2].strip()
            synonyms_str = cols[3].strip() if len(cols) > 3 else ""
            bt_str = cols[4].strip() if len(cols) > 4 else ""
            nt_str = cols[5].strip() if len(cols) > 5 else ""
            rt_str = cols[6].strip() if len(cols) > 6 else ""
            note_str = cols[7].strip() if len(cols) > 7 else ""
            ndlc_str = cols[8].strip() if len(cols) > 8 else ""
            ndc9_str = cols[9].strip() if len(cols) > 9 else ""
            ndc10_str = cols[10].strip() if len(cols) > 10 else ""
            lcsh_str = cols[11].strip() if len(cols) > 11 else ""
            created_str = cols[16].strip() if len(cols) > 16 else ""
            modified_str = cols[17].strip() if len(cols) > 17 else ""

            if not sh_id:
                continue

            # 1. 標目自身の redirect レコード登録 (is_ndlsh = 1)
            word, sub1, sub2, sub3, sub4, limitation = split_subdivisions(sh_term)
            redirect_records.append((
                word, sub1, sub2, sub3, sub4, limitation, sh_yomi, sh_id, 1
            ))

            # 2. 同義語の redirect レコード登録 (is_ndlsh = 0)
            synonyms = parse_synonyms(synonyms_str)
            for syn_term, syn_yomi in synonyms:
                syn_word, s1, s2, s3, s4, syn_limit = split_subdivisions(syn_term)
                if syn_word:
                    redirect_records.append((
                        syn_word, s1, s2, s3, s4, syn_limit, syn_yomi, sh_id, 0
                    ))

            # 3. link レコード登録 (BT, NT, RT)
            for to_id in extract_links(bt_str):
                link_records.append((sh_id, to_id, "BT"))
            for to_id in extract_links(nt_str):
                link_records.append((sh_id, to_id, "NT"))
            for to_id in extract_links(rt_str):
                link_records.append((sh_id, to_id, "RT"))

            # 4. SH レコード登録
            clean_sh = clean_term(sh_term)
            sn_val = note_str if note_str else None
            sa_val = None
            ndc9_val = ndc9_str if ndc9_str else None
            ndlc_val = ndlc_str if ndlc_str else None
            yomi_val = sh_yomi if sh_yomi else None
            ndc10_val = ndc10_str if ndc10_str else None
            lcsh_val = lcsh_str if lcsh_str else None
            created_val = created_str if created_str else None
            modified_val = modified_str if modified_str else None

            sh_records.append((
                sh_id, clean_sh, sn_val, sa_val, ndc9_val, ndlc_val, yomi_val,
                ndc10_val, lcsh_val, sn_val, created_val, modified_val
            ))

            count += 1
            if count % 5000 == 0:
                conn.cursor().executemany(
                    "INSERT INTO redirect VALUES (?,?,?,?,?,?,?,?,?)", redirect_records
                )
                conn.cursor().executemany(
                    "INSERT INTO SH VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", sh_records
                )
                conn.cursor().executemany(
                    "INSERT INTO link VALUES (?,?,?)", link_records
                )
                conn.commit()
                redirect_records.clear()
                sh_records.clear()
                link_records.clear()
                if progress_callback:
                    progress_callback(count)

        if redirect_records or sh_records or link_records:
            conn.cursor().executemany(
                "INSERT INTO redirect VALUES (?,?,?,?,?,?,?,?,?)", redirect_records
            )
            conn.cursor().executemany(
                "INSERT INTO SH VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", sh_records
            )
            conn.cursor().executemany(
                "INSERT INTO link VALUES (?,?,?)", link_records
            )
            conn.commit()

        if progress_callback:
            progress_callback(count)

    finally:
        if hasattr(stream, "close"):
            stream.close()

    create_indexes(conn)
    conn.close()

    return os.path.abspath(db_path)
