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

ERROR_HEADER_SIZE = 2
DATA_HEADER_SIZE = 4
DATA_SIZE = 512

TFTP_ERROR_FILE_NOT_FOUND = 1

class FileRequestManager(object):

    def __init__(self, served_files_path):
        """
        Manages and caches files, provides file blocks on request.
        """
        self.served_files_path = served_files_path
        self.files = {}

    def load_file(self, filename):
        """
        Loads a file into memory if it hasn't been loaded yet.
        """
        if filename not in self.files:
            with open(os.path.join(self.served_files_path, filename), "r") as f:
                self.files[filename] = f.read()

    def get_block(self, filename, block_number):
        """
        Get the block_number from the specified file
        """
        block_begin_index = (block_number - 1) * DATA_SIZE
        block_end_index = block_number * DATA_SIZE
        return self.files[filename][block_begin_index:block_end_index]


class UDPHandler(SocketServer.BaseRequestHandler):

    def get_opcode(self, packed_opcode):
        """
        Convenience method to get the op code out of a data packet.
        """
        opcode = struct.unpack("!H", packed_opcode)
        return opcode[0]

    def get_filename_and_mode(self, data):
        """
        Convenience method to get the filename and mode out of a data packet
        """
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
        Pack the data up in a tftp DATA packet
        """
        fmt = "!HH{}s".format(len(msg))
        return struct.pack(fmt, OP_DATA, block_number, msg)

    def pack_error(self, msg):
        """
        Pack the error message up in a tftp ERROR packet. Erroneously
        reports all errors as file not found.  It is correct, but only occasionally.

        TODO: Fully support all error messages below
        0         Not defined, see error message (if any).
        1         File not found.
        2         Access violation.
        3         Disk full or allocation exceeded.
        4         Illegal TFTP operation.
        5         Unknown transfer ID.
        6         File already exists.
        7         No such user.
        """
        fmt = "!HH{}sB".format(len(msg))
        return struct.pack(fmt, OP_ERROR, TFTP_ERROR_FILE_NOT_FOUND, msg, 0)

    def handle(self):
        """
        Listen for read requests. Spin off a separate socket to handle
        the actual transfer.
        """
        data, request_socket = self.request

        opcode = self.get_opcode(data[0:2])

        if opcode == OP_RRQ:
            try:
                self.process_read_request(data)
            except TypeError, e:
                data = self.pack_error(str(e))
                request_socket.sendto(data, self.client_address)
            except Exception, e:
                data = self.pack_error(e.strerror)
                request_socket.sendto(data, self.client_address)
        if opcode == OP_ERROR:
            self.process_error(data)

    def get_new_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def process_read_request(self, data):
        """
        Take a read request and handle processing of that file on a separate port
        """
        sock = self.get_new_socket()

        filename, mode = self.get_filename_and_mode(data)
        self.server.file_manager.load_file(filename)

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

    def process_error(self, data):
        fmt = "!H{}s".format(len(data) - ERROR_HEADER_SIZE)
        opcode, error = struct.unpack(fmt, data)
        print error

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
