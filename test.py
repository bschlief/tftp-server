#!/usr/bin/env python
import unittest
import struct
import mock
from server import UDPHandler, FileRequestManager, OP_RRQ, OP_DATA
from cStringIO import StringIO
import os

class TestUdpHandler(unittest.TestCase):

    def setUp(self):
        self.mock_sock = mock.Mock()
        self.server = mock.Mock()
        self.client_address = ("localhost", "65534")

        self.path = os.path.dirname(__file__)
        self.test_file_name = "test_file_to_serve.txt"

        with open(os.path.join(self.path, self.test_file_name), "w") as f:
            f.write("1" * 512)  # Block 1 has all 1s in it
            f.write("2" * 512)  # Block 2 has all 2s in it
            f.write("3" * 256)  # Half full block 3 has all 3s in it.
        self.manager = FileRequestManager(self.path)
        self.manager.load_file(self.test_file_name)

    def tearDown(self):
        os.remove(os.path.join(self.path, self.test_file_name))

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
        self.test_file_name = "test_file_to_serve.txt"
        self.second_test_file_name = "second.txt"

        self.path = os.path.dirname(__file__)
        self.test_file_name = "test_file_to_serve.txt"

        with open(os.path.join(self.path, self.test_file_name), "w") as f:
            f.write("1" * 512)  # Block 1 has all 1s in it
            f.write("2" * 512)  # Block 2 has all 2s in it
            f.write("3" * 256)  # Half full block 3 has all 3s in it.



        self.manager = FileRequestManager(self.path)
        self.manager.load_file(self.test_file_name)

    def tearDown(self):
        os.remove(os.path.join(self.path, self.test_file_name))

        if os.path.exists(os.path.join(self.path, self.second_test_file_name)):
            os.remove(os.path.join(self.path, self.second_test_file_name))

    def test_get_block(self):
        self.assertEqual(self.manager.get_block(self.test_file_name, 1), "1" * 512)
        self.assertEqual(self.manager.get_block(self.test_file_name, 2), "2" * 512)
        self.assertEqual(self.manager.get_block(self.test_file_name, 3), "3" * 256)

    def test_multiple_files(self):
        """
        Verify we can serve blocks from multiple files
        """

        # test a block from the first files
        self.assertEqual(self.manager.get_block(self.test_file_name, 2), "2" * 512)

        # load and test the second file.
        with open(os.path.join(self.path, self.second_test_file_name), "w") as f:
            f.write("4" * 512)  # Block 4 has all 1s in it
            f.write("5" * 512)  # Block 5 has all 2s in it
            f.write("6" * 256)  # Half full block 6 has all 3s in it.

        self.manager.load_file(self.second_test_file_name)
        self.assertEqual(self.manager.get_block(self.second_test_file_name, 1), "4" * 512)
        self.assertEqual(self.manager.get_block(self.second_test_file_name, 2), "5" * 512)
        self.assertEqual(self.manager.get_block(self.second_test_file_name, 3), "6" * 256)

        # go back to checking the first file
        self.assertEqual(self.manager.get_block(self.test_file_name, 1), "1" * 512)
        self.assertEqual(self.manager.get_block(self.test_file_name, 3), "3" * 256)





if __name__ == "__main__":
    print unittest.main()