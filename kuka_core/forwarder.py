from multiprocessing import Process
from init_utils import logger
import zmq


class DeviceForwarderTopic:
    """
    Enum class for storing device forwarder messaging topics.
    """
    EKI = 'eki'
    TOOL = 'tool'
    CAMERA = 'camera'
    FORWARDER = 'device_forwarder'


class SystemForwarderTopic:
    """
    Enum class for storing system forwarder messaging topics.
    """
    LOG = 'log'
    ERROR = 'error'
    FORWARDER = 'system_forwarder'


class ForwarderChannel:
    """
    Integrates publisher with subscriber in topic driven messaging.
    with usage of forwarder architecture pattern.
    """

    def __init__(self, topic: str):
        self._topic = topic


class Forwarder(Process, ForwarderChannel):
    """
    Forwarder main class to proxy messages of PUB-SUB architecture.
    """

    def __init__(self, topic, sub_addr: (str, int), pub_addr: (str, int)):
        super().__init__()
        self.running = False
        self.__sub_addr = sub_addr
        self.__pub_addr = pub_addr
        self._topic = topic

    def run(self):
        try:
            context = zmq.Context()
            sub_layer = context.socket(zmq.SUB)
            pub_host = self.__pub_addr[0]
            pub_port = self.__pub_addr[1]
            sub_layer.bind('tcp://%s:%d' % (pub_host, pub_port))
            sub_layer.setsockopt(zmq.SUBSCRIBE, b'')
            self.__log('setting up subscribing layer to services on {}'.format(self.__pub_addr))
            logger.info('setting up subscribing layer to services on {}'.format(self.__pub_addr))

            pub_layer = context.socket(zmq.PUB)

            sub_host = self.__sub_addr[0]
            sub_port = self.__sub_addr[1]
            pub_layer.bind('tcp://%s:%d' % (sub_host, sub_port))
            self.__log('setting up publishing layer to listeners on {}'.format(self.__sub_addr))
            logger.info('setting up publishing layer to listeners on {}'.format(self.__sub_addr))

            zmq.device(zmq.FORWARDER, sub_layer, pub_layer)
        except Exception as e:
            # TODO: send error to interface
            self.__log('error')
            print(e)

    def __log(self, msg: str):
        print('%s:%s -- %s' % (self.__class__.__name__, self._topic, msg))
