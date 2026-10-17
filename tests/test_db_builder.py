import io
import os
import sys
import tempfile
import unittest
import zipfile

src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from marc_ndlsh.db import build_ndlsh_db, get_default_db_path
from marc_ndlsh import NDLSH


class TestDBBuilder(unittest.TestCase):
    def test_build_from_zip(self):
        sample_tsv = (
            "件名標目\t標目よみ\tID\t同義語\t上位語\t下位語\t関連語\t注記\t分類記号(NDLC)\t分類記号(NDC9)\t分類記号(NDC10)\t参照(LCSH)\t参照(BSH4)\t出典(BSH4)\t出典\t編集履歴\t作成日\t最終更新日\n"
            "医学\tイガク\t00563816\tMedicine\t\t内科学<00567990>\t医療<00564245>\t\tSC\t490\t490\tsh85083064\t\t\t\t\t2000-01-01\t2020-01-01\n"
            "内科学\tナイカガク\t00567990\tInternal medicine\t医学<00563816>\t\t\t\tSC211\t493\t493\t\t\t\t\t\t2000-01-01\t2020-01-01\n"
        )
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            zip_path = os.path.join(temp_dir, "ndlsh-tsv.zip")
            db_path = os.path.join(temp_dir, "ndlsh.db")

            # Zipファイルを作成
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("ndlsh-tsv.tsv", sample_tsv.encode("utf-8"))

            # ZIP から DB ビルド
            out = build_ndlsh_db(source=zip_path, db_path=db_path)
            self.assertTrue(os.path.exists(out))

            # 検索テスト
            client = NDLSH(db_path=db_path)
            nodes = client.set_word("医学")
            self.assertEqual(len(nodes), 1)
            node = nodes[0]
            self.assertEqual(node.as_NDLSH(), "医学")
            self.assertEqual(node.getid(), "00563816")
            self.assertEqual(node.NDC9(), "490")

            # 下位語
            nt = node.NT()
            self.assertEqual(len(nt), 1)
            self.assertEqual(nt[0].as_NDLSH(), "内科学")

            # 内科学の上位語
            naika_nodes = client.set_word("内科学")
            self.assertEqual(len(naika_nodes), 1)
            bt = naika_nodes[0].BT()
            self.assertEqual(len(bt), 1)
            self.assertEqual(bt[0].as_NDLSH(), "医学")


if __name__ == "__main__":
    unittest.main()
