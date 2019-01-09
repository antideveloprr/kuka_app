import base64
import time

import cv2
import numpy as np
import zmq

from kuka_core.forwarder import DeviceForwarderTopic, SystemForwarderTopic
from kuka_core.kuka_services import DeviceService
from kuka_core.utils import Constant
from .pseyepy_master.pseyepy import Camera


class CameraService(DeviceService):
    """
    Pseye camera class.
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

    def __setup__(self):
        super().__setup__()
        """
        Video output devices configuration.
        """
        try:
            self.__cam_one = Camera(0, resolution=Camera.RES_LARGE, colour=False, gain=5, fps=20, exposure=100,
                                    hflip=True, vflip=True)
            self.__cam_two = Camera(1, resolution=Camera.RES_LARGE, colour=False, gain=5, fps=20, exposure=100)

            context = zmq.Context()
            self.__tool_socket = context.socket(zmq.PUB)
            self.__tool_socket.bind('tcp://127.0.0.1:8101')
        except Exception as e:
            byte_msg = [bytes(SystemForwarderTopic.ERROR, Constant.ENCODING_FORMAT),
                        bytes(str(e), Constant.ENCODING_FORMAT)]
            self._system_socket.send_multipart(byte_msg)
            self.running = False
            # TODO: terminate process and pop from processes list(from main flask process)
        time.sleep(1)

    def hough_circle(self, image):

        cimg1 = cv2.medianBlur(image, 3)

        edges1 = cv2.Canny(cimg1, 200, 255)
        edges2 = cv2.Canny(cimg1, 150, 250)

        circles1 = cv2.HoughCircles(edges1, cv2.HOUGH_GRADIENT, 1, 50, param1=50, param2=30, minRadius=20,
                                    maxRadius=150)
        colimg1 = cv2.cvtColor(cimg1, cv2.COLOR_GRAY2BGR)
        circles2 = cv2.HoughCircles(edges2, cv2.HOUGH_GRADIENT, 1, 50, param1=10, param2=15, minRadius=0, maxRadius=25)

        print('hougn circle process')
        try:
            circles1 = np.uint16(np.around(circles1))
            circles2 = np.uint16(np.around(circles2))

            for i in circles1[0, :]:
                cv2.circle(colimg1, (i[0], i[1]), i[2], (0, 255, 0), 2)
                cv2.circle(colimg1, (i[0], i[1]), 2, (0, 0, 255), 3)
                cv2.putText(colimg1, str(i[0]), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
                cv2.putText(colimg1, str(i[1]), (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
            for i in circles2[0, :]:
                cv2.circle(colimg1, (i[0], i[1]), i[2], (255, 0, 0), 2)
                cv2.circle(colimg1, (i[0], i[1]), 2, (255, 0, 255), 3)

        except:
            pass

        return colimg1

    def __process__(self):
        """
        Retrieving and processing images(detecting screw location).
        """
        super().__process__()
        img_one, timestamps = self.__cam_one.read()
        img_two, timestamps = self.__cam_two.read()

        img_one = self.hough_circle(img_one)
        img_two = self.hough_circle(img_two)

        encoded, buffer = cv2.imencode('.jpg', img_one)
        msg = str(base64.b64encode(buffer))[2:-1]
        byte_msg = [bytes(DeviceForwarderTopic.CAMERA, Constant.ENCODING_FORMAT),
                    bytes(msg, Constant.ENCODING_FORMAT)]
        self._device_socket.send_multipart(byte_msg)

        encoded, buffer = cv2.imencode('.jpg', img_two)
        msg = str(base64.b64encode(buffer))[2:-1]
        byte_msg = [bytes(DeviceForwarderTopic.CAMERA, Constant.ENCODING_FORMAT),
                    bytes(msg, Constant.ENCODING_FORMAT)]
        self._device_socket.send_multipart(byte_msg)

    def __terminate(self):
        self.__cams.end()

    def run(self):
        super().run()
