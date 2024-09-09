from threading import Thread
from collections import deque as Deque
from time import sleep

from packets import *


class Connection:
    def __init__(self, readMethod, writeMethod):
        self.readMethod = readMethod
        self.writeMethod = writeMethod

        self.dataGenerator = DataGenerator()
        self.packetsGenerator = PacketGenerator()

        self.cacheQueue = Deque()

        self.readThreadStop = False
        self.readThread = Thread(target = self.ReadAsync)
        self.readThread.start()


    def Close(self):
        self.readThreadStop = True
        self.readThread.join()


    def ReadAsync(self):
        newPacket = Packet()

        while not self.readThreadStop:
            try:
                newPacket.UnpackFrom(self.readMethod(MAX_PACKET_SIZE))

                if newPacket.tag == -1:
                    self.ProcessControl(newPacket.data)
                elif not self.dataGenerator.Store(newPacket):
                    self.WriteControl()
            except:
                # Не занимаем всё процессорное время.
                sleep(0.00001)
                continue



    def Write(self, data: bytes):
        self.packetsGenerator.Store(data)

        while self.packetsGenerator.HasPackets():
            packet = self.packetsGenerator.Get()
            self.cacheQueue.append(packet)

            self.writeMethod(packet.Pack())

        return len(data)


    def Read(self, n: int):
        numTries = 0

        while not self.dataGenerator.HasData(n):
            numTries += 1
            if (numTries >= 50):
                self.WriteControl()
                numTries = 0
            sleep(0.0001)

        return self.dataGenerator.Get(n)


    # Отправляем сообщение о недошедших пакетах.
    def WriteControl(self):
        errorTag = self.dataGenerator.tag
        errorTagData = struct.pack('!q', errorTag)

        controlPacket = Packet(-1, errorTagData)
        return self.writeMethod(controlPacket.Pack())


    # Обрабатываем сообщение о недошедших пакетах.
    def ProcessControl(self, errorTagData: bytes):
        if (len(self.cacheQueue) == 0):
            return

        errorTag = (struct.unpack('!q', errorTagData))[0]

        cacheErrorIndex = errorTag - self.cacheQueue[0].tag

        # Ещё ни разу не отправляли этот пакет...
        # Получатель торопится.
        if (cacheErrorIndex >= len(self.cacheQueue)):
            self.cacheQueue.clear()
            return

        # Если пользователь не получил errorTag,
        # то все пакеты до этого он уже получил.
        # Можем убрать их из кэша.
        for i in range (cacheErrorIndex):
            self.cacheQueue.popleft()
        
        # А вот все остальные отправим заново.
        for i in range (len(self.cacheQueue)):
            self.writeMethod(self.cacheQueue[i].Pack())
