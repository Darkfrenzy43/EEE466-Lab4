class CommunicationInterface(object):
    """
    This class provides the stub methods for Client and Server communication. These methods are overriden by specific
    interfaces designed for different communication paradigms.
    """

    def __init__(self):
        """
        This method is used to initialize your Communication Interface object. Class variables are defined here.
        """
        print("TODO implement this method")

    def initialize_server(self, source_port):
        """
        Performs any necessary communication setup for the server. Creates a socket and binds it to a port. The server
        listens for all IP addresses (e.g., "0.0.0.0").

        :param source_port: port that provides a service.
        """
        print("TODO implement this method")

    def establish_server_connection(self):
        """
        Accepts incoming connections for the server socket. Not implemented for connectionless protocols.

        The active connection is used to perform send and receive function calls. There should never be more than one
        active connection. If the CommunicationInterface does not have an established connection this method should
        establish one. If there is an existing, established connection this call should close it and create a new one.

        For UDP this method does nothing.
        """
        print("TODO implement this method")

    def initialize_client(self, address, destination_port):
        """
        Performs any necessary communication setup for the server. Creates a socket and attempts to connect to the
        server.

        :param address: the address you wish to connect to. (e.g., "localhost","127.0.0.1")
        :param destination_port: the port you want the client to connect to.
        """
        print("TODO implement this method")

    def send_file(self, file_path):
        """
        Transfers a file from the local directory to the "remote" directory. Can be used by either client (i.e., in a
        put request), or by the server when receiving a get request.

        This method will need to read the file from the sender's folder and transmit it over the connection. If the
        file is larger than 1028 bytes, it will need to be broken into multiple buffer reads.

        :param file_path: the location of the file to send. E.g., ".\Client\Send\\ploadMe.txt".
        """
        print("TODO implement this method")

    def receive_file(self, file_path):
        """
        Receives a filename and data over the communication channel to be saved in the local directory. Can be used by
        the client or the server.

        This method has a maximum buffer size of 1028 bytes. Multiple reads from the channel are required for larger
        files. This method writes the data it receives to the client or server "Receive" directory. Note: the filename
        must be sent over the wire and cannot be hard-coded.

        :param file_path: this is the destination where you wish to save the file. E.g.,
        ".\Server\Receive\\ploadMe.txt".
        """
        print("TODO implement this method")

    def send_command(self, command):
        """
        Sends a command from the client to the server. At a minimum this includes GET, PUT, QUIT and their parameters.

        This method may also be used to have the server return information, i.e., ACK, ERROR. This method can be used to
        inform the client or server of the filename ahead of sending the data.

        :param command: The command you wish to send to the server.
        """
        print("TODO implement this method")

    def error(self, error_msg):
        """
        OPTIONAL error method can be used to display an error to the client or server, or can be used to send
        an error message across an open connection if something fails.

        :param error_msg: The error message you would like to display.
        """
        print("TODO implement this method")

    def receive_command(self):
        """
        This method should be called by the server to await a command from the client. It can also be used by the
        client to receive information such as an ACK or ERROR message.

        :return: the command received and any parameters.
        """
        print("TODO implement this method")

    def close_connection(self):
        """
        If an unrecoverable error occurs or a QUIT command is called the server and client and tear down the
        connection.
        """
        print("TODO implement this method")
