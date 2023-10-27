
# Import the use of enums
from enum import Enum


# Contain all the device types
class DeviceTypes(Enum):
    TCPSERVER = "TCPSERVER";
    TCPCLIENT = "TCPCLIENT";
    UDPSERVER = "UDPSERVER";
    UDPCLIENT = "UDPCLIENT";
