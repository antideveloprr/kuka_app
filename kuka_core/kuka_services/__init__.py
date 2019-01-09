import time
from multiprocessing import Process

import zmq

from kuka_core.forwarder import ForwarderChannel


class DeviceService(Process, ForwarderChannel):
    """

    """

    def __init__(self,
                 topic: str,
                 device_pub_addr: (str, int),
                 system_pub_addr: (str, int),
                 processing_time: float):
        ForwarderChannel.__init__(self, topic=topic)
        Process.__init__(self)
        self._processing_time = processing_time
        self._device_pub_addr = device_pub_addr
        self._system_pub_addr = system_pub_addr
        self.running = False

    def __setup__(self):
        """

        """
        context = zmq.Context()
        self._device_socket = context.socket(zmq.PUB)
        device_host = self._device_pub_addr[0]
        device_port = self._device_pub_addr[1]
        self._device_socket.connect('tcp://%s:%d' % (device_host, device_port))

        self._system_socket = context.socket(zmq.PUB)
        system_host = self._system_pub_addr[0]
        system_port = self._system_pub_addr[1]
        self._system_socket.connect('tcp://%s:%d' % (system_host, system_port))

    def __process__(self):
        """

        """
        self.__log('service is in a processing state')
        pass

    def __terminate(self):
        """

        """
        self.__log('service is in a terminating state')
        pass

    def run(self):
        self.__setup__()
        while self.running:
            self.__process__()
            time.sleep(self._processing_time)
        self.__terminate()

    def __log(self, msg: str):
        print('%s:%s -- %s' % (self.__class__.
                               __bases__[0].__name__,
                               self._topic, msg))
