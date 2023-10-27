
from enum import Enum;

import os
import sys
from EEE466Baseline.TCPFileTransfer import TCPFileTransfer as CommunicationInterface

# DO NOT import socket

""" 
    Notes:
    
        1. Ensuring we get proper input from the user is pretty simple. If the number of elements that we parse
        is more than 2 (meaning we get something more than "command,file_name"), then obviously that is bad input.
        Furthermore, once the command is parsed, first we check the command portion if it s valid command. Then 
        we check the file_name if it is a valid file path (using os.path.exists()). If any of these are violated,
        then we stop processing the given command and continue execution according to the lab instructions.
        
        2. We'll be allowing white spaces in between the command elements. This means that "command,file_name" is valid,
        in addition to "  command   ,   file_name ". 
        
        3. Side note: I'm getting a lot of "pycharm suggests you turn a class method that doesn't use <self> in the
        method body into static" suggestions. We could, however I'm choosing not to in order to not introduce
        another factor of static class methods into the code. It wouldn't exactly hurt having these methods in
        question still remain as class methods. 
        
        4. Just decided that we're adding a few more enumerated server states: PUT_COMM and GET_COMM. I decided
        that to make the program flow linear, we're not going to call the sending file and receiving file commands
        in the decode_and_execute() function (in fact, we're renaming that to simply decode). The function will
        simply return the server state the client is requesting. If the client wants to put a file on the server, 
        the function returns PUT_COMM. If the client wants to get a file, the function returns GET_COMM. Remember,
        at this point all the bad input errors are handled as well. Also, adding a NO_FILE state that is returned
        when the client sends a put or get request, but no "file name element" was put in the command as well. 
        
        5. Adding one more thing. It's going to be a design choice where if the client sends more than one element when
        the server receives a "quit" command, then it will also throw an invalid quit error. This gets handled just
        like the rest of the bad input errors. 
        
        6. Just so it wasn't clear in the code flow, the server sends an acknowledgement to the user whenever it 
        it receives a valid command, letting the user know that it processed it all good and well. 

"""

# Making an enum class that tracks errors
class ServerState(Enum):
    UNRECOG_COMM = 0;
    NONEXIST_FILE = 1;
    PUT_COMM = 2;
    GET_COMM = 3;
    NO_FILE = 4;
    INVALID_QUIT = 5;
    QUIT_COMM = 6;


class FTServer(object):
    """
    This class creates a server object to send and receive files with a client. It can use different interfaces that
    allow for commands and files to be sent using different transport protocols.
    """

    def __init__(self):
        self.comm_inf = CommunicationInterface()

        # Hard code server port
        self.server_source_port = 9000;

    def run(self):
        """

        Upon initialization, wait to receive a connection from a client.
        Once received, executes main while loop.

        Contains main while loop of server:
            1. Waits to receive a command from user.
            2. Receives and decodes command, checking for bad input errors
            3. Notifies the client if sent command was acknowledged, or an error occurred.
            4. Server executes according to the received client command. If an error was sent,
                restarts main loop and waits for another response.

        :return: The program exit code.
        """

        # Upon initialization, open port 9000 on server and wait for connection from client.
        self.comm_inf.initialize_server(self.server_source_port);
        self.comm_inf.establish_server_connection();

        # Server main loop:
        while True:

            # Wait to receive a command from the client
            print("\nSERVER: Waiting to receive command from client... ", end = "");
            client_command = self.comm_inf.receive_command();
            print(f" command received: [{client_command}]");

            # Parse command into an array of strings.
            parsed_command = self.parse_command(client_command);

            # Check if parsed_command is empty - if so, means that
            # client sent too many arguments. Re-prompt client.
            if len(parsed_command) == 0:

                # Send to client here a reply notifying error and to retry.
                print(f"SERVER SIDE ERROR: Too many arguments received. Try again.")
                self.comm_inf.send_command("TOO MANY ARGS");
                continue;

            # Decode the array and handle decoding errors accordingly (refer Notes 1, 4, 5, 6).
            # If error, notify client and restart main server loop.
            server_state = self.decode(parsed_command);

            # If the client had sent a "get" request...
            if server_state == ServerState.GET_COMM:
                file_name = parsed_command[1];
                self.execute_get(file_name);

            # If the client had sent a "put" request...
            elif server_state == ServerState.PUT_COMM:
                file_name = parsed_command[1];
                self.execute_put(file_name);

            # If the client had sent a "quit" request...
            elif server_state == ServerState.QUIT_COMM:
                self.execute_quit();
                break;

            # If nothing else matches, means an error occurred.
            else:
                self.handle_server_error(server_state);


    def execute_get(self, in_file_name):
        """ This function was created to make the main loop code cleaner.
        This function is responsible for the facilitation of the "get" command requested by the client.
        The end result is the server sending the client requested file.

        Args:
            <in_file_name : String> : This is the name of the requested file in the server's database.
        """

        # Notify the client that server acknowledged get request
        self.comm_inf.send_command("GET ACK");

        # Once get request acknowledged by client, send the file
        self.comm_inf.send_file("Server\\Send\\" + in_file_name);


    def execute_put(self, in_file_name):
        """ This function was created to make the main loop code cleaner.
        This function is responsible for the facilitation of the "put" command requested by the client.
        The end result is the server receiving a file from the client and placing it in the server database.

        Args:
            <in_file_name : String> : The name of the file to be received from the client.
        """

        # First, send acknowledgement
        self.comm_inf.send_command("PUT ACK");

        # Next, wait for client response as they check if the given file exists in their database.
        client_response = self.comm_inf.receive_command();

        # If the client does have the file...
        if client_response == "ACK":

            # Create var for the file path destination
            server_file_path = "Server\\Receive\\" + in_file_name;

            # Receive the file
            self.comm_inf.receive_file(server_file_path);

            # Verify if the file is now in the server database since pycharm doesn't auto update
            if os.path.exists(server_file_path):
                print("SERVER STATUS: file sent by client fully received in server database.");
            else:
                print("SERVER SIDE ERROR: File sent by client failed to be placed in server database.");

        # If the client did not have the file... throw error
        elif client_response == "ERROR":
            print("SERVER SIDE ERROR: The file to receive from client does not exist in client database. "
                  "Try again.");


    def execute_quit(self):
        """ This function as created to make the main loop code cleaner.
        Function simply prints status message, acknowledges client quit request, and closes connection. """

        print("SERVER STATUS: Received quit request. Terminating server execution...")
        self.comm_inf.send_command("QUIT ACK");
        self.comm_inf.close_connection();


    def handle_server_error(self, server_error_state):
        """ Function was created to make the main loop code appear cleaner, due to the similar behaviour of these cases.
        Depending on the error, function prints out the appropriate error msg on the server side, then notifies the
        client of the error with the applicable "error response".

        "UNRECOG COMM"  --> client sent an unrecognizable command to server.
        "NONEXIST FILE" --> client has requested from the server a non-existent file in the latter's database.
        "NO FILE" --> client had sent a put/get request, but without specifying a file name.
        "QUIT INVALID" --> client had sent the server arguments with the quit command. Server refused.

        Args:
            <server_error_state : ServerState> : The state the server is in that reflects the error that had occurred.
        """

        if server_error_state == ServerState.NO_FILE:
            print("SERVER SIDE ERROR: The command was sent without a file to transfer. Try again.");
            self.comm_inf.send_command("NO FILE");

        elif server_error_state == ServerState.UNRECOG_COMM:
            print("SERVER SIDE ERROR: The inputted command is unrecognized. Try again.");
            self.comm_inf.send_command("UNRECOG COMM");

        elif server_error_state == ServerState.NONEXIST_FILE:
            print("SERVER SIDE ERROR: The inputted file does not exist in the "
                  "server's database. Try again.");
            self.comm_inf.send_command("NONEXIST FILE");

        elif server_error_state == ServerState.INVALID_QUIT:
            print("SERVER SIDE ERROR: The quit command was sent with extra arguments. Try again.");
            self.comm_inf.send_command("QUIT INVALID");


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


    def decode(self, parsed_command):
        """ Function receives an array that contains the parsed client's command.
        Depending on what was inputted, decodes and returns the "server state" to tell the server what to do next.

        If parsed_command was something unrecognized (command unrecognized or file_path doesn't exist), return the error

        Args:
            <parsed_command : [string]> : An array of strings of the parsed command that satisfies the conditions.
            Returns:
                Returns enum value UNRECOG_COMM when command unrecognized.
                Returns enum value NONEXIST_PATH when the file path does not exist.
                Returns enum value NO_PATH when it decodes a "get/put" command, but no file path element was included.
                Returns enum value INVALID_QUIT when it decodes a "quit" command, but there are extra arguments added.
                Returns enum value QUIT_COMM when it decodes a "quit" command from the client.
                Returns enum value GET_COMM when it decodes a "get" command from the client.
                Returns enum value PUT_COMM when it decodes a "put" command from the client.
        """

        # Unpack the command portion (path element parsed_command[1] may not exist if 'quit' command sent)
        this_command = parsed_command[0];

        # Making array of valid commands here
        command_list = ['put', 'get', 'quit'];

        # First check if command is valid - return appropriate server status if so
        if this_command not in command_list:
            return ServerState.UNRECOG_COMM;

        # Check if command was quit and ensure is valid if so (refer to Notes 5)
        if this_command == 'quit':
            if len(parsed_command) > 1:
                return ServerState.INVALID_QUIT;
            else:
                return ServerState.QUIT_COMM;

        # For non-quit commands, first check if a file name element was included in command (or was empty)
        if len(parsed_command) == 1 or parsed_command[1] == "":
            return ServerState.NO_FILE;

        # Here, return the appropriate server state depending on command (refer to Notes 4, 5)
        if this_command == 'put':
            return ServerState.PUT_COMM;
        elif this_command == 'get':

            # Check if the requested file. If client sent get request,
            # check if server has the file in Server\Send\
            parsed_path = parsed_command[1].split('\\');
            file_name = parsed_path[-1];
            if not os.path.exists("Server\\Send\\" + file_name):
                return ServerState.NONEXIST_FILE;

            return ServerState.GET_COMM;


if __name__ == "__main__":
    # Your program must be able to be run from the command line/IDE (using the line below).
    sys.exit(FTServer().run())
