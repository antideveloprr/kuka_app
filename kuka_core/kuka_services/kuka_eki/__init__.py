import socket

import zmq

from kuka_core.forwarder import SystemForwarderTopic, DeviceForwarderTopic
from kuka_core.kuka_services import DeviceService
from kuka_core.utils import Constant
from .utils import XmlWriter, XmlReader

xml_to_write = '<Sensor>' \
               '<Pos X=${pos_x} Y=${pos_y} Z=${pos_z}>' \
               '${pos}' \
               '</Pos>' \
               '</Sensor>'

xml_to_read = '<Robot>' \
              '<ActPos X="200" Y="100" Z="10">' \
              '0' \
              '</ActPos>' \
              '</Robot>'


class Position:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return '({},{},{})' \
            .format(self.x, self.y, self.z)


def write_xml_pos(pos):
    writer = XmlWriter(xml_to_write)
    writer.set_tag('${pos}', '1', {'${pos_x}': str(pos.x),
                                   '${pos_y}': str(pos.y),
                                   '${pos_z}': str(pos.z)})
    return writer.evaluate()


def read_xml_pos(xml):
    reader = XmlReader(xml)
    x = reader.get_attribute_value('ActPos', 'X')
    y = reader.get_attribute_value('ActPos', 'Y')
    z = reader.get_attribute_value('ActPos', 'Z')
    return Position(x, y, z)


def init_pos_list():
    pos_list = [Position(x=220,
                         y=-130,
                         z=700),
                Position(x=515,
                         y=-130,
                         z=700),
                Position(x=515,
                         y=278,
                         z=700),
                Position(x=220,
                         y=278,
                         z=700)
                ]
    return pos_list


class EkiServerService(DeviceService):
    """
    EKI Ethernet KUKA communication class.
    """

    def __init__(self,
                 topic: str,
                 device_pub_addr: (str, int),
                 system_pub_addr: (str, int),
                 processing_time: float,
                 eki_addr: (str, int)):
        super().__init__(topic=topic,
                         device_pub_addr=device_pub_addr,
                         system_pub_addr=system_pub_addr,
                         processing_time=processing_time)
        self.__eki_addr = eki_addr
        self.__buffer_size = 1024
        self.__connection: socket = None

    def __setup__(self):
        super().__setup__()
        try:
            self.__pos_list = init_pos_list()
            self.eki_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.eki_socket.bind(self.__eki_addr)
            self.eki_socket.listen(10)
            self.__pos_idx = 0

            self.__connection, client_addr = self.eki_socket.accept()
            context = zmq.Context()
            self.__tool_socket = context.socket(zmq.REQ)
            self.__tool_socket.connect('tcp://127.0.0.1:8110')

        except Exception as e:
            byte_msg = [bytes(SystemForwarderTopic.ERROR, Constant.ENCODING_FORMAT),
                        bytes(str(e), Constant.ENCODING_FORMAT)]
            self._system_socket.send_multipart(byte_msg)
            # TODO: terminate process and pop from processes list(from main flask process)

    def __process__(self):
        """
        Processing KUKA TCP connection and calculating operations
        """
        super().__process__()
        try:
            received = self.__connection.recv(self.__buffer_size)
            if received:
                actual_pos = read_xml_pos(str(received, Constant.ENCODING_FORMAT))
                next_pos = self.__pos_list[self.__pos_idx]
                sent = write_xml_pos(next_pos)
                if self.__pos_idx == 3:
                    byte_msg = [bytes(DeviceForwarderTopic.TOOL, Constant.ENCODING_FORMAT),
                                bytes('open tool', Constant.ENCODING_FORMAT)]
                    self.__tool_socket.send_string('open tool')
                    msg = self.__tool_socket.recv_string()
                self.__connection.send(bytes(sent, Constant.ENCODING_FORMAT))
                pos_msg = '%s,%s' % (actual_pos, next_pos)
                print(pos_msg)
                byte_msg = [bytes(DeviceForwarderTopic.EKI, Constant.ENCODING_FORMAT),
                            bytes(pos_msg, Constant.ENCODING_FORMAT)]
                self._device_socket.send_multipart(byte_msg)
                self.__pos_idx = (self.__pos_idx + 1) % len(self.__pos_list)
        except ConnectionResetError as e:
            print(e)
            byte_msg = [bytes(SystemForwarderTopic.ERROR, Constant.ENCODING_FORMAT),
                        bytes(str(e), Constant.ENCODING_FORMAT)]
            self._system_socket.send_multipart(byte_msg)

    def run(self):
        super().run()

    def __terminate(self):
        pass
