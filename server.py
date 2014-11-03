import SocketServer
import struct
import argparse

OP_RRQ = 1
OP_WRQ = 2
OP_DATA = 3
OP_ACK = 4
OP_ERROR = 5


class FileRequestManager(object):

    def __init__(self, file):
        self.contents = file.getvalue()

    def get_block(self, block_number):
        block_begin_index = (block_number - 1) * 512
        block_end_index = block_number * 512
        return self.contents[block_begin_index:block_end_index]


class UDPHandler(SocketServer.DatagramRequestHandler):

    def get_opcode(self, packed_opcode):
        opcode = struct.unpack("!H", packed_opcode)
        return opcode[0]

    def get_filename_and_mode(self, data):
        filename, mode, _ = data.split("\0")
        return (filename, mode)

    def send_data_packet(self, block_number, msg):
        fmt = "!HH{}s".format(len(msg))
        data_packet = struct.pack(fmt, OP_DATA, block_number, msg)
        self.wfile.write(data_packet)

    def handle(self):
        data, socket = self.request
        opcode = self.get_opcode(data[0:2])

        if opcode == OP_RRQ:
            filename, mode = self.get_filename_and_mode(data[2:])
            self.send_data_packet(1, "1" * 512)

        elif opcode == OP_ACK:
            print("received an ack")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A simple netascii-only tftp server')
    parser.add_argument('-p', '--port', type=int, default=69, help='TFTP server port. Defaults to 69.')
    parser.add_argument('path', type=str, help="Directory of files to serve")
    args = parser.parse_args()

    server = SocketServer.UDPServer(("localhost", args.port), UDPHandler)
    server.serve_forever()
