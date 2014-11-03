#!/usr/bin/env python
import unittest
import struct
import mock
from server import UDPHandler, FileRequestManager, OP_RRQ, OP_DATA
from cStringIO import StringIO

class TestUdpHandler(unittest.TestCase):

    def setUp(self):
        self.mock_sock = mock.Mock()
        self.server = mock.Mock()
        self.client_address = ("localhost", "65534")

        self.file = StringIO()
        self.file.write("1" * 512)  # Block 1 has all 1s in it
        self.file.write("2" * 512)  # Block 2 has all 2s in it
        self.file.write("3" * 256)  # Half full block 3 has all 3s in it.
        self.manager = FileRequestManager(self.file)

    def configure_udp_handler_with_request(self, data):
        """
        This creates a UDPHandler, which processes the request right away.
        """
        request = (data, self.mock_sock)
        return UDPHandler(request, self.client_address, self.server)

    def test_rrq(self):
        rrq = struct.pack("!H10sB8sB", OP_RRQ, "readme.txt", 0, "netascii", 0)
        self.configure_udp_handler_with_request(rrq)
        expected_block_number = 1
        expected_data_response = struct.pack("!HH512s", OP_DATA, expected_block_number, "1"*512)
        self.mock_sock.sendto.assert_called_with(expected_data_response, self.client_address)


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