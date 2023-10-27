
"""

    Notes:

        1. We're going to have to save the client address each time we receive data from them. Like, for each command.



"""


import random
import os
import socket
from constants_file import DeviceTypes
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

        todo: write down the parameter explanations.
        """

        # Planting the seed
        random.seed(SEED)

        # Creating attributes as needed (might not need all of them)
        self.device_type = DeviceTypes.UDPCLIENT;  # Setting the device type - default to UDP client
        self.client_socket = None;
        self.server_socket = None;
        self.client_addr = None;
        self.server_addr = None;


        # Add your code here



    def initialize_server(self, source_port):
        """
        Performs any necessary communication setup for the server. Creates a socket and binds it to a port. The server
        listens for all IP addresses (e.g., "0.0.0.0").

        NOTE: Switches the object's device type to DeviceTypes.UDPSERVER.

        :param source_port: port that provides a service.
        """

        # Change the device type to UDP server
        self.device_type = DeviceTypes.UDPSERVER;

        # Set self.server_addr as a tuple
        self.server_addr = ('localhost', source_port);

        # Bind a UDP socket to the server address
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);
        self.server_socket.bind(self.server_addr);

        # Print statement for status
        print(f"{self.device_type} COMM STATUS: Server bounded and listening on UDP port {self.server_addr[1]}...")


    def initialize_client(self, address, destination_port):
        """
        Performs any necessary communication setup for the client. Creates a socket and attempts to connect to the
        server.

        :
        :param address: The server address to send UDP traffic to.
        :param destination_port: The server port to send UDP traffic to.
        """

        # Stop calling of function if detected not a client
        if self.device_type != DeviceTypes.UDPCLIENT:
            print(f"ERROR: Can't establish a client connection with device type {self.device_type}.");
            return;

        # Set server address attribute
        self.server_addr = (address, destination_port);

        # Create the UDP socket for the client
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);

        # Print status
        print(f"{self.device_type} COMM STATUS: Initialized client socket to send "
              f"traffic to server at  {self.server_addr}.")

    def send_command(self, command):
        """
        Sends a command from the client to the server. At a minimum this includes GET, PUT, QUIT and their parameters.

        This method may also be used to have the server return information, i.e., ACK, ERROR. This method can be used to
        inform the client or server of the filename ahead of sending the data.

        UDP ADDITIONS:
            - commands now sent with request IDs
            - commands and their request IDs are saved in a history
                - history is used to handle dropped messages and duplicated requests
            - The way how commands are sent depend on the command

        :param command: The command you wish to send to the server.
        """

        # Determine the socket to use to send, depending on the type of sending device (default to client)
        sending_socket = self.initial_socket;
        if self.device_type == DeviceTypes.TCPSERVER:
            sending_socket = self.server_socket;

        # Check if the TCP connection still exists, and that the sender and receiver
        # agree in terms of the format of the transmitted data. If not, stop function
        if self.verify_sender(sending_socket, b'COMM ACK'):
            return;

        # Convert msg into utf-8 bytes
        send_data = bytes(command, 'utf-8');

        # Send message to the client (slice up into 1028 byte msgs if needed)
        self.slice_and_send(sending_socket, send_data);

    def receive_command(self):
        """
        This method should be called by the server to await a command from the client. It can also be used by the
        client to receive information such as an ACK or ERROR message.

        UDP ADDITIONS:
            - commands now sent with request IDs
            - commands and their request IDs are saved in a history
                - history is used to handle dropped messages and duplicated requests
            - The way how commands are received depend on the command

        :return: the command received and any parameters.
        """

        # Determine the socket to receive from, depending on the type of current receiving device (default to client)
        receiving_socket = self.initial_socket;
        if self.device_type == DeviceTypes.TCPSERVER:
            receiving_socket = self.server_socket;

        # Check if the TCP connection still exists, and that the sender and receiver
        # agree in terms of the format of the transmitted data. If not, stop function
        if self.verify_receiver(receiving_socket, b'COMM ACK'):
            return;

        # Receive the data bytes from the server
        recv_msg = self.recv_and_parse(receiving_socket);

        # Decode and return received command
        return recv_msg.decode();

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
