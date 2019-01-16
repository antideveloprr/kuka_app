import zmq
from serial import Serial, SerialException

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
        except SerialException as e:
            byte_msg = [bytes(SystemForwarderTopic.ERROR, Constant.ENCODING_FORMAT),
                        bytes(str(e), Constant.ENCODING_FORMAT)]
            self._system_socket.send_multipart(byte_msg)
            self.running = False
            print(byte_msg)
            # TODO: terminate process and pop from processes list(from main flask process)

    def __process__(self):
        """
        Processing serial connection with Arduino Board via USB.
        """
        super().__process__()
        msg = self.__eki_socket.recv_string()
        if msg == 'open tool right':
            byte_msg = [bytes(DeviceForwarderTopic.TOOL, Constant.ENCODING_FORMAT),
                        bytes('starting screwing left process', Constant.ENCODING_FORMAT)]
            self._device_socket.send_multipart(byte_msg)
            self.__ser.write(bytes('r', 'utf-8'))
        if msg == 'open tool left':
            byte_msg = [bytes(DeviceForwarderTopic.TOOL, Constant.ENCODING_FORMAT),
                        bytes('starting screwing right process', Constant.ENCODING_FORMAT)]
            self._device_socket.send_multipart(byte_msg)
            self.__ser.write(bytes('l', 'utf-8'))
        while self.__ser.read() != bytes('d', 'utf-8'):
            print('screwing in progress')
        self.__eki_socket.send_string('close tool')
        byte_msg = [bytes(DeviceForwarderTopic.TOOL, Constant.ENCODING_FORMAT),
                    bytes('ending screwign process ', Constant.ENCODING_FORMAT)]
        self._device_socket.send_multipart(byte_msg)

    def run(self):
        super().run()
