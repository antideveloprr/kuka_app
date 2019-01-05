import base64
import time

import cv2

from kuka_core.forwarder import DeviceForwarderTopic, SystemForwarderTopic
from kuka_core.kuka_services import DeviceService
from kuka_core.utils import Constant
from .pseyepy_master.pseyepy import Camera


class CameraService(DeviceService):
    """

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

        """
        try:
            self.__cams = Camera([0, 1], resolution=Camera.RES_LARGE, colour=True, gain=5, fps=20, exposure=100)
        except Exception as e:
            byte_msg = [bytes(SystemForwarderTopic.ERROR, Constant.ENCODING_FORMAT),
                        bytes(str(e), Constant.ENCODING_FORMAT)]
            self._system_socket.send_multipart(byte_msg)
            self.running = False
            print(self.__class__.__name__, ' service work has been stopped.')
            # TODO: terminate process and pop from processes list(from main flask process)
        time.sleep(1)

    def __process__(self):
        """

        """
        super().__process__()
        imgs, timestamps = self.__cams.read()
        for img in imgs:
            encoded, buffer = cv2.imencode('.jpg', img)
            msg = str(base64.b64encode(buffer))[2:-1]
            byte_msg = [bytes(DeviceForwarderTopic.CAMERA, Constant.ENCODING_FORMAT),
                        bytes(msg, Constant.ENCODING_FORMAT)]
            self._device_socket.send_multipart(byte_msg)

    def __terminate(self):
        self.__cams.end()

    def run(self):
        super().run()
