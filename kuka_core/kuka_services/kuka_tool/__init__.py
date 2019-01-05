from serial import Serial, SerialException

from kuka_core.forwarder import SystemForwarderTopic, DeviceForwarderTopic
from kuka_core.kuka_services import DeviceService
from kuka_core.utils import Constant


class ToolService(DeviceService):
    """

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
        except SerialException as e:
            byte_msg = [bytes(SystemForwarderTopic.ERROR, Constant.ENCODING_FORMAT),
                        bytes(str(e), Constant.ENCODING_FORMAT)]
            self._system_socket.send_multipart(byte_msg)
            self.running = False
            print(self.__class__.__name__, ' service work has been stopped.')
            # TODO: terminate process and pop from processes list(from main flask process)

    def __process__(self):
        """

        """
        super().__process__()
        msg = self.__ser.read_all()
        byte_msg = [bytes(DeviceForwarderTopic.TOOL, Constant.ENCODING_FORMAT),
                    msg]
        self._device_socket.send_multipart(byte_msg)

    def run(self):
        super().run()
