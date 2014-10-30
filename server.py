import SocketServer
import struct
import logging

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logger = logging.getLogger("tftp-client")
logger.addHandler(console)

OP_RRQ = 1
OP_WRQ = 2
OP_ACK = 3
OP_DATA = 4
OP_ERROR = 5

class UDPHandler(SocketServer.DatagramRequestHandler):

    def get_opcode(self, packed_opcode):
        opcode = struct.unpack("!H", packed_opcode)
        return opcode[0]

    def get_filename_and_mode(self, data):
        filename, mode, _ = data.split("\0")
        return (filename, mode)

    def handle(self):
        data, socket = self.request
        opcode = self.get_opcode(data[0:2])

        if opcode == OP_RRQ:
            filename, mode = self.get_filename_and_mode(data[2:])

        elif opcode == OP_ACK:
            print("received an ack")

        socket.sendto(data.upper(), self.client_address)


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    server = SocketServer.UDPServer((HOST, PORT), UDPHandler)
    server.serve_forever()
