import socket
from threading import Thread


class Client:
    def __init__(self, host, port):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.client_socket = None
        self.eof_token = None

    def receive_message_ending_with_token(self, active_socket, buffer_size, eof_token):
        """
        Same implementation as in receive_message_ending_with_token() in server.py
        A helper method to receives a bytearray message of arbitrary size sent on the socket.
        This method returns the message WITHOUT the eof_token at the end of the last packet.
        :param active_socket: a socket object that is connected to the server
        :param buffer_size: the buffer size of each recv() call
        :param eof_token: a token that denotes the end of the message.
        :return: a bytearray message with the eof_token stripped from the end.
        """
        data = active_socket.recv(buffer_size)
        print(data.decode())
        return data.decode('utf-8').strip().split(eof_token.decode())[0].encode("utf-8").strip()

    def initialize(self, host, port):
        """
        1) Creates a socket object and connects to the server.
        2) receives the random token (10 bytes) used to indicate end of messages.
        3) Displays the current working directory returned from the server (output of get_working_directory_info() at the server).
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param host: the ip address of the server
        :param port: the port number of the server
        :return: the created socket object
        :return: the eof_token
        """
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM):
            client_socket.connect((host, port))
            print('Connected to server at IP:', host, 'and Port:', port)
            eof_token = client_socket.recv(1024)
            print('Handshake Done. EOF is:', eof_token.decode())

            server_messages = self.receive_message_ending_with_token(client_socket, 1024, eof_token)
            return client_socket, eof_token

    def issue_cd(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full cd command entered by the user to the server. The server changes its cwd accordingly and sends back
        the new cwd info.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        """
        client_socket.sendall(command_and_arg.encode() + eof_token)
        curr_working_dir = self.receive_message_ending_with_token(client_socket, 1024, eof_token)

    def issue_mkdir(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full mkdir command entered by the user to the server. The server creates the sub directory and sends back
        the new cwd info.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        """
        client_socket.sendall(command_and_arg.encode() + eof_token)
        self.receive_message_ending_with_token(client_socket, 1024, eof_token)

    def issue_rm(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full rm command entered by the user to the server. The server removes the file or directory and sends back
        the new cwd info.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        """
        client_socket.sendall(command_and_arg.encode() + eof_token)
        self.receive_message_ending_with_token(client_socket, 1024, eof_token)

    def issue_ul(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full ul command entered by the user to the server. Then, it reads the file to be uploaded as binary
        and sends it to the server. The server creates the file on its end and sends back the new cwd info.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        """
        client_socket.sendall(command_and_arg.encode() + eof_token)
        file = open(command_and_arg.split(" ")[1].strip(), 'rb')
        client_socket.sendall(file.read())
        self.receive_message_ending_with_token(client_socket, 1024, eof_token)

    def issue_dl(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full dl command entered by the user to the server. Then, it receives the content of the file via the
        socket and re-creates the file in the local directory of the client. Finally, it receives the latest cwd info from
        the server.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        :return:
        """
        client_socket.sendall(command_and_arg.encode() + eof_token)
        file_data = client_socket.recv(409600)
        with open(command_and_arg.split(" ")[1].strip(), "wb") as file:
            file.write(file_data)
        self.receive_message_ending_with_token(client_socket, 1024, eof_token)

    def issue_info(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full info command entered by the user to the server. The server reads the file and sends back the size of
        the file.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        :return: the size of file in string
        """
        client_socket.sendall(command_and_arg.encode() + eof_token)
        file_size = client_socket.recv(1024)
        print("Size in bytes: ", file_size.decode())
        self.receive_message_ending_with_token(client_socket, 1024, eof_token)

    def issue_mv(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full mv command entered by the user to the server. The server moves the file to the specified directory and sends back
        the updated. This command can also act as renaming the file in the same directory.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        """
        client_socket.sendall(command_and_arg.encode() + eof_token)
        self.receive_message_ending_with_token(client_socket, 1024, eof_token)

    def start(self):
        """
        1) Initialization
        2) Accepts user input and issue commands until exit.
        """
        # initialize
        self.client_socket, eof_token = self.initialize(self.host, self.port)
        while True:
            command = input("Enter the command: ")
            if command == "exit":
                self.client_socket.sendall(command.encode() + eof_token)
                break
            elif "cd" in command:
                self.issue_cd(command, self.client_socket, eof_token)
            elif "mkdir" in command:
                self.issue_mkdir(command, self.client_socket, eof_token)
            elif "rm" in command:
                self.issue_rm(command, self.client_socket, eof_token)
            elif "mv" in command:
                self.issue_mv(command, self.client_socket, eof_token)
            elif "info" in command:
                self.issue_info(command, self.client_socket, eof_token)
            elif "dl" in command:
                self.issue_dl(command, self.client_socket, eof_token)
            elif "ul" in command:
                self.issue_ul(command, self.client_socket, eof_token)
        self.client_socket.close()

    # get user input

    # call the corresponding command function or exit

    print('Exiting the application.')


def run_client():
    HOST = "127.0.0.1"  # The server's hostname or IP address
    PORT = 65432  # The port used by the server

    client = Client(HOST, PORT)
    client.start()


if __name__ == '__main__':
    run_client()
