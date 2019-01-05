import time
from threading import Thread

import zmq

from kuka_core.forwarder import ForwarderChannel
from kuka_core.utils import Constant


class Listener(Thread, ForwarderChannel):
    def __init__(self, address: (str, int), topic: str, processing_time: float):
        super().__init__()
        self.__socket = zmq.Context().socket(zmq.SUB)
        self.__processing_time = processing_time
        self._address = address
        self._topic = topic
        self.running = False

    def __setup__(self):
        self.__socket.setsockopt(zmq.SUBSCRIBE, bytes(self._topic, Constant.ENCODING_FORMAT))
        host = self._address[0]
        port = self._address[1]
        self.__socket.connect('tcp://%s:%d' % (host, port))
        addr = (host, port)
        self.__log('connected to {}'.format(addr))

    def run(self):
        self.__setup__()
        while self.running:
            # TODO: check possible usage of addr variable(socket address)
            [addr, contents] = self.__socket.recv_multipart()
            from kuka_web import events
            msg = str(contents, Constant.ENCODING_FORMAT)
            events.socketio.emit(self._topic, msg)
            self.__log(msg)
            time.sleep(self.__processing_time)
        self.__socket.close()

    def __log(self, msg: str):
        print('%s:%s -- %s' % (self.__class__.__name__, self._topic, msg))
