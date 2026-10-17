import io
import os
import sys

# src ディレクトリを sys.path に追加
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import sqlite3
import tempfile
import unittest

from marc_ndlsh.db import build_ndlsh_db, clean_term, extract_limitation, split_subdivisions, parse_synonyms, extract_links
from marc_ndlsh import NDLSH, simple


class TestNDLSH(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 擬似的な Web NDL Authorities TSV データを作成
        tsv_content = (
            "件名標目\t標目よみ\tID\t同義語\t上位語\t下位語\t関連語\t注記\t分類記号(NDLC)\t分類記号(NDC9)\t分類記号(NDC10)\t参照(LCSH)\t参照(BSH4)\t出典(BSH4)\t出典\t編集履歴\t作成日\t最終更新日\n"
            "風力発電\tフウリョク ハツデン\t00575250\tWind power plants\t発電<00569940>\t洋上風力発電<001092249>\t風車<00563456>\t注記テスト\tDL231\t543.6\t543.6\tsh85146930\t\t\t出典テスト\t\t2000-01-01\t2020-01-01\n"
            "洋上風力発電\tヨウジョウ フウリョク ハツデン\t001092249\tオフショア風力発電[オフショア フウリョク ハツデン];海上風力発電[カイジョウ フウリョク ハツデン];Offshore wind power plants\t風力発電<00575250>\t\t海洋開発<00564600>\t地理区分.\tDL231;ND158\t543.6\t543.6\tsh2011004061\t\t\t報告書\t\t2011-12-12\t2017-10-27\n"
            "防災教育 (学校)\tボウサイ キョウイク (ガッコウ)\t001100000\t学校防災\t防災教育<001099999>\t\t\t注記\tFB\t374\t374\t\t\t\t\t\t2012-01-01\t2012-01-01\n"
            "ロシア--歴史--ソビエト連邦時代\tロシア--レキシ--ソビエト レンポウ ジダイ\t001099504\t\t\t\t\t\tGE\t238\t238\t\t\t\t\t\t2011-01-01\t2011-01-01\n"
        )
        cls.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.db_path = os.path.join(cls.temp_dir.name, "test_ndlsh.db")
        stream = io.StringIO(tsv_content)
        build_ndlsh_db(source=stream, db_path=cls.db_path)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.temp_dir.cleanup()
        except Exception:
            pass

    def test_term_helpers(self):
        self.assertEqual(clean_term("《※洋上風力発電〈テスト〉》"), "洋上風力発電")
        word, lim = extract_limitation("防災教育 (学校)")
        self.assertEqual(word, "防災教育")
        self.assertEqual(lim, "学校")

        w, s1, s2, s3, s4, lim2 = split_subdivisions("ロシア--歴史--ソビエト連邦時代")
        self.assertEqual(w, "ロシア")
        self.assertEqual(s1, "歴史")
        self.assertEqual(s2, "ソビエト連邦時代")
        self.assertIsNone(s3)

        syns = parse_synonyms("オフショア風力発電[オフショア フウリョク ハツデン];Offshore wind power plants")
        self.assertEqual(len(syns), 2)
        self.assertEqual(syns[0], ("オフショア風力発電", "オフショア フウリョク ハツデン"))
        self.assertEqual(syns[1], ("Offshore wind power plants", None))

        links = extract_links("風力発電<00575250>;風車<00563456>")
        self.assertEqual(links, ["00575250", "00563456"])

    def test_ndlsh_search(self):
        ndlsh = NDLSH(db_path=self.db_path)

        # 標目自身で検索
        nodes = ndlsh.set_word("洋上風力発電")
        self.assertEqual(len(nodes), 1)
        node = nodes[0]
        self.assertEqual(node.getid(), "001092249")
        self.assertEqual(node.as_NDLSH(), "洋上風力発電")
        self.assertEqual(node.yomi(), "ヨウジョウ フウリョク ハツデン")
        self.assertEqual(node.NDC9(), "543.6")
        self.assertEqual(node.NDLC(), "DL231;ND158")
        self.assertEqual(node.SN(), "地理区分.")

        # 同義語（参照形）で検索
        syn_nodes = ndlsh.set_word("オフショア風力発電")
        self.assertEqual(len(syn_nodes), 1)
        self.assertEqual(syn_nodes[0].getid(), "001092249")
        self.assertEqual(syn_nodes[0].as_NDLSH(), "洋上風力発電")

        # 限定語付き標目の検索（カッコなしの語でヒット）
        bousai_nodes = ndlsh.set_word("防災教育")
        self.assertTrue(len(bousai_nodes) >= 1)
        self.assertEqual(bousai_nodes[0].getid(), "001100000")

        # 細目付き標目の検索（主標目でヒット）
        russia_nodes = ndlsh.set_word("ロシア")
        self.assertTrue(len(russia_nodes) >= 1)
        self.assertEqual(russia_nodes[0].getid(), "001099504")

    def test_links(self):
        ndlsh = NDLSH(db_path=self.db_path)
        nodes = ndlsh.set_word("洋上風力発電")
        node = nodes[0]

        # 上位語 (BT)
        bt_nodes = node.BT()
        self.assertEqual(len(bt_nodes), 1)
        self.assertEqual(bt_nodes[0].as_NDLSH(), "風力発電")

        # 風力発電の下位語 (NT)
        furyoku_nodes = ndlsh.set_word("風力発電")
        nt_nodes = furyoku_nodes[0].NT()
        self.assertEqual(len(nt_nodes), 1)
        self.assertEqual(nt_nodes[0].as_NDLSH(), "洋上風力発電")

    def test_simular(self):
        ndlsh = NDLSH(db_path=self.db_path)
        nodes = ndlsh.set_word("洋上風力発電")
        node = nodes[0]
        sims = node.simular()
        # 標目自身と各同義語が含まれていること
        self.assertIn("洋上風力発電", sims)
        self.assertIn("オフショア風力発電", sims)
        self.assertIn("海上風力発電", sims)
        self.assertIn("Offshore wind power plants", sims)

    def test_simple_functions(self):
        # simple.NDLSH
        sh_terms = simple.NDLSH("オフショア風力発電", db_path=self.db_path)
        self.assertEqual(sh_terms, ["洋上風力発電"])

        # simple.SimmularTerms (自身は除外)
        sim_terms = simple.SimmularTerms("洋上風力発電", db_path=self.db_path)
        self.assertNotIn("洋上風力発電", sim_terms)
        self.assertIn("オフショア風力発電", sim_terms)

        # simple.BroaderTerms
        bt_terms = simple.BroaderTerms("洋上風力発電", db_path=self.db_path)
        self.assertEqual(bt_terms, ["風力発電"])

        # simple.NallowerTerms
        nt_terms = simple.NallowerTerms("風力発電", db_path=self.db_path)
        self.assertEqual(nt_terms, ["洋上風力発電"])


if __name__ == "__main__":
    unittest.main()
