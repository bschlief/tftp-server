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

    def get_opcode(self, data):
        opcode = struct.unpack("!H", data[0:2])
        return opcode[0]

    def handle(self):
        data, socket = self.request
        opcode = self.get_opcode(data)

        if opcode == OP_RRQ:
            print("Received a read request")
        elif opcode == OP_ACK:
            print("received an ack")

        socket.sendto(data.upper(), self.client_address)


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    server = SocketServer.UDPServer((HOST, PORT), UDPHandler)
    server.serve_forever()
