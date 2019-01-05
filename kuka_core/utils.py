class Constant:
    """
    Class for storing some useful constants.
    """
    ENCODING_FORMAT = 'utf-8'
    TEST_HOST = '127.0.0.1'
    TEST_PORT = '8000'


class ErrorCode:
    """
    Class for storing application runtime error codes with with theirs explanations.
    """
    ERROR_100 = 'TCP socket address is not reachable.'
    ERROR_101 = 'TCP socket address is already in use.'
    ERROR_102 = 'TCP socket connection rapidly terminated.'
    ERROR_200 = 'Cannot find any available camera device.'
    ERROR_201 = 'Camera device communication channel is already opened.'
    ERROR_300 = 'Cannot find any available tool device.'
    ERROR_301 = 'Tool device communication channel is already opened.'
