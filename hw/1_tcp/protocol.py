import socket

from packets import *
from entities import *


class UDPBasedProtocol:
    def __init__(self, *, local_addr, remote_addr):
        self.udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.remote_addr = remote_addr
        self.udp_socket.bind(local_addr)


    def sendto(self, iter: int, calledFrom, name: str, data):
        print('[{:s}][{:d}][{:s}] Sending data ({:d})'.format(name, iter, calledFrom, len(data)))
        res = self.udp_socket.sendto(data, self.remote_addr)
        print('[{:s}][{:d}][{:s}] Sent data ({:d})'.format(name, iter, calledFrom, res))
        return res

    def recvfrom(self, iter: int, calledFrom, name: str, n):
        msg, addr = self.udp_socket.recvfrom(n, socket.MsgFlag.MSG_DONTWAIT)
        print('[{:s}][{:d}][{:s}] Recieving data ({:d})'.format(name, iter, calledFrom, n))
        # msg, addr = self.udp_socket.recvfrom(n)
        print('[{:s}][{:d}][{:s}] Recieved data ({:d})'.format(name, iter, calledFrom, len(msg)))
        return msg

    def close(self):
        self.udp_socket.close()

class MyTCPProtocol(UDPBasedProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.udp_socket.settimeout(0.0001)
        self.connection = Connection(self.recvfrom, self.sendto)

    def send(self, iter: int, name: str, data: bytes):
        return self.connection.Write(iter, name, data)
        # return self.sendto(data)

    def recv(self, iter: int, name: str, n: int):
        return self.connection.Read(iter, name, n)
        # return self.recvfrom(n)

    def close(self, iter: int, name: str):
        super().close()


