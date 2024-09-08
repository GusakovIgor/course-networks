import struct
import threading
from collections import deque as Deque

MAX_PACKET_LEN = 64512
MAX_PACKET_SIZE = 64520

class Packet:
    def __init__(self, tag: int = 0, data: bytes = bytes()):
        self.tag = tag
        self.data = data

    def UnpackFrom(self, raw_packet: bytes):
        self.tag = (struct.unpack('!q', raw_packet[:8]))[0]
        self.data = raw_packet[8:]
    
    def Pack(self):
        return struct.pack('!q', self.tag) + self.data


class PacketGenerator:
    def __init__(self):
        self.tag = 0
        self.packets = Deque()

    def HasPackets(self):
        return len(self.packets) > 0

    def Store(self, data: bytes):
        # Складываем "целые" пакеты (по MAX_PACKET_LEN байт)
        while len(data) >= MAX_PACKET_LEN:
            self.packets.append(Packet(self.tag, data[:MAX_PACKET_LEN]))
            data = data[MAX_PACKET_LEN:]
            self.tag += 1
            
        # Складываем "остаток"
        if len(data) > 0:
            self.packets.append(Packet(self.tag, data))
            self.tag += 1

    def Get(self):
        return self.packets.popleft()


class DataGenerator:
    def __init__(self):
        self.tag = 0
        self.data = bytes()

    def HasData(self, n: int):
        return len(self.data) >= n

    def Store(self, packet: Packet):
        # Пропускаем уже считанные пакеты
        # но говорим, что всё окей.
        if packet.tag < self.tag:
            # print('Filter duplicate packet {:d}'.format(packet.tag))
            return True

        # Пропускаем будущие пакеты но говорим, что произошла ошибка,
        # потому что мы пропустили пакет.
        if packet.tag > self.tag:
            # print('Report future packet {:d} ({:d})'.format(packet.tag, self.tag))
            return False
        
        self.data += packet.data
        self.tag += 1
        return True

    def Get(self, n: int):
        outData = self.data[:n]
        self.data = self.data[n:]
        return outData
