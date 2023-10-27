import random
import os
import socket
from EEE466Baseline.CommunicationInterface import CommunicationInterface

SUCCESS = 1
ERROR = -1
SEED = 66

# Change these constants to create reliability errors. Their sum cannot exceed 1.0.
DROP_PROBABILITY = 0.0
REPEAT_PROBABILITY = 0.0


class RUDPFileTransfer(CommunicationInterface):
    """
    This class inherits and implements the CommunicationInterface. It enables
    reliable file transfers between client and server using UDP.
    """

    def __init__(self):
        """
        This method is used to initialize your Communication Interface object.
        """
        self.sock = None
        random.seed(SEED)
        # Add your code here

    # You may modify or ignore this method as necessary.
    def __send_with_errors(self, msg, addr):
        """
        This method randomly drops or duplicates a message transmission. The probability of an error is the sum of
        error probabilities.

        DROP_PROBABILITY: probability that message will be ignored.
        REPEAT_PROBABILITY: probability that message will be sent twice.

        :param msg: Message to be sent.
        :param addr: Tuple of IP address and port number to address message to.
        """

        send_errors = {
            "drop": DROP_PROBABILITY,
            "repeat": REPEAT_PROBABILITY,
        }
        send_errors["none"] = 1 - sum(send_errors.values())

        selected_error = random.choices(list(send_errors.keys()), list(send_errors.values()))[0]

        if selected_error == "drop":
            return
        elif selected_error == "repeat":
            self.sock.sendto(msg, addr)
            self.sock.sendto(msg, addr)
        else:
            self.sock.sendto(msg, addr)
