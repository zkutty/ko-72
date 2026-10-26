"""The printed food index must preserve source coverage while merging aliases."""

import unittest

from book.build_glossary_index import collapse, paginate


def entry(label, english, written, romaji, catalog, seasons):
    return {
        "category": "fish", "display_name": label, "english": english,
        "kanji": written, "kana": "さけ", "romaji": romaji,
        "catalog_key": catalog, "source_labels": [label],
        "season_ids": seasons,
        "season_refs": [{"id": sid, "name_en": f"Season {sid}"} for sid in seasons],
    }


class GlossaryIndexTests(unittest.TestCase):
    def test_salmon_aliases_merge_and_keep_all_seasons(self):
        raw = {"scope": "test", "source_seasons": 3, "source_mentions": 3,
               "entries": [
                   entry("Sake (salmon)", "Salmon", "鮭", "sake", "salmon-sake", [48]),
                   entry("Salmon (aki-sake)", "Salmon", "秋鮭", "aki-sake", "salmon-aki", [52]),
                   entry("Salmon (sake)", "Salmon", "鮭", "sake", "salmon-sake", [53]),
               ]}
        index, report, labels = collapse(raw)
        self.assertEqual(index["entry_count"], 1)
        self.assertEqual(index["entries"][0]["season_ids"], [48, 52, 53])
        self.assertEqual(len(index["entries"][0]["source_entries"]), 3)
        self.assertEqual(report["collapsed_entries"], 2)
        self.assertEqual(len(set(labels.values())), 1)
        self.assertEqual(index["entries"][0]["identity_review_status"],
                         "needs_editorial_review")

    def test_distinct_foods_do_not_merge_without_exact_identity(self):
        raw = {"scope": "test", "source_seasons": 2, "source_mentions": 2,
               "entries": [
                   entry("Salmon", "Salmon", "鮭", "sake", "salmon", [48]),
                   entry("Trout", "Trout", "鱒", "masu", "trout", [52]),
               ]}
        index, report, _ = collapse(raw)
        self.assertEqual(index["entry_count"], 2)
        self.assertEqual(report["collapsed_entries"], 0)

    def test_paginate_requires_two_distinct_illustrated_foods(self):
        foods = [{"id": str(i)} for i in range(8)]
        pages = paginate(foods, {str(i) for i in (0, 2, 4, 7)})
        self.assertEqual(sum(map(len, pages)), 8)
        self.assertTrue(all(len(page) <= 6 for page in pages))
        self.assertTrue(all(sum(e["id"] in {"0", "2", "4", "7"}
                                for e in page) >= 2 for page in pages))
        with self.assertRaisesRegex(ValueError, "two distinct"):
            paginate(foods, {"0", "7"})


if __name__ == "__main__":
    unittest.main()
