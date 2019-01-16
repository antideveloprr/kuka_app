import base64

import cv2
# from kuka_core.forwarder import DeviceForwarderTopic, SystemForwarderTopic
# from kuka_core.kuka_services import DeviceService
# from kuka_core.utils import Constant
import numpy as np
import zmq

from kuka_core.forwarder import SystemForwarderTopic, DeviceForwarderTopic
from kuka_core.kuka_services import DeviceService
from kuka_core.kuka_services.kuka_eki import Position
from kuka_core.utils import Constant
from .pseyepy_master.pseyepy import Camera


class CameraService(DeviceService):
    """
    Pseye camera class.s
    """

    def __init__(self,
                 topic: str,
                 device_pub_addr: (str, int),
                 system_pub_addr: (str, int),
                 processing_time: float):
        super().__init__(topic=topic,
                         device_pub_addr=device_pub_addr,
                         system_pub_addr=system_pub_addr,
                         processing_time=processing_time)
        self.__cams: Camera = None
        self.__img_width = 640
        self.__img_height = 480
        self.__cam_one: Camera = None

    def __setup__(self):
        super().__setup__()
        """
        Video output devices configuration.
        """
        try:
            # self.__cam_two = Camera(1, resolution=Camera.RES_LARGE, colour=False, gain=5, fps=20, exposure=100)
            context = zmq.Context()
            self.__eki_socket = context.socket(zmq.REP)
            self.__eki_socket.bind('tcp://127.0.0.1:8310')

            self.__cam_one = Camera(0, resolution=Camera.RES_LARGE, colour=False, gain=1, fps=24, exposure=30, vflip = False, hflip = False)
        except Exception as e:
            byte_msg = [bytes(SystemForwarderTopic.ERROR, Constant.ENCODING_FORMAT),
                        bytes(str(e), Constant.ENCODING_FORMAT)]
            self._system_socket.send_multipart(byte_msg)
            self.running = False
            # TODO: terminate process and pop from processes list(from main flask process)

    def hough_circle(self, image):

        cimg1 = cv2.medianBlur(image, 5)

        # simg1 = cv2.cvtColor(img1, cv2.COLOR_BGRA2BGR)

        edges1 = cv2.Canny(cimg1, 200, 255)
        edges2 = cv2.Canny(cimg1, 200, 250)

        # test1 i test3 dzialaja przy param1=250 i param2=80
        # test2 dziala przy param1=200 i param2=70

        # circles1 = cv2.HoughCircles(edges1, cv2.HOUGH_GRADIENT, 1, 5, param1=50, param2=30, minRadius=20,
        #                          maxRadius=150)
        colimg1 = cv2.cvtColor(cimg1, cv2.COLOR_GRAY2BGR)
        circles2 = cv2.HoughCircles(edges2, cv2.HOUGH_GRADIENT, 1, 40, param1=10, param2=15, minRadius=7, maxRadius=15)

        try:
            # circles1 = np.uint16(np.around(circles1))
            circles2 = np.uint16(np.around(circles2))

            # for i in circles1[0, :]:
            #    cv2.circle(colimg1, (i[0], i[1]), i[2], (0, 255, 0), 2)
            #    cv2.circle(colimg1, (i[0], i[1]), 2, (0, 0, 255), 3)
            #    cv2.putText(colimg1, str('({},{})'.format(i[0]-img_width/2, i[1]-img_height/2)), (i[0] + 10, i[1] + 10),
            #                cv2.FONT_HERSHEY_SIMPLEX, 0.3,
            #                (0, 0, 0), 1, cv2.LINE_AA)
            positions = []

            for i in circles2[0, :]:
                positions.append(self.__map_position(i))
                cv2.circle(colimg1, (i[0], i[1]), i[2], (255, 0, 0), 2)
                cv2.circle(colimg1, (i[0], i[1]), 2, (255, 0, 255), 3)
                cv2.putText(colimg1, str('({},{})'.format(i[1] - self.__img_width / 2, i[0] - self.__img_height / 2)),
                            (i[0] + 10, i[1] + 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.3,
                            (0, 0, 0), 1, cv2.LINE_AA)
            self.__eki_socket.send_pyobj(
                positions)
        except:
            pass

        return colimg1

    def __map_position(self, i: []):
        return Position(x= (310 - i[1]) * 0.9, y=(320-i[0]) * 0.9, z=0)

    def __process__(self):
        """
        Retrieving and processing images(detecting screw location).
        """
        super().__process__()
        self.__cam_one.exposure = 10
        self.__cam_one.gain = 1
        for i in (0, 240):
            img_one, timestamps = self.__cam_one.read()
        # img_two, timestamps = self.__cam_two.read()

        if self.__eki_socket.recv_string() == 'check screws':
            img_one = self.hough_circle(img_one)
        # img_two = self.hough_circle(img_two)

        encoded, buffer = cv2.imencode('.jpg', img_one)
        msg = str(base64.b64encode(buffer))[2:-1]
        byte_msg = [bytes(DeviceForwarderTopic.CAMERA, Constant.ENCODING_FORMAT),
                    bytes(msg, Constant.ENCODING_FORMAT)]
        self._device_socket.send_multipart(byte_msg)

        # encoded, buffer = cv2.imencode('.jpg', img_two)
        # msg = str(base64.b64encode(buffer))[2:-1]
        # byte_msg = [bytes(DeviceForwarderTopic.CAMERA, Constant.ENCODING_FORMAT),
        #             bytes(msg, Constant.ENCODING_FORMAT)]
        # self._device_socket.send_multipart(byte_msg)

    def __terminate(self):
        self.__cams.end()

    def run(self):
        super().run()
