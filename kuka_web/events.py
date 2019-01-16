from flask_socketio import SocketIO

from init_utils import logger
from kuka_core import InternalAddress
from kuka_core.forwarder import Forwarder, DeviceForwarderTopic, SystemForwarderTopic
from kuka_core.kuka_services.kuka_camera import CameraService
from kuka_core.kuka_services.kuka_eki import EkiServerService
from kuka_core.kuka_services.kuka_tool import ToolService
from kuka_web import app
from kuka_web.listener import Listener

listeners = dict()
devices = dict()
forwarders = dict()
processes = dict()

socketio = SocketIO(app, async_mode='threading')


@socketio.on('connect')
def connect():
    """
    Configures and initializes system and device layer forwarders.
    """
    logger.info('browser client connected')
    system_forwarder = Forwarder(topic=SystemForwarderTopic.FORWARDER,
                                 pub_addr=InternalAddress.SYSTEM_PUB,
                                 sub_addr=InternalAddress.SYSTEM_SUB)

    device_forwarder = Forwarder(topic=DeviceForwarderTopic.FORWARDER,
                                 pub_addr=InternalAddress.DEVICE_PUB,
                                 sub_addr=InternalAddress.DEVICE_SUB)

    internal_forwarder = Forwarder(topic=DeviceForwarderTopic.FORWARDER_INTERNAL,
                                   pub_addr=('127.0.0.1', 8100),
                                   sub_addr=('127.0.0.1', 8101))

    internal_forwarder.running = True
    if DeviceForwarderTopic.FORWARDER_INTERNAL not in forwarders.keys():
        forwarders[DeviceForwarderTopic.FORWARDER_INTERNAL] = internal_forwarder
        forwarders.get(DeviceForwarderTopic.FORWARDER_INTERNAL).start()

    system_forwarder.running = True
    if SystemForwarderTopic.FORWARDER not in forwarders.keys():
        forwarders[SystemForwarderTopic.FORWARDER] = system_forwarder
        forwarders.get(SystemForwarderTopic.FORWARDER).start()

    device_forwarder.running = True
    if DeviceForwarderTopic.FORWARDER not in forwarders.keys():
        forwarders[DeviceForwarderTopic.FORWARDER] = device_forwarder
        forwarders.get(DeviceForwarderTopic.FORWARDER).start()


@socketio.on('disconnect')
def disconnect():
    """
    Terminates system and device layer forwarders.
    """
    logger.info('browser client disconnected')
    if SystemForwarderTopic.FORWARDER in forwarders.keys():
        system_forwarder = forwarders.get(SystemForwarderTopic.FORWARDER)
        system_forwarder.running = False
        system_forwarder.terminate()
        system_forwarder.join()
        forwarders.pop(SystemForwarderTopic.FORWARDER)

    if DeviceForwarderTopic.FORWARDER in forwarders.keys():
        device_forwarder = forwarders.get(DeviceForwarderTopic.FORWARDER)
        device_forwarder.running = False
        device_forwarder.terminate()
        device_forwarder.join()
        forwarders.pop(DeviceForwarderTopic.FORWARDER)

    if DeviceForwarderTopic.FORWARDER_INTERNAL in devices.keys():
        internal_forwarder = devices.get(DeviceForwarderTopic.FORWARDER_INTERNAL)
        internal_forwarder.running = False
        internal_forwarder.terminate()
        internal_forwarder.join()
        devices.pop(DeviceForwarderTopic.FORWARDER_INTERNAL)


@socketio.on('tcp_start')
def tcp_start(data):
    """
    Initializes listeners and devices processes with given communication address.
    :param data: communication address
    """
    host = data['host']
    port = int(data['port'])

    eki_listener = Listener(address=InternalAddress.DEVICE_SUB,
                            topic=DeviceForwarderTopic.EKI,
                            processing_time=0.5)

    tool_listener = Listener(address=InternalAddress.DEVICE_SUB,
                             topic=DeviceForwarderTopic.TOOL,
                             processing_time=0.5)

    camera_listener = Listener(address=InternalAddress.DEVICE_SUB,
                               topic=DeviceForwarderTopic.CAMERA,
                               processing_time=0.01)

    log_listener = Listener(address=InternalAddress.SYSTEM_SUB,
                            topic=SystemForwarderTopic.LOG,
                            processing_time=0.5)

    error_listener = Listener(address=InternalAddress.SYSTEM_SUB,
                              topic=SystemForwarderTopic.ERROR,
                              processing_time=0.5)

    eki_addr = (host, port)
    eki_service = EkiServerService(topic=DeviceForwarderTopic.EKI,
                                   device_pub_addr=InternalAddress.DEVICE_PUB,
                                   system_pub_addr=InternalAddress.SYSTEM_PUB,
                                   processing_time=0.01,
                                   eki_addr=eki_addr)

    tool_service = ToolService(topic=DeviceForwarderTopic.TOOL,
                               device_pub_addr=InternalAddress.DEVICE_PUB,
                               system_pub_addr=InternalAddress.SYSTEM_PUB,

                               processing_time=10,
                               serial_port_addr='COM4',
                               serial_baud_rate=115200)

    camera_service = CameraService(topic=DeviceForwarderTopic.CAMERA,
                                   device_pub_addr=InternalAddress.DEVICE_PUB,
                                   system_pub_addr=InternalAddress.SYSTEM_PUB,
                                   processing_time=0.1)

    eki_listener.running = True
    if DeviceForwarderTopic.EKI not in listeners.keys():
        listeners[DeviceForwarderTopic.EKI] = eki_listener
        listeners.get(DeviceForwarderTopic.EKI).start()
        print('Eki listener started.')

    tool_listener.running = True
    if DeviceForwarderTopic.TOOL not in listeners.keys():
        listeners[DeviceForwarderTopic.TOOL] = tool_listener
        listeners.get(DeviceForwarderTopic.TOOL).start()
        print('Tool listener started.')

    camera_listener.running = True
    if DeviceForwarderTopic.CAMERA not in listeners.keys():
        listeners[DeviceForwarderTopic.CAMERA] = camera_listener
        listeners.get(DeviceForwarderTopic.CAMERA).start()
        print('Camera listener started.')

    log_listener.running = True
    if SystemForwarderTopic.LOG not in listeners.keys():
        listeners[SystemForwarderTopic.LOG] = log_listener
        listeners.get(SystemForwarderTopic.LOG).start()
        print('Log listener started.')

    error_listener.running = True
    if SystemForwarderTopic.ERROR not in listeners.keys():
        listeners[SystemForwarderTopic.ERROR] = error_listener
        listeners.get(SystemForwarderTopic.ERROR).start()
        print('Error listener started.')

    eki_service.running = True
    if DeviceForwarderTopic.EKI not in devices.keys():
        devices[DeviceForwarderTopic.EKI] = eki_service
        devices.get(DeviceForwarderTopic.EKI).start()
        print('Eki service started.')

    tool_service.running = True
    if DeviceForwarderTopic.TOOL not in devices.keys():
        devices[DeviceForwarderTopic.TOOL] = tool_service
        devices.get(DeviceForwarderTopic.TOOL).start()
        print('Tool service started.')

    camera_service.running = True
    if DeviceForwarderTopic.CAMERA not in devices.keys():
        devices[DeviceForwarderTopic.CAMERA] = camera_service
        devices.get(DeviceForwarderTopic.CAMERA).start()
        print('Camera service started.')

    # # TODO: implement manual testing client
    # tcp_client = TcpClientProcess((host, port))
    # tcp_client.running = True
    # if 'tcp_client' not in processes.keys():
    #     processes['tcp_client'] = tcp_client
    #     processes.get('tcp_client').start()


@socketio.on('tcp_stop')
def tcp_stop(data):
    """
    Terminates listeners and devices processes with given communication address.
    :param data: communication address
    """
    host = data['host']
    port = int(data['port'])

    if DeviceForwarderTopic.TOOL in listeners.keys():
        tool_listener = listeners.get(DeviceForwarderTopic.TOOL)
        tool_listener.running = False
        listeners.pop(DeviceForwarderTopic.TOOL)
        print('Tool listener terminated.')

    if DeviceForwarderTopic.CAMERA in listeners.keys():
        camera_listener = listeners.get(DeviceForwarderTopic.CAMERA)
        camera_listener.running = False
        listeners.pop(DeviceForwarderTopic.CAMERA)
        print('Camera listener terminated.')

    if DeviceForwarderTopic.EKI in listeners.keys():
        eki_listener = listeners.get(DeviceForwarderTopic.EKI)
        eki_listener.running = False
        listeners.pop(DeviceForwarderTopic.EKI)
        print('Eki listener terminated.')

    if SystemForwarderTopic.LOG in listeners.keys():
        log_listener = listeners.get(SystemForwarderTopic.LOG)
        log_listener.running = False
        listeners.pop(SystemForwarderTopic.LOG)
        print('Log listener terminated.')

    if SystemForwarderTopic.ERROR in listeners.keys():
        error_listener = listeners.get(SystemForwarderTopic.ERROR)
        error_listener.running = False
        listeners.pop(SystemForwarderTopic.ERROR)
        print('Error listener terminated.')

    if DeviceForwarderTopic.CAMERA in devices.keys():
        camera_service = devices.get(DeviceForwarderTopic.CAMERA)
        camera_service.running = False
        camera_service.terminate()
        camera_service.join()
        devices.pop(DeviceForwarderTopic.CAMERA)
        print('Camera service terminated.')

    if DeviceForwarderTopic.TOOL in devices.keys():
        tool_service = devices.get(DeviceForwarderTopic.TOOL)
        tool_service.running = False
        tool_service.terminate()
        tool_service.join()
        devices.pop(DeviceForwarderTopic.TOOL)
        print('Tool service terminated.')

    if DeviceForwarderTopic.EKI in devices.keys():
        eki_service = devices.get(DeviceForwarderTopic.EKI)
        eki_service.running = False
        eki_service.terminate()
        eki_service.join()
        devices.pop(DeviceForwarderTopic.EKI)
        print('Eki service terminated.')

    # if 'tcp_client' in processes.keys():
    #     tcp_client = processes.get('tcp_client')
    #     tcp_client.running = False
    #     tcp_client.terminate()
    #     tcp_client.join()
    #     processes.pop('tcp_client')
