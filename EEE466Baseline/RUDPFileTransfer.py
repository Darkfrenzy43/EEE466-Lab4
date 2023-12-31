
"""

    Notes: Ehh some of these are no longer valid :). You're still welcome to read them to see the evolution of the
    program.

        1. We're going to have to save the client address each time we receive data from them. Like, for each command.

        2. Note on slice_and_send_udp() function:

            2.1: We want to ignore any duplicate ACKS we get from the receiving device,
            so, we'll create an ack history (probably a list) to contain the most recent
            ack from the receiver, and if we get a duplicate ack, we can recognize it if it is
            in the ack history and ignore it accordingly. As soon as we get a different ack
            the ack to the next message sent), then we can replace the recent ack history with
            what we just received, since we can anticipate any duplicate acks to be of that kind

            2.2: Okay, we're going to take a streamlined approach to sending the messages over,
            including the slice number to send - this is to ensure we ignore any duplicated acks for all sent msgs.

        3. Note on slice_and_send_udp() and recv_and_parse_udp():

            3.1: So contrary to the TCP version, I decided to use while loops for the sending and receiving of packets.
            Reason being is that the "counter" of the while loop will have the same value for given iterations
            depending on the unreliability of the network. To be more specific, say if the sender function is currently
            sending slice 3, and the receiving function does not receive the slice of data so no acknowledgement is
            sent back, then the sender function must re-iterate the same loop with the same counter value to
            send slice 3 again. This same principle applies for any duplicate or dropped packets in any order
            part of the transmission of data.

        4. Note on recv_and_parse_udp():

            4.1: So we're going to have to turn off timeouts when this function is waiting to receive a
            slice number. That's because this blocking receive would be the server's resting state when
            the user tries to figure out what command to send to the server. If we didn't turn off the
            timeouts (or disable them) then it would be impossible for the server to be used.


        5. Socket flushing:

            5.1: Huh, so I've encountered errors where invoking send file and send command functions back
            to back resulted in some strange behaviour where the sockets were reading data that were from
            previous UDP transactions. Of course with the way the code was written that would get into
            some issues as it would read an ACK as some data that was sent in a previous transaction.
            Thus, I figured after every use of a socket (either sending or receiving) we'll just have
            good practice of ensuring it is all emptied out before the next time it's used.

            5.2: Guess what! We're also doing it before any socket use, just to be sure. Wouldn't hurt to do so.
            Also because for some reason the flushing out still didn't flush everrrrything out - some data
            may still have been in transmission and hadn't arrived before the next time the server waits for input,
            basically meaning stuff will break.


        6. Last ACK not sent to sender: NO LONGER APPLIES

            6.1: I'm encountering an annoying problem where there are often times when the last acknowledgement
            to send to the sender device gets dropped. The thing is, it's not an entire issue because at some point
            the client and the server will return to normal operations again after timeouts, but it's still
            an annoying situation. Honestly, I can't think of any solutions to it - in the end what had needed
            to be sent was sent in terms of data over the wire.

        7. Making the message history list and dictionary a class wide attribute: NO LONGER APPLIES

            7.1: Yeah so I was also encountering another problem with UDP, where if the final message a sender or
            receiver sends to the other in a conversation, if it a duplicate, then 99% of the time the duplicates
            of the message end up getting passed as input in whatever next data transaction takes place, and
            consequently it screws everything up. that's when I realized I can't have these message histories span
            between messages within the scope of a given conversation, but also between the first and last messages
            of separate transactions. Hope this works.

        8. The most recent changes:

            8.1: Alright, the code has evolved a lot since the last time. The sender device in an transaction
            is even implemented to respond to FIN msgs with FIN ACKs when it would be expecting a regular ACK reply.
            I ran into a lot of bugs because of things like these, which caused the program to hang.
            Many other implementations like this were made to account for all the cases that could possibly
            make the sender and receiver hang - either a lot of it was having more possible cases accounted for
            like receiving a FIN ack when you're the sender. Hopefully it should be good to go now.


"""


import random
import socket
from constants_file import DeviceTypes, TIMEDOUT, NON_DECODABLE_NUM         # <-- Importing error codes in bytes
from EEE466Baseline.CommunicationInterface import CommunicationInterface

import math

from enum import Enum


# --- Define Global Variables ---

SUCCESS = 1
ERROR = -1
SEED = 66

# Change these constants to create reliability errors. Their sum cannot exceed 1.0.
DROP_PROBABILITY = 0.4
REPEAT_PROBABILITY = 0.3

# Constant that manages the receive buffer size
RECV_BUFFER_SIZE = 1028;

# Constant that manages max timeouts
MAX_TIMEOUTS = 10;


class RUDPFileTransfer(CommunicationInterface):
    """
    This class inherits and implements the CommunicationInterface. It enables
    reliable file transfers between client and server using UDP.
    """

    def __init__(self):
        """
        This method is used to initialize your Communication Interface object.
        """

        # Planting the seed
        random.seed(SEED)

        # Attribute for timeouts
        self.timeout_time = 0.5;

        # Creating attributes as needed
        self.device_type = DeviceTypes.UDPCLIENT;  # Setting the device type - default to UDP client
        self.client_socket = None;
        self.server_socket = None;
        self.client_addr = None;
        self.server_addr = None;

        # Creating ack history to store the most recent ACK from receiver device (refer to notes 6)
        self.ack_history = [];

        # Create a dictionary of messages received from sender. Will store one
        # "received msg" : "ACK Response" pair at a time. (Refer to notes 6)
        self.recv_msg_history = {};


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
            print(f"ERROR: Can't initialize as a UDP client with device type {self.device_type}.");
            return;

        # Set server address attribute
        self.server_addr = (address, destination_port);

        # Create the UDP socket for the client
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);

        # Set timeout for socket
        self.client_socket.settimeout(self.timeout_time);

        # Print status
        print(f"{self.device_type} COMM STATUS: Initialized client socket to send "
              f"traffic to server at  {self.server_addr}.")


    def send_command(self, command):

        """
        Sends a command from the client to the server. At a minimum this includes GET, PUT, QUIT and their parameters.

        This method may also be used to have the server return information, i.e., ACK, ERROR. This method can be used to
        inform the client or server of the filename ahead of sending the data.

        :param command: The command you wish to send to the server as a string.
        Returns: The UDP error code should one arise (i.e. TIMEDOUT or NON_DECODABLE_NUM).
        """
        # Convert inputted data into bytes
        send_data = bytes(command, 'utf-8');

        # Send it over the wire (ensure using correct socket depending on device type).
        # Return any UDP error codes that may have occurred during sending
        return_result = None;
        if self.device_type == DeviceTypes.UDPCLIENT:
            return_result = self.slice_and_send_udp(self.client_socket, self.server_addr, send_data);
        elif self.device_type == DeviceTypes.UDPSERVER:
            return_result = self.slice_and_send_udp(self.server_socket, self.client_addr, send_data);

        return return_result;


    def receive_command(self):
        """
        This method should be called by the server to await a command from the client. It can also be used by the
        client to receive information such as an ACK or ERROR message.

        :return: the command received and any parameters as a string, or a UDP error code as a string as well.
        """

        # Determine the socket to receive on depending on device type
        recv_socket = None;
        if self.device_type == DeviceTypes.UDPCLIENT:
            recv_socket = self.client_socket;
        elif self.device_type == DeviceTypes.UDPSERVER:
            recv_socket = self.server_socket;

        # Receive the command and return result (could also be sending back UDP error codes should any arise).
        recv_data = self.recv_and_parse_udp(recv_socket, False);
        return recv_data.decode();


    def send_file(self, file_path):
        """
        Transfers a file via UDP from the local directory to the "remote" directory.
        Can be used by either client (i.e., in a put request), or by the server when receiving a get request.

        This method will need to read the file from the sender's folder and transmit it over the connection. If the
        file is larger than 1028 bytes, it will need to be broken into multiple buffer reads.

        In the event a UDP error occurs (a timeout), the function aborts sending the file.

        :param file_path: the location of the file to send. E.g., ".\Client\Send\\ploadMe.txt".
        """

        # Print statement for status
        path_separated = file_path.split('\\');
        file_name = path_separated[-1];
        print(f"\n{self.device_type} COMM STATUS: Sending file <{file_name}> in directory "
              f"[{file_path[:-len(file_name)]}] to other device...")

        # Determine the socket to use to send and the address to send to,
        # depending on the type of sending device (Default to client)
        sending_socket = self.client_socket;
        recv_addr = self.server_addr
        if self.device_type == DeviceTypes.UDPSERVER:
            sending_socket = self.server_socket;
            recv_addr = self.client_addr;

        # Open 'utf-8' file to read with with(), specifying the encoding [ref Notes 3]...
        with open(file_path, encoding = 'utf-8') as open_file:

            # Read the file contents into bytes (.read() returns a string, we convert to bytes)
            file_data = bytes(open_file.read(), 'utf-8');

            # Send the data. If so, a timeout ever happens during transaction, abort sending the file
            result = self.slice_and_send_udp(sending_socket, recv_addr, file_data);
            if result == TIMEDOUT:
                print(f"{self.device_type} ERROR: Timeout detected while sending file. Terminating.")
                return;

        # Print status
        print(f"{self.device_type} COMM STATUS: File <{file_name}> finished sending.")


    def receive_file(self, file_path):
        """
        Receives a filename and data over the a UDP communication channel to be saved in the local directory.
        Can be used by the client or the server.

        This method has a maximum buffer size of 1028 bytes. Multiple reads from the channel are required for larger
        files. This method writes the data it receives to the client or server "Receive" directory. Note: the filename
        must be sent over the wire and cannot be hard-coded.

        In the event a UDP error occurs (a timeout or non-decodable packet received), the function aborts
        sending the file.

        :param file_path: this is the destination where you wish to save the file. E.g.,
        ".\Server\Receive\\ploadMe.txt".
        """

        # Printing the status
        path_separated = file_path.split('\\');
        file_name = path_separated[-1];
        print(f"\n{self.device_type} COMM STATUS: Receiving file and placing it in directory "
              f"[{file_path[:-len(file_name)]}] under name <{file_name}>.")

        # Determine the socket to receive on and the address sending the data,
        # depending on the type of sending device (Default to client)
        receiving_socket = self.client_socket;
        if self.device_type == DeviceTypes.UDPSERVER:
            receiving_socket = self.server_socket;

        # Open the file to write the received file info. If none exists, create one at path file_path
        with open(file_path, 'w', encoding = 'utf-8') as open_file:

            # Receiving the data from the sender
            recv_data = self.recv_and_parse_udp(receiving_socket, True).decode();

            # Check if there was a UDP error receiving the file.
            if recv_data == TIMEDOUT.decode():
                print(f"{self.device_type} ERROR: Detected timeout while receiving file. Terminating attempt to "
                      f"receive file.");
                open_file.write("\nTimeout occurred during receiving process. Receiving process aborted.");
                return;
            elif recv_data == NON_DECODABLE_NUM.decode():
                print(f"{self.device_type} ERROR: Detected a bad packet was received. Terminating attempt to receive"
                      f"file");
                open_file.write("\nDetected bad packet received. Receiving process aborted.");
                return;

            # If successful, write received data to the file (wow python makes this easy)
            open_file.write(recv_data);

        print(f"{self.device_type} COMM STATUS: File <{file_name}> fully received.")



    # --- Making UDP versions of the lower-level message transmission methods ---

    def flush_socket(self, in_socket):
        """ (Refer to notes 5) Method ensures that the given socket is completely empty when called.
        After repeatedly calling receive method and timing out after 0.2 seconds, function terminates.

        Args:
            <in_socket : socket> : The socket to flush the buffer of. """

        in_socket.settimeout(0.5);
        while True:
            try:
                in_socket.recv(RECV_BUFFER_SIZE);
            except socket.timeout:
                break;
        in_socket.settimeout(self.timeout_time);


    def slice_and_send_udp(self, in_socket, recv_addr, in_data):
        """
            Function slices up message in 1028 byte groups. Sending device sends
            the separate messages via UDP to the destination device.

            Accounts for unreliability of network (dropped and duplicated packets, complete network failure).

        Args:
            <in_socket : socket> : A UDP socket object which the message is sent through.
            <recv_addr : tuple(string, port)> : The destination address to send the UDP traffic to.
            <in_data : bytes> : The data to be sent to the other device
        Returns:
            Returns the TIMEDOUT error code if a timeout occurs.

        """

        # Print for formatting
        print("\n\n" + "-" * 15 + " SENDING LOG " + "-" * 15);

        # Print this for debugging:
        print_data = in_data.decode();
        if len(print_data) > 13:
            print_data = print_data[:13] + "...";
        print(f"\nMessage to send: \"{print_data}\"\n");

        # Determine how many slices we are to send
        bytes_len = len(in_data);
        slice_num = math.ceil(bytes_len / RECV_BUFFER_SIZE);

        # Initialize timeout counter outside of while loop
        timeout_counter = 0;

        # Send number of slices and data slices (refer to Notes 2.2 and 3 for more info)
        i = 0;
        while i < slice_num + 1:

            # For first iteration (when i = 0), send slice number
            if i == 0:

                # Configure data to send and ack msg to expect to receive
                send_data = b'SLICE ' + bytes(str(slice_num), 'utf-8')
                ack_msg = b'ACK NUM';

            # For all other iterations, send the slices
            else:

                # Subtract 1 from i in order to conveniently extract slices from in_data
                slice_i = i - 1;

                # Check if sending last slice
                if slice_i == slice_num - 1:

                    start_ind = slice_i * 1028;
                    send_data = in_data[start_ind:];

                # Otherwise, compute start and end indices for data slices
                else:

                    start_ind = slice_i * 1028;
                    end_ind = (slice_i + 1) * 1028;
                    send_data = in_data[start_ind: end_ind]

                # Configure ack message expect to receive for given slice
                ack_msg = b'ACK ' + bytes(str(slice_i), 'utf-8');

            # Print this for debugging:
            send_data_window = send_data.decode();
            if len(send_data_window) > 13:
                send_data_window = send_data_window[:13] + "...";

            # Sending data through unreliable network
            print(f"{self.device_type} STATUS: Sending data [{send_data_window}], expecting ack of {ack_msg.decode()}")
            self.__send_with_errors(send_data, recv_addr, in_socket);

            # RECV ACK: with max timeout count. If no response received before timeout, send the data
            # for this iteration again. If no ack received after sending last slice (ie. last
            # ack may have been dropped), stop function since would cause a reset connection error.
            recv_ack = None;
            try:
                recv_ack = in_socket.recv(RECV_BUFFER_SIZE);
            except socket.timeout:

                # Increment total timeouts here. If surpassed max, terminate function
                timeout_counter += 1;
                if timeout_counter == MAX_TIMEOUTS:
                    print(f"{self.device_type} ERROR: Reached max timeouts of {MAX_TIMEOUTS}. Possible network failure,"
                          f" or last ACK reply was dropped. Terminating attempt to send data.");
                    return TIMEDOUT;

                # Print messages for debugging
                if i == 0:
                    print(f"{self.device_type} ERROR: No ACK received before timeout. Retransmitting slice number in"
                          f" attempt {timeout_counter}.")
                else:
                    print(f"{self.device_type} ERROR: No ACK received before timeout. Retransmitting slice {i - 1} in"
                          f" attempt {timeout_counter}.");
                continue;

            # Handling case where connection gets severed, usually from last ACK msg getting dropped.
            # (Strangely this happens randomly, but I'm going to account for it just in case).
            except ConnectionResetError:
                if i == slice_num:
                    print(f"{self.device_type} ERROR: A connection was detected to be forcibly closed. "
                          f"Continuing operations as usual. ");
                    break;

            # Check if the received ACK was as expected. If so, send the next message.
            if recv_ack == ack_msg:

                # Update the ack history
                self.update_ack_history(recv_ack);

                # Reset timeout counter
                timeout_counter = 0;

                # Print status
                print(f"{self.device_type} STATUS: Received {recv_ack.decode()} - replacing previous ack "
                      f"in ACK history.");

            # It is possible to receive a FIN from a previous, or currently not-terminated sender device.
            # If received, reply with a FIN ACK to terminate that conversation
            elif recv_ack == b'FIN':

                print(f"{self.device_type} STATUS: Received a 'FIN'. Sending back FIN ACK and restarting loop.");
                self.__send_with_errors(b'FIN ACK', recv_addr, in_socket);
                continue;

            # Also could receive a FIN ACK. If so, just ignore and restart loop.
            elif recv_ack == b'FIN ACK':

                print(f"{self.device_type} STATUS: Received a 'FIN'/'FIN ACK' (probably from prev convo). "
                      f"Restarting loop.");
                continue;

            # If received a duplicate of the previous ack, ignore and re-transmit current slice again.
            elif recv_ack in self.ack_history:

                # If received duplicate previous ack, retransmit current slice.
                print(f"{self.device_type} STATUS: Received DUPLICATE ack for {self.ack_history[0].decode()}."
                      f" Retransmitting slice {i - 1}.");
                continue;

            # In all other scenarios, print error message (mainly for debugging)
            else:
                print(f"{self.device_type} ERROR: Received an unexpected ack.\n"
                      f"Expected ack message {ack_msg.decode()}, received {recv_ack.decode()}. Retry iteration.");
                continue;


            # Increment i here to send next slice (or terminate loop)
            i += 1;

        # Send FIN to indicate finished sending data, wait for FIN ACK to confirm end of transmission.
        # Handle cases where we may receive a duplicate ACK from sent slices or if the connection timed out.
        print(f"{self.device_type} STATUS: Ending conversation - sending FIN.")
        self.__send_with_errors(b'FIN', recv_addr, in_socket);
        while True:
            recv_ack = self.generic_recv_with_timeouts(in_socket, MAX_TIMEOUTS, send_back = True,
                                                       send_back_msg = b'FIN', dest_addr = recv_addr);
            if recv_ack == b'FIN ACK':
                print(f"{self.device_type} STATUS: Receiver has acknowledged end of conversation.")
                self.update_ack_history(recv_ack);
                break;
            elif self.check_duplicate_sender(recv_ack):
                continue;
            elif recv_ack == TIMEDOUT:
                print(f"{self.device_type} ERROR: Timed out waiting for FIN ACK. Receiving device may have received "
                      f"data in complete. Terminating transaction from sending side.")
                return TIMEDOUT;

        # After use, ensure to flush socket (refer to notes 5)
        self.flush_socket(in_socket);

        # Print for formatting
        print("-" * 15 + " END OF SENDING LOG " + "-" * 15 + "\n");


    def recv_and_parse_udp(self, in_socket, recv_file):
        """
            Function receives data slices of max size 1028 bytes from sender, and reconstructs
            the original message accordingly.

            Accounts for unreliability of network (dropped and duplicated packets, complete network failure).

            Note: We want to resend ACKS if we get duplicate messages from the sender

        Args:
            <in_socket : socket> : A UDP socket object which the message is received from.
            <recv_file : bool > : Is true if we are receiving a file.
        Returns:
            The parsed meessage in bytes. If a timeout error occurs, returns TIMEDOUT in bytes.
            If ever a non-decodable packet is received, returns NON_DECODABLE_PACKET in bytes.
        """

        # Create dummy vars to contain all the received data and the sender's address
        parsed_data = b'';
        slice_num_data = None;
        sender_addr = None;

        # Before use, ensure to flush socket (refer to notes 5)
        self.flush_socket(in_socket);

        # ONLY FOR COMMANDS: If it's first time calling receive after
        # method's invocation, turn off timeouts (refer notes 4)
        first_time_command = False;
        if not recv_file:
            first_time_command = True;
            in_socket.settimeout(None);
            slice_num_data, sender_addr = in_socket.recvfrom(RECV_BUFFER_SIZE);
            in_socket.settimeout(self.timeout_time);

        # Print for formatting
        print("\n\n" + "-" * 15 + " RECEIVING LOG " + "-" * 15);

        # Commence while loop to handle potential FIN/FIN ACK duplicates from
        # previous UDP transaction and potential network timeouts(refer notes 6)
        timeout_counter = 0;
        while True:

            # If receiving a command, ensure we don't call another "first receive"
            if first_time_command:
                first_time_command = False;
            else:

                # Account for timeouts
                try:
                    slice_num_data, sender_addr = in_socket.recvfrom(RECV_BUFFER_SIZE);
                except socket.timeout:

                    # Increment total timeouts here.
                    timeout_counter += 1;

                    # If reached max, give up and return error code
                    if timeout_counter == MAX_TIMEOUTS:
                        print(f"{self.device_type} ERROR: Reached max timeouts of {MAX_TIMEOUTS} after receiving"
                              f"duplicate packets of previous transaction. Terminating attempt to receive data.");
                        return TIMEDOUT;

                    print( f"{self.device_type} STATUS: UDP receive socket timed out waiting for data."
                           f"  {timeout_counter} accumulated timeouts. Waiting again...");
                    continue;

            # If currently the server, save the client address in the attribute so we can reply to them.
            if self.device_type == DeviceTypes.UDPSERVER:
                self.client_addr = sender_addr;

            # -- Check if slice_num_data was a FIN or a FIN ACK from previous UDP transaction --

            # If received a FIN from prev conversation, resend FIN ACK.
            if slice_num_data == b'FIN':
                print(f"{self.device_type} STATUS: Received duplicate FIN from previous transaction. Resending response.");
                self.__send_with_errors(b'FIN ACK', sender_addr, in_socket);
                continue;

            # If was FIN ACK, ignore and restart loop
            elif slice_num_data == b'FIN ACK':
                print(f"{self.device_type} STATUS: Received duplicate FIN from previous transaction. Ignoring.");
                continue;

            # If it could have been something in the message history (who knows,
            # its UDP, the wild west. Anything could happen), handle that case too.
            elif slice_num_data in self.recv_msg_history:
                print(f"{self.device_type} STATUS: Received duplicate message {slice_num_data} from previous "
                      f"transaction. Resending response.");
                self.__send_with_errors(self.recv_msg_history[slice_num_data], sender_addr, in_socket);
                continue;

            # Otherwise, break from this loop
            else:
                break;

        # Attempt to decode data to find number of slices to receive. Handle cases  where this data received was
        # non-decodable (either because data could not conv to int, or legitimately nothing was received).
        try:
            print("Received slice_num_data is " + slice_num_data.decode());
            slice_num = int(slice_num_data.decode()[6:]);
            print(f"{self.device_type} STATUS: Expect to receive {slice_num} slices of bytes from sender. "
                  f"Acknowledging...");
        except ValueError:
            print(f"{self.device_type} VALUE ERROR: Unable to decode received slice number data [{slice_num_data}]. "
                  f"Likely due to network error. Terminating receiving transaction.");
            return NON_DECODABLE_NUM;
        except AttributeError:
            print(f"{self.device_type} ATTRIBUTE ERROR: Unable to decode received slice number data [{slice_num_data}]."
                  f" Likely due to network error. Terminating receiving function.");
            return NON_DECODABLE_NUM;

        # Otherwise, acknowledge sender slice number received, and update recv msg history
        self.__send_with_errors(b'ACK NUM', sender_addr, in_socket);
        self.recv_msg_history.clear();
        self.recv_msg_history[slice_num_data] = b'ACK NUM';


        # --- Receiving slices (refer to Notes 3 for while loop implementation) ---

        i = 0;
        while i < slice_num:

            # Receive data (account for timeout possibility)
            recv_data = self.generic_recv_with_timeouts(in_socket, MAX_TIMEOUTS);
            if recv_data == TIMEDOUT:
                return TIMEDOUT;

            # First check if received a duplicate packet of data of the previous message. If so, ignore
            if self.check_duplicate_receiver(recv_data, in_socket, sender_addr):
                continue;
            else:
                print(f"{self.device_type} STATUS: Received data for slice {i} of length {len(recv_data)}.")

            # Add received data to total parsed data
            parsed_data += recv_data;

            # Send back ack to current slice
            ack_msg = b'ACK ' + bytes(str(i), 'utf-8');
            print(f"{self.device_type} STATUS: Sending back {ack_msg} for received slice {i}.");
            self.__send_with_errors(ack_msg, sender_addr, in_socket);

            # Update the new received data slice with the received message history attribute with its sent back ACK.
            self.recv_msg_history.clear();
            self.recv_msg_history[recv_data] = ack_msg;

            # Increment i
            i += 1;

        # Print status for debugging
        print(f"{self.device_type} STATUS: Received all slices - expecting FIN from sender.");

        # Send FIN ACK after receiving FIN to acknowledge end of transmission.
        # Handle if we receive a duplicate packet from the sender, or if we encounter a timeout.
        while True:
            recv_data = self.generic_recv_with_timeouts(in_socket, MAX_TIMEOUTS);
            if self.check_duplicate_receiver(recv_data, in_socket, sender_addr):
                continue;
            elif recv_data == TIMEDOUT:
                print(f"{self.device_type} ERROR: Timed out waiting for FIN.");
                return TIMEDOUT;
            elif recv_data == b'FIN':
                print(f"{self.device_type} STATUS: Received FIN. Acknowledging with FIN ACK.")
                self.__send_with_errors(b'FIN ACK', sender_addr, in_socket);
                break;

        # Print complete received msg for debugging:
        print_data = parsed_data.decode();
        if len(print_data) > 13:
            print_data = print_data[:13] + "...";
        print(f"\nMessage received: \"{print_data}\"\n");

        # After use, ensure to flush socket (refer to notes 5)
        self.flush_socket(in_socket);

        # Print for formatting
        print("-" * 15 + " END OF RECEIVING LOG " + "-" * 15 + "\n");

        # Return the parsed data as bytes
        return parsed_data;


    def check_duplicate_receiver(self, in_recv_data, in_socket, sender_addr):
        """
        For receiver only: when method is called, checks if the received data was a duplicate looking
        in the message history. If so, sends back the corresponding response to received data, and returns True.

        Args:
            <in_recv_data : bytes> : The data received in bytes.
            <in_socket : socket> : The socket to send the corresponding response on.
            <sender_addr : tuple(ip addr, port)> : The address of the sender device to reply to.
        Returns:
            True if did receive duplicate. False otherwise.
        """

        # Checking message history if did receive duplicate
        if in_recv_data in self.recv_msg_history:

            # Print this for debugging:
            recv_data_window = in_recv_data.decode();
            if len(recv_data_window) > 13:
                recv_data_window = recv_data_window[:13] + "...";

            # If so, reply with the duplicated message's corresponding ack through unreliable network
            print(f"{self.device_type} STATUS: Received duplicate packet [{recv_data_window}] for response "
                  f"{self.recv_msg_history[in_recv_data]}. Resending response.")
            self.__send_with_errors(self.recv_msg_history[in_recv_data], sender_addr, in_socket);

            # Return true if received duplicate
            return True;

        # Otherwise, return false
        return False;


    def check_duplicate_sender(self, in_recv_ack):
        """
        For sender only: When method is called, checks if the inputted received ack is in the ack history.
        If so, simply returns true.

        Args:
            <in_recv_ack : bytes> : The ack received from the receiver device.
        Returns:
            True when received ack is in history. Otherwise, false.
        """
        if in_recv_ack in self.ack_history:
            print(f"{self.device_type} STATUS: Received DUPLICATE ack for {self.ack_history[0].decode()}."
                  f" Retransmitting data.");
            return True;
        return False;


    def update_ack_history(self, new_ack):
        """ Only for sender devices: When method is called, replaces current ack message in
        ack history with the ack message passed through args. Happens when we receive a new ack
        from the sender.

        Args:
            <new_ack : bytes> : The newly received ack message to put into the ack history. """

        # Replace the ACK msg in the ack_history with newly received ack (account for case if history was empty)
        if len(self.ack_history) == 0:
            self.ack_history.append(new_ack);
        else:
            self.ack_history[0] = new_ack;


    def generic_recv_with_timeouts(self, in_socket, timeout_count, send_back = False, send_back_msg = None,
                                   dest_addr = None):
        """ 
        When this method is called, it calls a blocking receive, and if it timeouts 
        an inputted amount, it returns a special timeout code to indicate so. 
        
        Args:
            <in_socket : socket> : The socket to receive data through.
            <timeout_count : int> : The number of times the connection is to timeout before giving up.
            <send_back : bool> : If True, will send back a certain input
            <send_back_msg : bytes> : The message to send back after timeouts to other device if send_back is true.
            <dest_addr : tuple(ip, port)> : The destination address to send back messages to if send_back is True.
        Returns:
            The received data. If timed out, returns TIMEDOUT error code. 
        """
        
        # Initialize variables
        timeout_counter = 0;
        
        while True:

            try:
                recv_data = in_socket.recv(RECV_BUFFER_SIZE);
                return recv_data;

            except socket.timeout:

                # Increment total timeouts again here. If surpassed max,
                # return special error code and stop function
                timeout_counter += 1;
                if timeout_counter == timeout_count:
                    print(f"{self.device_type} ERROR: Reached max timeouts of {timeout_count}. "
                          f"Possible network failure. Terminating attempt to receive data.");
                    return TIMEDOUT;

                print(  f"{self.device_type} STATUS: UDP receive socket timed out waiting for data."
                        f" Trying attempt {timeout_counter}.");

                # If send_back bool True, send back the inputted message (with errors)
                if send_back:
                    print(f"{self.device_type} STATUS: Sending back {send_back_msg} again.");
                    self.__send_with_errors(send_back_msg, dest_addr, in_socket);

                continue;

            # Apparently this is also a possibility of happening.
            except ConnectionResetError:

                print(f"{self.device_type} ERROR: Detected the connection forcibly being shutdown."
                      f" Possible network failure. Terminating attempt to receive data.");
                return TIMEDOUT;


    def __send_with_errors(self, msg, addr, in_socket):
        """
        This method randomly drops or duplicates a message transmission. The probability of an error is the sum of
        error probabilities.

        I've added a few more print comments for debugging.

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
            print(f"{self.device_type} SENDING STATUS: Sent data was DROPPED.")
            return
        elif selected_error == "repeat":
            print(f"{self.device_type} SENDING STATUS: Sent data was DUPLICATED.")
            in_socket.sendto(msg, addr)
            in_socket.sendto(msg, addr)
        else:
            print(f"{self.device_type} SENDING STATUS: Sent data was sent NORMALLY.")
            in_socket.sendto(msg, addr)
