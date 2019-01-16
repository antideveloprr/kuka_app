import socket
import time

import zmq

from kuka_core.forwarder import SystemForwarderTopic, DeviceForwarderTopic
from kuka_core.kuka_services import DeviceService
from kuka_core.utils import Constant
from .utils import XmlWriter, XmlReader

xml_to_write = '<Sensor>' \
               '<Pos X=${pos_x} Y=${pos_y} Z=${pos_z}>' \
               '${pos}' \
               '</Pos>' \
               '<predkosc>${predkosc}</predkosc>' \
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
        return 'Position:\nx={}\ny={}\nz={}\n' \
            .format(self.x, self.y, self.z)


def write_xml_pos(pos: Position, predkosc: int):
    writer = XmlWriter(xml_to_write)
    writer.set_tag('${pos}', '1', {'${pos_x}': str(pos.x),
                                   '${pos_y}': str(pos.y),
                                   '${pos_z}': str(pos.z)})
    writer.set_tag('${predkosc}', str(predkosc), {})
    return writer.evaluate()


def read_xml_pos(xml):
    reader = XmlReader(xml)
    x = reader.get_attribute_value('ActPos', 'X')
    y = reader.get_attribute_value('ActPos', 'Y')
    z = reader.get_attribute_value('ActPos', 'Z')
    return Position(x, y, z)


# def init_pos_list():
#     pos_list = [
#         Position(x=552.27,
#                  y=-25,
#                  z=650)
#     ]
#     return pos_list


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
        self.__pos: Position
        self.__pos_list: []
        self.__pos_idx: int = 0
        self.__photo_position: Position

    def __setup__(self):
        super().__setup__()
        try:
            # self.__pos_list = init_pos_list()
            self.eki_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.eki_socket.bind(self.__eki_addr)
            self.eki_socket.listen(1)
            self.__pos_idx = 0

            self.__connection, client_addr = self.eki_socket.accept()
            context = zmq.Context()
            self.__tool_socket = context.socket(zmq.REQ)
            self.__tool_socket.connect('tcp://127.0.0.1:8110')
            self.__camera_socket = context.socket(zmq.REQ)
            self.__camera_socket.connect('tcp://127.0.0.1:8310')
            self.__status = 'START'

        except Exception as e:
            byte_msg = [bytes(SystemForwarderTopic.ERROR, Constant.ENCODING_FORMAT),
                        bytes(str(e), Constant.ENCODING_FORMAT)]
            self._system_socket.send_multipart(byte_msg)
            print(e)
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
                if self.__status == 'START':
                    self.__camera_socket.send_string('check screws')
                    self.__pos_list = self.__camera_socket.recv_pyobj()
                    self.__pos = self.__pos_list[self.__pos_idx]
                    self.__photo_position = actual_pos
                    for i in self.__pos_list:
                        pos = Position(int(self.__photo_position.x) + int(i.x),
                                       int(self.__photo_position.y) + int(i.y), 0)
                        print('posssss : {}\n'.format(pos))
                    sent = write_xml_pos(actual_pos, 0)
                    self.__status = 'INIT'
                    self.__connection.send(bytes(sent, Constant.ENCODING_FORMAT))
                elif self.__status == 'INIT':
                    self.__pos = self.__pos_list[self.__pos_idx]
                    self.__pos = Position(int(self.__photo_position.x) + self.__pos.x,
                                          int(self.__photo_position.y) + self.__pos.y, 450)
                    print(self.__pos)
                    sent = write_xml_pos(self.__pos, 0)
                    self.__connection.send(bytes(sent, Constant.ENCODING_FORMAT))
                    self.__status = 'SCREW UP'
                elif self.__status == 'SCREW UP':
                    self.__pos = Position(self.__pos.x, self.__pos.y, 400)
                    sent = write_xml_pos(self.__pos, 1)
                    self.__connection.send(bytes(sent, Constant.ENCODING_FORMAT))
                    self.__status = 'UNSCREW'
                elif self.__status == 'UNSCREW':
                    self.__pos = Position(self.__pos.x, self.__pos.y, 450)
                    sent = write_xml_pos(self.__pos, 1)
                    self.__tool_socket.send_string('open tool left')
                    time.sleep(1)
                    self.__connection.send(bytes(sent, Constant.ENCODING_FORMAT))
                    msg = self.__tool_socket.recv_string()
                    if self.__pos_idx == 4:
                        self.__status = 'END'
                    else:
                        self.__status = 'INIT'
                        self.__pos_idx += 1
                elif self.__status == 'END':
                    sent = write_xml_pos(self.__pos, 2)
                    self.__connection.send(bytes(sent, Constant.ENCODING_FORMAT))
                pos_msg = '%s,%s' % (actual_pos, self.__pos)
                print(pos_msg)
                byte_msg = [bytes(DeviceForwarderTopic.EKI, Constant.ENCODING_FORMAT),
                            bytes(pos_msg, Constant.ENCODING_FORMAT)]
                self._device_socket.send_multipart(byte_msg)
                # (self.__pos_idx + 1) % len(self.__pos_list)
        except ConnectionResetError as e:
            print(e)
            byte_msg = [bytes(SystemForwarderTopic.ERROR, Constant.ENCODING_FORMAT),
                        bytes(str(e), Constant.ENCODING_FORMAT)]
            self._system_socket.send_multipart(byte_msg)

    def run(self):
        super().run()

    def __terminate(self):
        pass
