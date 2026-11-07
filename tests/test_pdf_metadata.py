"""Regressions for arXiv margin stamps being mistaken for paper titles."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'pdf_to_sections', Path(__file__).parents[1] / 'scripts' / 'pdf_to_sections.py'
)
extractor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extractor)


class TitleExtractionTests(unittest.TestCase):
    def test_large_arxiv_stamp_does_not_replace_multiline_title(self):
        blocks = [
            {'page': 1, 'size': 20, 'text': 'arXiv:1706.03762v7 [cs.CL] 2 Aug 2023'},
            {'page': 1, 'size': 17, 'text': 'Attention Is'},
            {'page': 1, 'size': 17, 'text': 'All You Need'},
            {'page': 1, 'size': 10, 'text': 'Abstract'},
            {'page': 1, 'size': 10, 'text': 'A model based on attention.'},
            {'page': 1, 'size': 12, 'text': '1 Introduction'},
        ]
        title, abstract = extractor.extract_title_authors_abstract(blocks)
        self.assertEqual(title, 'Attention Is All You Need')
        self.assertEqual(abstract, 'A model based on attention.')

    def test_plaintext_backend_ignores_stamp(self):
        blocks = [
            {'page': 1, 'size': None, 'text': 'arXiv:1706.03762v7 [cs.CL]'},
            {'page': 1, 'size': None, 'text': 'Attention Is All You Need'},
        ]
        title, _ = extractor.extract_title_authors_abstract(blocks)
        self.assertEqual(title, 'Attention Is All You Need')


if __name__ == '__main__':
    unittest.main()
