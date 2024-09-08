from threading import Thread
from collections import deque as Deque
from time import sleep
from time import time

import os

from packets import *



class Connection:
    def __init__(self, readMethod, writeMethod):
        self.readMethod = readMethod
        self.writeMethod = writeMethod

        self.dataGenerator = DataGenerator()
        self.packetsGenerator = PacketGenerator()

        self.cacheQueue = Deque()

        self.canClose = False


    def Close(self, iter: int, name: str):
        readSmth = False
        numTries = 0
        while readSmth and numTries < 2000:
            readSmth = self.ReadCurrentPackets(iter, name)
            if not readSmth:
                numTries += 1
                sleep(0.001)


    def Write(self, iter: int, name: str, data: bytes):
        self.packetsGenerator.Store(data)

        while self.packetsGenerator.HasPackets():
            packet = self.packetsGenerator.Get()
            self.cacheQueue.append(packet)

            self.writeMethod(iter, "Write", name, packet.Pack())

            # Вычитываем пришедшие пакеты, чтобы
            # раньше получить уведомление о нашем fuckup
            self.ReadCurrentPackets(iter, name)

        return len(data)


    def ReadCurrentPackets(self, iter: int, name: str):
        newPacket = Packet()

        while True:
            try:
                newPacket.UnpackFrom(self.readMethod(iter, "ReadCurrent", name, MAX_PACKET_SIZE))

                # Получили управляющий пакет
                # Должны исправить ошибки
                if newPacket.tag == -1:
                    self.ProcessControlFuckup(iter, name, newPacket.data)
                elif newPacket.tag == -2:
                    self.ProcessControlRequestClose(iter, name, newPacket.data)
                elif newPacket.tag == -3:
                    self.canClose = True
                elif not self.dataGenerator.Store(newPacket):
                    self.WriteControlFuckup(iter, name)

                return True

            except:
                return False


    def Read(self, iter: int, name: str, n: int):
        newPacket = Packet()
        numTries = 0

        while not self.dataGenerator.HasData(n):
            try:
                newPacket.UnpackFrom(self.readMethod(iter, "Read", name, MAX_PACKET_SIZE))
                numTries = 0

                # Получили управляющий пакет
                # Должны исправить ошибки
                if newPacket.tag == -1:
                    self.ProcessControlFuckup(iter, name, newPacket.data)
                elif newPacket.tag == -2:
                    self.ProcessControlRequestClose(iter, name, newPacket.data)
                elif newPacket.tag == -3:
                    self.canClose = True
                elif not self.dataGenerator.Store(newPacket):
                    self.WriteControlFuckup(iter, name)
            except:
                numTries += 1
                if (numTries >= 10):
                    self.WriteControlFuckup(iter, name)
                    numTries = 0
                sleep(0.0001)

        return self.dataGenerator.Get(n)


    def WriteControlRequestClose(self, iter: int, name: str):
        doneTag = self.dataGenerator.tag - 1
        doneTagData = struct.pack('!q', doneTag)

        donePacket = Packet(-2, doneTagData)
        return self.writeMethod(iter, "WriteControlRequestClose", name, donePacket.Pack())

    def WriteControlAllowClose(self, iter: int, name: str):
        allowPacket = Packet(-3)
        return self.writeMethod(iter, "WriteControlAllowClose", name, allowPacket.Pack())

    def WriteControlFuckup(self, iter: int, name: str):
        fuckupTag = self.dataGenerator.tag
        fuckupTagData = struct.pack('!q', fuckupTag)

        controlPacket = Packet(-1, fuckupTagData)
        return self.writeMethod(iter, "WriteControlFuckup", name, controlPacket.Pack())

    def ProcessControlFuckup(self, iter: int, name: str, fuckupTagData: bytes):
        if (len(self.cacheQueue) == 0):
            return

        fuckupTag = (struct.unpack('!q', fuckupTagData))[0]

        cacheFuckupIndex = fuckupTag - self.cacheQueue[0].tag

        # print('FT = {:d}; CT = {:d}; CI = {:d}; CL = {:d}'.format(fuckupTag, self.cacheQueue[0].tag, cacheFuckupIndex, len(self.cacheQueue)))

        # Ещё ни разу не отправляли этот пакет...
        # Получатель торопится
        if (cacheFuckupIndex >= len(self.cacheQueue)):
            # print('Clearing queue')
            self.cacheQueue.clear()
            return

        # for i in range (cacheFuckupIndex):
        #     print('Popping from queue')
        #     self.cacheQueue.popleft()
        
        for i in range (cacheFuckupIndex, len(self.cacheQueue)):
            # print('Resending from queue ({:d})'.format(self.cacheQueue[i].tag))
            self.writeMethod(iter, "ProcessControl", name, self.cacheQueue[i].Pack())

        
    def ProcessControlRequestClose(self, iter: int, name: str, doneTagData: bytes):
        doneTag = (struct.unpack('!q', doneTagData))[0]

        if (doneTag <= self.dataGenerator.tag):
            self.WriteControlAllowClose(iter, name)
