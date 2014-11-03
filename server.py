#!/usr/bin/env python
import SocketServer
import socket
import struct
import argparse
import os

OP_RRQ = 1
OP_WRQ = 2
OP_DATA = 3
OP_ACK = 4
OP_ERROR = 5

DATA_HEADER_SIZE = 4
DATA_SIZE = 512

class FileRequestManager(object):

    def __init__(self, served_files_path):
        self.served_files_path = served_files_path
        self.files = {}

    def load_file(self, filename):
        if filename not in self.files:
            with open(os.path.join(self.served_files_path, filename), "r") as f:
                self.files[filename] = f.read()

    def get_block(self, filename, block_number):
        block_begin_index = (block_number - 1) * 512
        block_end_index = block_number * 512
        return self.files[filename][block_begin_index:block_end_index]


class UDPHandler(SocketServer.BaseRequestHandler):

    def get_opcode(self, packed_opcode):
        """
        Convenience method to get the op code out of a data packet.
        """
        opcode = struct.unpack("!H", packed_opcode)
        return opcode[0]

    def get_filename_and_mode(self, data):
        filename, mode, _ = data[2:].split("\0")
        return (filename, mode)

    def get_block_number(self, data):
        """
        Convenience method to get a block number out of an ack packet
        """
        _, block_number = struct.unpack("!HH", data)
        return block_number

    def pack_data(self, block_number, msg):
        """
        Pack the data up in a tfpt DATA packet
        """
        fmt = "!HH{}s".format(len(msg))
        return struct.pack(fmt, OP_DATA, block_number, msg)

    def handle(self):
        """
        Listen for read requests. Spin off a separate socket to handle
        the actual transfer.
        """
        data, request_socket = self.request

        opcode = self.get_opcode(data[0:2])

        if opcode == OP_RRQ:
            self.process_read_request(data)

    def process_read_request(self, data):
        """
        Take a read request and handle processing of that file on a separate port
        """
        filename, mode = self.get_filename_and_mode(data)
        self.server.file_manager.load_file(filename)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        block_number = 0
        data_length = DATA_HEADER_SIZE + DATA_SIZE

        while data_length == DATA_HEADER_SIZE + DATA_SIZE:
            block_number += 1
            block_data = self.server.file_manager.get_block(filename, block_number)
            packed_data = self.pack_data(block_number, block_data)
            data_length = sock.sendto(packed_data, self.client_address)

            # If the data packet was the maximum size, listen for the ack to send
            # the next packet. If it was less than the maximum size, then the
            # transfer is complete.
            if data_length == DATA_HEADER_SIZE + DATA_SIZE:
                raw_data, _ = sock.recvfrom(DATA_HEADER_SIZE + DATA_SIZE)


class FileManagerUDPServer(SocketServer.UDPServer):

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, path=os.path.dirname(__file__)):
        self.file_manager = FileRequestManager(path)
        SocketServer.UDPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A simple netascii-only tftp server')
    parser.add_argument('-p', '--port', type=int, default=69, help='TFTP server port. Defaults to 69.')
    parser.add_argument('path', type=str, help="Directory of files to serve")
    args = parser.parse_args()

    server = FileManagerUDPServer(("localhost", args.port), UDPHandler, path=args.path)
    server.serve_forever()
