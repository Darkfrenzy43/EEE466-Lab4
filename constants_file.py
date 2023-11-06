
# Import the use of enums
from enum import Enum


# Contain all the device types
class DeviceTypes(Enum):
    TCPSERVER = "TCPSERVER";
    TCPCLIENT = "TCPCLIENT";
    UDPSERVER = "UDPSERVER";
    UDPCLIENT = "UDPCLIENT";

# Making an enum class that tracks errors
class ServerState(Enum):
    UNRECOG_COMM = 0;
    NONEXIST_FILE = 1;
    PUT_COMM = 2;
    GET_COMM = 3;
    NO_FILE = 4;
    INVALID_QUIT = 5;
    QUIT_COMM = 6;


# --- ERROR CODES ---

TIMEDOUT = b'XX_TIMEDOUT_XX'
NON_DECODABLE_NUM = b'XX_NON_DECODABLE_NUM_XX'