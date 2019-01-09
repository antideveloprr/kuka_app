import zmq
from serial import Serial

from kuka_core.forwarder import SystemForwarderTopic, DeviceForwarderTopic
from kuka_core.kuka_services import DeviceService
from kuka_core.utils import Constant


class ToolService(DeviceService):
    """
    Tool serial communication class.
    """

    def __init__(self,
                 topic: str,
                 device_pub_addr: (str, int),
                 system_pub_addr: (str, int),
                 processing_time: float,
                 serial_port_addr: str,
                 serial_baud_rate: int):
        super().__init__(topic=topic,
                         device_pub_addr=device_pub_addr,
                         system_pub_addr=system_pub_addr,
                         processing_time=processing_time)
        self.__serial_port_addr = serial_port_addr
        self.__serial_baud_rate = serial_baud_rate
        self.__ser: Serial = None

    def __setup__(self):
        super().__setup__()
        try:
            self.__ser = Serial(self.__serial_port_addr, self.__serial_baud_rate)

            context = zmq.Context()
            self.__eki_socket = context.socket(zmq.REP)
            self.__eki_socket.bind('tcp://127.0.0.1:8110')
        except Exception as e:
            byte_msg = [bytes(SystemForwarderTopic.ERROR, Constant.ENCODING_FORMAT),
                        bytes(str(e), Constant.ENCODING_FORMAT)]
            self._system_socket.send_multipart(byte_msg)
            self.running = False
            # TODO: terminate process and pop from processes list(from main flask process)

    def __process__(self):
        """
        Processing serial connection with Arduino Board via USB.
        """
        super().__process__()
        msg = self.__eki_socket.recv_string()
        if msg == 'open tool':
            self.__ser.write(bytes('a', 'utf-8'))
        while self.__ser.read() != bytes('d', 'utf-8'):
            print('waiting for tool work end')
        # byte_msg = [bytes(DeviceForwarderTopic.FORWARDER_INTERNAL, Constant.ENCODING_FORMAT),
        #             bytes('close tool', Constant.ENCODING_FORMAT)]
        self.__eki_socket.send_string('close tool')
        # byte_msg = [bytes(DeviceForwarderTopic.TOOL, Constant.ENCODING_FORMAT),
        #             msg]
        # self._device_socket.send_multipart(byte_msg)


def run(self):
    super().run()
