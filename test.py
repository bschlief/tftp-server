#!/usr/bin/env python
import unittest
import struct
import mock
from server import UDPHandler, FileRequestManager, FileManagerUDPServer
from server import OP_RRQ, OP_DATA, OP_ERROR
import os

class TestUdpHandler(unittest.TestCase):

    def setUp(self):
        self.path = os.path.dirname(__file__)
        self.client_address = ("127.0.0.1", 65534)
        self.test_file_name = "test_file_to_serve.txt"
        self.does_not_exist_filename = "not_actually_there.txt"

        with open(os.path.join(self.path, self.test_file_name), "w") as f:
            f.write("1" * 512)  # Block 1 has all 1s in it
            f.write("2" * 512)  # Block 2 has all 2s in it
            f.write("3" * 256)  # Half full block 3 has all 3s in it.
        self.manager = FileRequestManager(self.path)
        self.manager.load_file(self.test_file_name)

        # Mock out the socket used to answer the request so that we can see what it was sent.
        self.mock_answer_sock = mock.Mock()
        UDPHandler.get_new_socket = mock.Mock(return_value=self.mock_answer_sock)

        self.mock_listen_sock = mock.Mock()

        self.mock_server = mock.Mock()
        self.mock_server.file_manager = FileRequestManager(os.path.dirname(__file__))

    def tearDown(self):
        os.remove(os.path.join(self.path, self.test_file_name))

    def test_rrq(self):
        """
        Test a read request
        """
        self.mock_server.file_manager.get_block = mock.Mock(return_value = "1" * 512)

        fmt = "!H{}sB{}sB".format(len(self.test_file_name), len("netascii"))
        rrq = struct.pack(fmt, OP_RRQ, self.test_file_name, 0, "netascii", 0)
        request = (rrq, self.mock_listen_sock)

        handler = UDPHandler(request, self.client_address, self.mock_server)

        expected_block_number = 1
        expected_data_response = struct.pack("!HH512s", OP_DATA, expected_block_number, "1" * 512)
        self.mock_answer_sock.sendto.assert_called_with(expected_data_response, self.client_address)


    def test_rrq_for_nonexistant_file(self):
        fmt = "!H{}sB{}sB".format(len(self.does_not_exist_filename), len("netascii"))
        rrq = struct.pack(fmt, OP_RRQ, self.does_not_exist_filename, 0, "netascii", 0)

        request = (rrq, self.mock_listen_sock)
        handler = UDPHandler(request, self.client_address, self.mock_server)

        error_message = "No such file or directory"
        fmt = "!H{}s".format(len(error_message))
        expected_error_response = struct.pack(fmt, OP_ERROR, error_message)
        self.mock_listen_sock.sendto.assert_called_with(expected_error_response, self.client_address)


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