"""MARC::NDLSH::Simple 関数型インターフェイスモジュール

国会図書館件名標目 (NDLSH) から手軽に情報を取得できる関数群を提供します。
Perl版 MARC::NDLSH::Simple と完全互換です。
"""

from typing import List, Optional
from .core import NDLSH as NDLSHClient


def NDLSH_terms(any_term: str, db_path: Optional[str] = None) -> List[str]:
    """国会図書館件名標目の件名標目形を得ます。該当がない場合は空リストを返します。"""
    obj = NDLSHClient(db_path=db_path)
    nodes = obj.set_word(any_term)
    results = []
    for node in nodes:
        term = node.as_NDLSH()
        if term and term not in results:
            results.append(term)
    return results


def SimmularTerms(any_term: str, db_path: Optional[str] = None) -> List[str]:
    """類似語・同義語（リンクしている件名標目形と参照形）を得ます（入力語句自身は除外）。"""
    obj = NDLSHClient(db_path=db_path)
    nodes = obj.set_word(any_term)
    relation = {}
    for node in nodes:
        for term in node.simular():
            if term != any_term:
                relation[term] = relation.get(term, 0) + 1
    return list(relation.keys())


def RelatedTerms(any_term: str, db_path: Optional[str] = None) -> List[str]:
    """関連語を得ます（入力語句自身は除外）。"""
    obj = NDLSHClient(db_path=db_path)
    nodes = obj.set_word(any_term)
    relation = {}
    for node in nodes:
        for t in node.RT():
            term = t.as_NDLSH()
            if term and term != any_term:
                relation[term] = relation.get(term, 0) + 1
    return list(relation.keys())


def BroaderTerms(any_term: str, db_path: Optional[str] = None) -> List[str]:
    """上位語を得ます（入力語句自身は除外）。"""
    obj = NDLSHClient(db_path=db_path)
    nodes = obj.set_word(any_term)
    relation = {}
    for node in nodes:
        for t in node.BT():
            term = t.as_NDLSH()
            if term and term != any_term:
                relation[term] = relation.get(term, 0) + 1
    return list(relation.keys())


def NallowerTerms(any_term: str, db_path: Optional[str] = None) -> List[str]:
    """下位語を得ます（入力語句自身は除外）。"""
    obj = NDLSHClient(db_path=db_path)
    nodes = obj.set_word(any_term)
    relation = {}
    for node in nodes:
        for t in node.NT():
            term = t.as_NDLSH()
            if term and term != any_term:
                relation[term] = relation.get(term, 0) + 1
    return list(relation.keys())


# Perl版の別名や大文字小文字の互換エイリアス
NDLSH = NDLSH_terms
NallowTerms = NallowerTerms

# Pythonic な小文字・スネークケース エイリアス
ndlsh = NDLSH_terms
simular_terms = SimmularTerms
similar_terms = SimmularTerms
related_terms = RelatedTerms
broader_terms = BroaderTerms
narrower_terms = NallowerTerms
