
"""

    Notes:

        1. We're going to have to save the client address each time we receive data from them. Like, for each command.



"""


import random
import os
import socket
from constants_file import DeviceTypes
from EEE466Baseline.CommunicationInterface import CommunicationInterface

import math

# --- Define Global Variables ---

SUCCESS = 1
ERROR = -1
SEED = 66

# Change these constants to create reliability errors. Their sum cannot exceed 1.0.
DROP_PROBABILITY = 0.0
REPEAT_PROBABILITY = 0.0

RECV_BUFFER_SIZE = 1028;


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

        # Attribute for timeouts
        self.timeout_time = 2;

        # Creating attributes as needed (might not need all of them)
        self.device_type = DeviceTypes.UDPCLIENT;  # Setting the device type - default to UDP client
        self.client_socket = None;
        self.server_socket = None;
        self.client_addr = None;
        self.server_addr = None;

        # --- Client only attributes ---

        self.request_id = 0;

        # --- Server only attributes ---

        self.request_database = {}; # Maybe use a dictionary?


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

        # Set timeout for 1 second for now (hardcoded)
        self.server_socket.settimeout(self.timeout_time);

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

        # Set timeout for 1 second for now (hardcoded)
        self.client_socket.settimeout(self.timeout_time);

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

        # --- If sender is Client ---

        if self.device_type == DeviceTypes.UDPCLIENT:

            # Testing for now
            self.slice_and_send_udp(self.client_socket, self.server_addr, command);

            # <------ FOR GET ------>

            # Send command, and request ID


            # Wait for ACK from server

            # Send over the file in slices

            # <------ FOR PUT ------>

            # <------ FOR QUIT ------>

            pass;


        # --- If sender is Server ---

        elif self.device_type == DeviceTypes.UDPSERVER:

            # <------ FOR GET ------>

            # <------ FOR PUT ------>

            # <------ FOR QUIT ------>

            pass;


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

        # Initialize receive data variable
        recv_data = None;

        # --- If receiver is Client ---

        if self.device_type == DeviceTypes.UDPCLIENT:

            # <------ FOR GET ------>

            # <------ FOR PUT ------>

            # <------ FOR QUIT ------>

            pass;

        # --- If receiver is Server ---

        elif self.device_type == DeviceTypes.UDPSERVER:

            # Testing for now
            recv_data = self.recv_and_parse_udp(self.server_socket);

            # <------ FOR GET ------>

            # Receive command with request ID, store in database (key = ID, command = content)

            # Reply with ACK with request ID ("ACK ID#")

            # <------ FOR PUT ------>

            # <------ FOR QUIT ------>

            pass;


        return recv_data;

    def slice_and_send_udp(self, in_socket, dest_addr, in_data):
        """
            Function slices up message in 1028 byte groups. Sending device sends
            the separate messages via UDP to the destination device.

        Args:
            <in_socket : socket> : A UDP socket object which the message is sent through.
            <dest_addr : tuple(string, port)> : The destination address to send the UDP traffic to.
            <in_data : bytes> : The data to be sent to the other device
        """





        # Create a dictionary here to put the slices and their corresponding slice identifier
        slice_dict = {};

        # Determine how many slices we are to send
        bytes_len = len(in_data);
        slice_num = math.ceil(bytes_len / RECV_BUFFER_SIZE);

        # todo STATUS: Just implemented the packet duplication handling on server side for slice number
        # todo need to handle timeout from not receiving reply here. Also, consider making adjustment of turning
        # todo duplicate packets because it would not make sense i think.

        # Send the slice number (convert to string first, then bytes)
        in_socket.sendto(b'SLICE ' + bytes(str(slice_num), 'utf-8'), dest_addr);
        in_socket.sendto(b'SLICE ' + bytes(str(slice_num), 'utf-8'), dest_addr);
        print(in_socket.recv(RECV_BUFFER_SIZE));
        print(in_socket.recv(RECV_BUFFER_SIZE));
        print(in_socket.recv(RECV_BUFFER_SIZE));
        # self.__send_with_errors(b'SLICE ' + bytes(str(slice_num), 'utf-8'), dest_addr, in_socket)

        # socket.timeout IS THE ERROR

        # Block and wait for acknowledgement to number.
        # if in_socket.recv(RECV_BUFFER_SIZE) == b'ACK NUM':
        #     print(f"{self.device_type} STATUS: Received slice number acknowledgement. Sending slices...");
        # else:
        #     pass; # TODO handle case of no reply - timeout

        # # Send via slices via UDP in order, and wait for acknowledgment each time.
        # for i in range(slice_num):
        #
        #     # Check if sending last slice
        #     if i == slice_num - 1:
        #
        #         # possibility of exceeding in_data's indices, so sending
        #         # last slice like this for good practice
        #         start_ind = i * 1028;
        #         slice_bytes = in_data[start_ind:];
        #
        #     # Otherwise, compute start and end indices for data slices
        #     else:
        #
        #         start_ind = i * 1028;
        #         end_ind = (i + 1) * 1028;
        #         slice_bytes = in_data[start_ind: end_ind]
        #
        #     # Send the slice of bytes via UDP,
        #     in_socket.sendto(slice_bytes, dest_addr);
        #
        #     # and wait for acknowledgment (todo handle retransmission here)
        #     ack_msg = b'ACK ' + bytes(str(slice_num), 'utf-8');
        #     if in_socket.recv(RECV_BUFFER_SIZE) != ack_msg:
        #         print("SHIT, WE DIDN'T GET SOMETHING BACK!");
        #         # Handle retransmission here I guess



    def recv_and_parse_udp(self, in_socket):
        """
            Function receives data slices of max size 1028 bytes from sender, and reconstructs
            the original message accordingly.

            TODO Implement possibility of packets being dropped (including with slice number sending)

        Args:
            <in_socket : socket> : A UDP socket object which the message is received from.
        Returns:
            The parsed meessage in bytes.
        """

        # Create a dictionary for duplicated responses... not?
        comm_dict = {};

        # Create dummy var to contain all the received data
        parsed_data = b'';

        # Block and wait to receive the number of slices of bytes to receive
        slice_num_data, dest_addr = in_socket.recvfrom(RECV_BUFFER_SIZE);
        slice_num = int(slice_num_data.decode()[6:]);

        # Print status
        print(f"{self.device_type} STATUS: Expect to receive {slice_num} slices of bytes from sender. "
              f"Acknowledging...");

        # Acknowledge sender slice number received
        in_socket.sendto(b'ACK NUM', dest_addr);

        # Add to dictionary the reply to what we received
        comm_dict[slice_num_data] = b'ACK NUM';

        # Receiving slices
        i = 0;
        while i < slice_num:


            # Receive data
            recv_data = in_socket.recv(RECV_BUFFER_SIZE);

            # First check if received a duplicate slice_num_data message (meaning they didn't receive our prev ack)
            if recv_data in comm_dict:

                print(f"{self.device_type} STATUS: Received duplicate packet {recv_data.decode()}. Resending response.")
                in_socket.sendto(comm_dict[recv_data], dest_addr);

                # Restart the loop again without modifying i
                continue;

            # If we received something else, we can remove the (hopefully only) element in the comm_dict history since
            # we are presuming the sender received the ack
            comm_dict.clear(); # yep this will do

            # Add to total data, and acknowledge todo handle when nothing received
            parsed_data += in_socket.recv(RECV_BUFFER_SIZE);
            ack_msg = b'ACK ' + bytes(str(slice_num), 'utf-8');
            in_socket.sendto(ack_msg, dest_addr);

            i += 1;

        # Return the parsed data
        return parsed_data;

    # You may modify or ignore this method as necessary.
    def __send_with_errors(self, msg, addr, in_socket):
        """
        This method randomly drops or duplicates a message transmission. The probability of an error is the sum of
        error probabilities.

        DROP_PROBABILITY: probability that message will be ignored.
        REPEAT_PROBABILITY: probability that message will be sent twice.

        :param msg: Message to be sent.
        :param addr: Tuple of IP address and port number to address message to.
        :param in_socket: The socket to send the errors on.
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
            in_socket.sendto(msg, addr)
            in_socket.sendto(msg, addr)
        else:
            in_socket.sendto(msg, addr)
