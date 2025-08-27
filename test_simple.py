"""Simple test to verify VSCode test discovery is working."""

import unittest

class TestSimple(unittest.TestCase):
    def test_simple(self):
        """A simple test that should be discovered by VSCode."""
        self.assertEqual(1 + 1, 2)

    def test_another_simple(self):
        """Another simple test."""
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
