import socket
import time
from multiprocessing import Process

from kuka_core.utils import Constant

xml_to_read = '<Robot>' \
              '<ActPos X="200" Y="100" Z="10">' \
              '0' \
              '</ActPos>' \
              '</Robot>'


class TcpClientProcess(Process):
    def __init__(self, tcp_addr: (str, int)):
        super().__init__()
        self.running = False
        self.__tcp_addr = tcp_addr

    def run(self):
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect(self.__tcp_addr)
        while self.running:
            tcp_sock.sendall(bytes(xml_to_read, 'utf-8'))
            data = tcp_sock.recv(1024)
            print('client data received: ', str(data, Constant.ENCODING_FORMAT))

            time.sleep(0.1)
        tcp_sock.close()
