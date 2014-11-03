#!/usr/bin/env python
import unittest
from server import UDPHandler, FileRequestManager
from cStringIO import StringIO

class TestUdpHandler(unittest.TestCase):

    def setUp(self):
        self.handler = UDPHandler()

class TestFileRequestManager(unittest.TestCase):

    def setUp(self):
        self.file = StringIO()
        self.file.write("1" * 512)  # Block 1 has all 1s in it
        self.file.write("2" * 512)  # Block 2 has all 2s in it
        self.file.write("3" * 256)  # Half full block 3 has all 3s in it.
        self.manager = FileRequestManager(self.file)

    def test_get_block(self):
        self.assertEqual(self.manager.get_block(1), "1" * 512)
        self.assertEqual(self.manager.get_block(2), "2" * 512)
        self.assertEqual(self.manager.get_block(3), "3" * 256)


if __name__ == "__main__":
    print unittest.main()