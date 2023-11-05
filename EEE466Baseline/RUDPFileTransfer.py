
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
import datetime

# --- Define Global Variables ---

SUCCESS = 1
ERROR = -1
SEED = 66

# Change these constants to create reliability errors. Their sum cannot exceed 1.0.
DROP_PROBABILITY = 0.0
REPEAT_PROBABILITY = 0.80

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

        send_data = bytes(command, 'utf-8');

        # --- If sender is Client ---

        if self.device_type == DeviceTypes.UDPCLIENT:

            # Testing for now
            self.slice_and_send_udp(self.client_socket, self.server_addr, send_data);

        # --- If sender is Server ---

        elif self.device_type == DeviceTypes.UDPSERVER:

            self.slice_and_send_udp(self.server_socket, self.client_addr, send_data);

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
            recv_data = self.recv_and_parse_udp(self.client_socket);

        # --- If receiver is Server ---
        elif self.device_type == DeviceTypes.UDPSERVER:
            recv_data = self.recv_and_parse_udp(self.server_socket);



        return recv_data.decode();

    def slice_and_send_udp(self, in_socket, recv_addr, in_data):
        """
            Function slices up message in 1028 byte groups. Sending device sends
            the separate messages via UDP to the destination device.

        Args:
            <in_socket : socket> : A UDP socket object which the message is sent through.
            <recv_addr : tuple(string, port)> : The destination address to send the UDP traffic to.
            <in_data : bytes> : The data to be sent to the other device
        """

        # Note: We want to ignore any duplicate ACKS we get from the receiving device,
        # so, we'll create an ack history (probably a list) to contain the most recent
        # ack from the receiver, and if we get a duplicate ack, we can recognize it if it is
        # in the ack history and ignore it accordingly. As soon as we get a different ack
        # (the ack to the next message sent), then we can replace the recent ack history with
        # what we just received, since we can anticipate any duplicate acks to be of that kind

        # Creating ack history to store the most recent ACK from receiver
        ack_history = [];

        # Determine how many slices we are to send
        bytes_len = len(in_data);
        slice_num = math.ceil(bytes_len / RECV_BUFFER_SIZE);

        print(bytes_len);

        # Okay, we're going to take a streamlined approach to sending the messages over,
        # including the slice number to send - this is to ensure we ignore any duplicated acks
        ack_msg = b'';
        send_data = b'';
        i = 0;
        while i < slice_num + 1:

            print(f"[{datetime.datetime.utcnow()}] ", end="")

            # For first iteration (when i = 0), send slice number
            if i == 0:

                # Configure data to send and ack msg to expect to receive
                send_data = b'SLICE ' + bytes(str(slice_num), 'utf-8')
                ack_msg = b'ACK NUM';

            else:

                temp_i = i - 1;  # Used for calculations of the slices

                # Check if sending last slice (remember, we added an extra iteration to send
                # the slice numbers, so the last slice of data to send would be when i == slice_num
                if i == slice_num:

                    # possibility of exceeding in_data's indices, so sending
                    # last slice like this for good practice
                    start_ind = temp_i * 1028;
                    send_data = in_data[start_ind:];

                # Otherwise, compute start and end indices for data slices
                else:

                    start_ind = temp_i * 1028;
                    end_ind = (temp_i + 1) * 1028;
                    send_data = in_data[start_ind: end_ind]

                # Configure ack messasge expect to receive
                ack_msg = b'ACK ' + bytes(str(i - 1), 'utf-8');


            print(f"Sending data length: {len(send_data)}")
            # Send info (with errors)
            print(f"{self.device_type} SENDING: Sending data, expecting ack of {ack_msg.decode()}")
            self.__send_with_errors(send_data, recv_addr, in_socket);
            # in_socket.sendto(send_data, recv_addr);


            # Wait for ack with timeout possibility
            try:
                recv_data = in_socket.recv(RECV_BUFFER_SIZE);

            except socket.timeout:

                if i == 0:
                    print(f"{self.device_type} ERROR: No ACK received before timeout. Retransmitting slice number.")
                else:
                    print(f"{self.device_type} ERROR: No ACK received before timeout. Retransmitting slice {i - 1}.");
                continue;

            # todo won't we encounter the case where in one recv_data buffer read,
            # todo we'll have the duplicate acks there ie. 'ACK 1ACK 1'? We'll have to see.

            # Check if the ack received is what we were expecting, or if it
            # was the previous ack received. If former, proceed with next message to send,
            # if latter, ignore it and proceed with next one
            print(f"[{datetime.datetime.utcnow()}] ", end = "")
            if recv_data == ack_msg:

                # Replace the ack in the ack_history with newly received ack, and continue
                # (account for case if was empty)
                if len(ack_history) == 0:
                    ack_history.append(ack_msg);
                else:
                    ack_history[0] = ack_msg;

                print(f"{self.device_type} STATUS: Received ack {recv_data.decode()}. ack_history contains "
                      f"{ack_history[0].decode()}.");

            elif recv_data in ack_history:

                # Don't increment i because we would inadvertently skip the current i slice. Basically, we retransmit
                # the current i slice in the end lol
                print(f"{self.device_type} STATUS: Received DUPLICATE ack for {ack_history[0].decode()}. Retransmitting"
                      f" slice {i - 1}.");
                continue;

            else:
                print(f"{self.device_type} ERROR: Received an unexpected ack.\n"
                      f"Expected ack message {ack_msg.decode()}, received {recv_data.decode()}.");

            # Increment i here
            i += 1;



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

        # Note: We want to resend ACKS if we get duplicate messages from the sender

        # Create a dictionary of messages received from sender. Used to handle duplicated responses.
        recv_msg_history = {};

        # Create dummy vars to contain all the received data, and the sender's address
        parsed_data = b'';
        slice_num_data = None;
        sender_addr = None;

        # todo how are we handling duplicates for this slice receiving part?

        # Block and wait to receive the number of slices of bytes to receive.
        # Account for possibility of timeout (note, nothing to retransmit though here)
        while True:
            try:
                slice_num_data, sender_addr = in_socket.recvfrom(RECV_BUFFER_SIZE);
                break;
            except socket.timeout:
                print(f"{self.device_type} STATUS: UDP receive socket timed out waiting for slice number. Trying again.");
                continue;

        # Decode data to find number of slices to receive
        slice_num = int(slice_num_data.decode()[6:]);
        print(f"[{datetime.datetime.utcnow()}] ", end = "")
        print(f"{self.device_type} STATUS: Expect to receive {slice_num} slices of bytes from sender. "
              f"Acknowledging...");

        # Acknowledge sender slice number received, and add received msg and returned ack to history
        # self.__send_with_errors(b'ACK NUM', sender_addr, in_socket);
        in_socket.sendto(b'ACK NUM', sender_addr);
        print(f"[{datetime.datetime.utcnow()}] : Sent back acknowledgement for slice number.")
        recv_msg_history[slice_num_data] = b'ACK NUM';

        # Receiving slices (use while loop to account for repeated replies)
        i = 0;
        while i < slice_num:

            print(f"[{datetime.datetime.utcnow()}] ", end="")

            # Receive data (account for timeout possibility)
            recv_data = None;
            while True:
                try:
                    recv_data = in_socket.recv(RECV_BUFFER_SIZE);
                    break;
                except socket.timeout:
                    print(
                        f"{self.device_type} STATUS: UDP receive socket timed out waiting for slice {i}. Trying again.");
                    continue;


            # First check if received a duplicate message
            if recv_data in recv_msg_history:

                # If so, reply with the duplicated message's corresponding ack
                print(f"{self.device_type} STATUS: Received duplicate packet for response {recv_msg_history[recv_data]}."
                      f" Duplicate had length {len(recv_data)}. Resending response.")
                #self.__send_with_errors(recv_msg_history[recv_data], sender_addr, in_socket);
                in_socket.sendto(recv_msg_history[recv_data], sender_addr);

                # Do a dummy read here to clear any data that may have been collected in the buffer before
                # receiving the duplicate message
                in_socket.recv(RECV_BUFFER_SIZE);

                # Restart the loop again without modifying i
                continue;

            else:
                print(len(recv_msg_history))

                print(f"{self.device_type} STATUS: Received data for slice {i} of length {len(recv_data)}.")

            # If we received something else, we can remove the (hopefully only) element in the comm_dict history since
            # we are presuming the sender received the ack
            recv_msg_history.clear(); # yep this will do

            # Add to total data, and acknowledge
            parsed_data += recv_data;
            ack_msg = b'ACK ' + bytes(str(i), 'utf-8');
            recv_msg_history[recv_data] = ack_msg;
            # self.__send_with_errors(ack_msg, sender_addr, in_socket);
            in_socket.sendto(ack_msg, sender_addr);

            # Increment i
            i += 1;

        # Return the parsed data
        print(len(parsed_data));
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
            print(f"[{datetime.datetime.utcnow()}]: First sent")
            in_socket.sendto(msg, addr)
            print(f"[{datetime.datetime.utcnow()}]: Duplicate sent")
            in_socket.sendto(msg, addr)
        else:
            in_socket.sendto(msg, addr)
