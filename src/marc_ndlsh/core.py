"""MARC::NDLSH コアクラスモジュール

NDLSH (検索エンジン) および NDLSHNode (件名標目ノード) を提供します。
"""

import os
import re
import sqlite3
from typing import List, Optional
from .db import get_default_db_path


class NDLSHNode:
    """件名標目の単一ノードを表すクラス。
    Perl版 MARC::NDLSH::Node と互換のメソッドおよび Pythonic なプロパティを提供します。
    """

    def __init__(self, node_id: str, db_path: Optional[str] = None):
        self._id = str(node_id)
        self.db_path = db_path or get_default_db_path()
        self._sh_data = None

    def _connect(self) -> sqlite3.Connection:
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"NDLSH database file not found: {self.db_path}\n"
                "Please run make_ndlshdb or build_ndlsh_db() first."
            )
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_sh_field(self, field_name: str):
        if self._sh_data is None:
            conn = self._connect()
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM SH WHERE id = ?", (self._id,))
                row = cur.fetchone()
                self._sh_data = dict(row) if row else {}
            finally:
                conn.close()
        return self._sh_data.get(field_name)

    # --- Perl 互換メソッド ---

    def getid(self) -> str:
        """NDLSHのID番号を返します。"""
        return self._id

    def as_NDLSH(self) -> Optional[str]:
        """件名標目形を返します。"""
        return self._get_sh_field("ndlsh")

    def SN(self) -> Optional[str]:
        """SN (Scope Note / 注記) を返します。"""
        return self._get_sh_field("SN")

    def SA(self) -> Optional[str]:
        """SA (参照注記) を返します。"""
        return self._get_sh_field("SA")

    def NDC9(self) -> Optional[str]:
        """日本十進分類法（第9版）の分類記号を返します。"""
        return self._get_sh_field("NDC9")

    def NDLC(self) -> Optional[str]:
        """国立国会図書館分類表（NDLC）の分類記号を返します。"""
        return self._get_sh_field("NDLC")

    def yomi(self) -> Optional[str]:
        """件名標目のカタカナ読みを返します。"""
        return self._get_sh_field("yomi")

    def NDC10(self) -> Optional[str]:
        """日本十進分類法（第10版）の分類記号を返します。"""
        return self._get_sh_field("NDC10")

    def LCSH(self) -> Optional[str]:
        """米国議会図書館典拠番号（LCCN）を返します。"""
        return self._get_sh_field("LCSH")

    def note(self) -> Optional[str]:
        """注記を返します。"""
        return self._get_sh_field("note")

    def created(self) -> Optional[str]:
        """作成日を返します。"""
        return self._get_sh_field("created")

    def modified(self) -> Optional[str]:
        """最終更新日を返します。"""
        return self._get_sh_field("modified")

    # --- リンク関連メソッド ---

    def _get_links(self, relation: str) -> List["NDLSHNode"]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT to_id FROM link WHERE from_id = ? AND relation = ?",
                (self._id, relation)
            )
            rows = cur.fetchall()
            return [NDLSHNode(r["to_id"], db_path=self.db_path) for r in rows]
        finally:
            conn.close()

    def RT(self) -> List["NDLSHNode"]:
        """関連語 (Related Terms) の NDLSHNode リストを返します。"""
        return self._get_links("RT")

    def BT(self) -> List["NDLSHNode"]:
        """上位語 (Broader Terms) の NDLSHNode リストを返します。"""
        return self._get_links("BT")

    def NT(self) -> List["NDLSHNode"]:
        """下位語 (Narrower Terms) の NDLSHNode リストを返します。"""
        return self._get_links("NT")

    def simular(self) -> List[str]:
        """類似語・同義語（標目形およびすべての参照形/USE・同義語）のリストを返します。
        Perl版 MARC::NDLSH::Node::simular と完全互換です。
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT word, subdivision1, subdivision2, subdivision3, subdivision4, limitation "
                "FROM redirect WHERE id = ?",
                (self._id,)
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        results = []
        for row in rows:
            word = row["word"] or ""
            sub1 = row["subdivision1"]
            sub2 = row["subdivision2"]
            sub3 = row["subdivision3"]
            sub4 = row["subdivision4"]
            limitation = row["limitation"]

            # 英数字のみで構成されているか判定
            if re.match(r"^[\w\s\-]+$", word):
                if limitation:
                    word += f"({limitation})"
                if sub1:
                    word += f" -- {sub1}"
                if sub2:
                    word += f" -- {sub2}"
                if sub3:
                    word += f" -- {sub3}"
                if sub4:
                    word += f" -- {sub4}"
            else:
                if limitation:
                    word += f"（{limitation}）"
                if sub1:
                    word += f"--{sub1}"
                if sub2:
                    word += f"--{sub2}"
                if sub3:
                    word += f"--{sub3}"
                if sub4:
                    word += f"--{sub4}"

            results.append(word)

        return results

    # --- Pythonic エイリアス ---

    @property
    def id(self) -> str:
        return self.getid()

    @property
    def ndlsh(self) -> Optional[str]:
        return self.as_NDLSH()

    def related_terms(self) -> List["NDLSHNode"]:
        return self.RT()

    def broader_terms(self) -> List["NDLSHNode"]:
        return self.BT()

    def narrower_terms(self) -> List["NDLSHNode"]:
        return self.NT()

    def similar_terms(self) -> List[str]:
        return self.simular()

    def __repr__(self) -> str:
        term = self.as_NDLSH()
        return f"<NDLSHNode id={self._id!r} ndlsh={term!r}>"

    def __str__(self) -> str:
        return self.as_NDLSH() or self._id


class NDLSH:
    """国会図書館件名標目表 (NDLSH) へのアクセスインターフェイス。
    Perl版 MARC::NDLSH と互換性があります。
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_default_db_path()

    def _connect(self) -> sqlite3.Connection:
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"NDLSH database file not found: {self.db_path}\n"
                "Please run make_ndlshdb or build_ndlsh_db() first."
            )
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def set_word(self, word: str) -> List[NDLSHNode]:
        """フレーズまたは見出し語から件名標目を検索し、該当する NDLSHNode のリストを返します。
        Perl版 MARC::NDLSH::set_word と完全互換です。
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM redirect WHERE word = ?", (word,))
            rows = cur.fetchall()
        finally:
            conn.close()

        # 同一IDが重複する場合は一意にしつつ順序維持
        seen = set()
        nodes = []
        for r in rows:
            node_id = r["id"]
            if node_id not in seen:
                seen.add(node_id)
                nodes.append(NDLSHNode(node_id, db_path=self.db_path))
        return nodes

    def get_node(self, node_id: str) -> Optional[NDLSHNode]:
        """IDから直接 NDLSHNode を取得します。存在しない場合は None を返します。"""
        node = NDLSHNode(node_id, db_path=self.db_path)
        if node.as_NDLSH() is not None:
            return node
        return None

    def search(self, word: str) -> List[NDLSHNode]:
        """set_word の Pythonic エイリアス。"""
        return self.set_word(word)
