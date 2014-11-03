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

class SocketManager(object):
    def __init__(self):
        self.sockets = {}

    def initialize_socket(self, client_address):
        pass

        # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sockets[client_address] = sock

    def send_data(self, data, client_address):
        # print "Sending data to {}".format(client_address)
        # client_socket = self.sockets[client_address]
        # client_socket.sendto(data, client_address)

        # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # s.sendto(data, client_address)
        pass

class UDPHandler(SocketServer.DatagramRequestHandler):

    def get_opcode(self, packed_opcode):
        opcode = struct.unpack("!H", packed_opcode)
        return opcode[0]

    def get_filename_and_mode(self, data):
        filename, mode, _ = data[2:].split("\0")
        return (filename, mode)

    def get_block_number(self, data):
        _, block_number = struct.unpack("!HH", data)
        return block_number

    def pack_data(self, block_number, msg):
        fmt = "!HH{}s".format(len(msg))
        return struct.pack(fmt, OP_DATA, block_number, msg)

    def handle(self):
        data, request_socket = self.request

        print "Received data from {}".format(self.client_address)

        opcode = self.get_opcode(data[0:2])

        print "Opcode received was {}".format(opcode)

        if opcode == OP_RRQ:
            filename, mode = self.get_filename_and_mode(data)
            self.server.file_manager.load_file(filename)
            block_number = 1
            raw_data = self.server.file_manager.get_block(filename, block_number)
            packed_data = self.pack_data(block_number, raw_data)
            if packed_data == None:
                raise Exception("Unable to pack data")
            self.wfile.write(packed_data)

        elif opcode == OP_ACK:
            block_number = self.get_block_number(data)
            raw_data = self.server.file_manager.get_block("longtext.txt", block_number + 1)
            packed_data = self.pack_data(block_number + 1, raw_data)
            if packed_data == None:
                raise Exception("Unable to pack data")
            self.wfile.write(packed_data)

class FileManagerUDPServer(SocketServer.UDPServer):

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, path=os.path.dirname(__file__)):
        self.file_manager = FileRequestManager(path)
        # self.socket_manager = SocketManager()
        SocketServer.UDPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A simple netascii-only tftp server')
    parser.add_argument('-p', '--port', type=int, default=69, help='TFTP server port. Defaults to 69.')
    parser.add_argument('path', type=str, help="Directory of files to serve")
    args = parser.parse_args()

    server = FileManagerUDPServer(("localhost", args.port), UDPHandler, path=args.path)
    server.serve_forever()
