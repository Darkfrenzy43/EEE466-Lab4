import os
import sys
from EEE466Baseline.RUDPFileTransfer import RUDPFileTransfer as CommunicationInterface

# DO NOT import socket

"""
    Notes:

        1. Below are the possible server responses:
            "QUIT ACK" --> server acknowledges the quit command that was sent. Prep client to quit as well.
            "PUT ACK" --> server acknowledges the put command it was sent. Prep client to send file.
            "GET ACK" --> server acknowledges the get command it was sent. Prep client to receive file.
            -------------------- CLIENT SIDE ERRORS (handled in separate function) ---------------------
            "TOO MANY ARGS" --> client sent too many args to the server.
            "UNRECOG COMM"  --> client sent an unrecognizable command to server.
            "NONEXIST FILE" --> client has requested from the server a non-existent file in the latter's database.
            "NO FILE" --> client had sent a put/get request, but without specifying a file name.
            "QUIT INVALID" --> client had sent the server arguments with the quit command. Server refused.
"""


class FTClient(object):
    """
    This class creates a client object to send and receive files with a server. It can use different interfaces that
    allow for commands and files to be sent using different transport protocols.
    """

    def __init__(self):
        self.comm_inf = CommunicationInterface()

        # Hard code server address for now
        self.server_address = ('localhost', 9000);

    def run(self):
        """

        Upon initialization, connects to server.

        Once connected, executes main while loop:
            1. Waits for user input from user.
            2. Sends the user input as a command to the server.
            3. Waits for a server response (acknowledgement or a reply indicating error)
            4. If error reply received, notifies user of error.
            5. If acknowledgement received for a command, execute command accordingly.


        :return: The program exit code.
        """

        print("CLIENT STATUS: Client started. Looking for server to connect to...")

        # Upon initialization, connect client to the server
        self.comm_inf.initialize_client(self.server_address[0], self.server_address[1]);

        # Try sending a bit of data
        self.comm_inf.send_command(b'RANDOM' * 1000);

        # # Client main loop:
        # while True:
        #
        #     # Getting user input (stripped of whitespace)
        #     user_input = input("\nType in a command to send to server: \n> ");
        #
        #
        #
        #     # Send user input to server
        #     self.comm_inf.send_command(user_input);
        #
        #     # Wait for a server response, decode received msg accordingly (refer to Notes 2)
        #     server_response = self.comm_inf.receive_command();
        #     if server_response == "GET ACK":
        #
        #         # Getting the file name from command
        #         parsed_command = self.parse_command(user_input);
        #         file_name = parsed_command[1];
        #
        #         # Execute client side of command
        #         self.execute_get(file_name);
        #
        #     elif server_response == "PUT ACK":
        #
        #         # Getting the file name from command
        #         parsed_command = self.parse_command(user_input);
        #         file_name = parsed_command[1];
        #
        #         # Execute client side of command
        #         self.execute_put(file_name);
        #
        #     elif server_response == "QUIT ACK":
        #
        #         # Break main while loop.
        #         print("CLIENT STATUS: Server acknowledged quit request. Terminating client execution...");
        #         break;
        #
        #     else:
        #
        #         # If nothing else matches, means error was returned. Print error msg accordingly.
        #         self.print_client_error(server_response);


    def execute_get(self, in_file_name):
        """ Function was created to make the main loop code cleaner.
        The end state of this function is the client receiving a requested file from the server.

        Args:
            <in_file_name : String> : The name of the file being requested by the client from the server."""

        # Create the path variable for clarity
        client_file_path = "Client\\Receive\\" + in_file_name;

        # Receive the requested file and place in Client\Receive\ directory
        self.comm_inf.receive_file(client_file_path);

        # Verify here if client received the file (refer to Notes 1)
        if os.path.exists(client_file_path):
            print("CLIENT STATUS: Requested file confirmed received in client database.");
        else:
            print("CLIENT SIDE ERROR: Requested file failed to be placed in client database.");


    def execute_put(self, in_file_name):
        """ Function was created to make the main loop code cleaner.
        The end state of this function is the client sending the server a specified file.
        If the specified file does not exist in the client database, the error is handled appropriately.

        Args:
            <in_file_name : String> : The name of the file the user intends to send to the server."""

        # Create the path variable for clarity
        client_file_path = "Client\\Send\\" + in_file_name;

        # Check if the given file exists in client database.
        # If so, send ACK, then file, otherwise, send ERROR.
        if os.path.exists(client_file_path):
            print("CLIENT STATUS: File to send exists in client database. Sending...");
            self.comm_inf.send_command("ACK");
            self.comm_inf.send_file(client_file_path);
        else:
            print("CLIENT SIDE ERROR: File to send does not exist in client database. Verify file name.");
            self.comm_inf.send_command("ERROR");


    def parse_command(self, in_command):
        """ Function receives in a raw client command. Parses it, and returns
        the parsed words in an array if it does not violate conditions (2 elements or less).

        If parsed more than 2 elements, returns nothing to indicate error.

        Args:
            <in_command : string> : The raw string that contains the command sent by the client.
        """

        # Remove all whitespaces (refer to Notes 2), and parse command
        parsed_command = in_command.replace(" ", "").split(',');

        # If more than 2 elements in parsed_command, return empty list indicating error (refer to Notes 1).
        # Otherwise, return the parsed commands
        if len(parsed_command) > 2:
            return [];
        else:
            return parsed_command;

    def print_client_error(self, server_error_response):
        """ This function was just created to clean up the main loop code, due to the similar behaviour of these cases.
        The function prints out the appropriate error msg depending on the
        error the server had returned to the client.

        "TOO MANY ARGS" --> client sent too many args to the server.
        "UNRECOG COMM"  --> client sent an unrecognizable command to server.
        "NONEXIST FILE" --> client has requested from the server a non-existent file in the latter's database.
        "NO FILE" --> client had sent a put/get request, but without specifying a file name.
        "QUIT INVALID" --> client had sent the server arguments with the quit command. Server refused.

        Args:
            <server_error_response : string> : The error response that the server had replied with. """

        if server_error_response == "QUIT INVALID":

            print("CLIENT SIDE ERROR: Quit command was sent with an argument. If wish to quit, send only <quit>.");

        elif server_error_response == "TOO MANY ARGS":
            print(f"CLIENT SIDE ERROR: Last command had too many arguments. Follow format <command,file_name>.");

        elif server_error_response == "UNRECOG COMM":
            print(f"CLIENT SIDE ERROR: Last command sent unrecognized by server. Choose either <get> or <put>.");

        elif server_error_response == "NONEXIST FILE":
            print(f"CLIENT SIDE ERROR: Requested file does not exist in "
                  f"server database. Verify and try again.");

        elif server_error_response == "NO FILE":
            print("CLIENT SIDE ERROR: Last command was sent without a file. Ensure to include one.");



if __name__ == "__main__":
    # Your program must be able to be run from the command line/IDE (using the line below).
    # However, you may want to add test cases to run automatically.
    sys.exit(FTClient().run())

