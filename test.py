#!/usr/bin/env python
import unittest
from server import UDPHandler, FileRequestManager

class TestUdpHandler(unittest.TestCase):

    def setUp(self):
        self.handler = UDPHandler()

class TestFileRequestManager(unittest.TestCase):

    def setUp(self):
        self.manager = FileRequestManager()


if __name__ == "__main__":
    print unittest.main()