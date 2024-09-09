import socket

from connection import *


class UDPBasedProtocol:
    def __init__(self, *, local_addr, remote_addr):
        self.udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.remote_addr = remote_addr
        self.udp_socket.bind(local_addr)


    def sendto(self, data):
        res = self.udp_socket.sendto(data, self.remote_addr)
        return res

    def recvfrom(self, n):
        msg, addr = self.udp_socket.recvfrom(n, socket.MsgFlag.MSG_DONTWAIT)
        return msg

    def close(self):
        self.udp_socket.close()

class MyTCPProtocol(UDPBasedProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.udp_socket.setblocking(False)
        self.connection = Connection(self.recvfrom, self.sendto)

    def send(self, data: bytes):
        return self.connection.Write(data)

    def recv(self, n: int):
        return self.connection.Read(n)

    def close(self):
        self.connection.Close()
        super().close()


