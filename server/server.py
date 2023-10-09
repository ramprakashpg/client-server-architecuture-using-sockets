import os
import secrets
import shutil
import socket
import time
from pathlib import Path
from threading import Thread

eof_token = ""


class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None

    def start(self):
        """
        1) Create server, bind and start listening.
        2) Accept clinet connections and serve the requested commands.

        Note: Use ClientThread for each client connection.
        """
        # Create a socket
        # Bind the socket to the specified address and port

        # Listen for incoming connections
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"Server listening on {self.host}:{self.port}")
            while True:
                conn, client_address = s.accept()
                print(f"Accepted connection from {client_address}")
                conn.sendall(self.generate_random_eof_token().encode())
                client_socket = ClientThread(self, conn, client_address, eof_token)
                client_socket.start()
                # Handle the client requests using ClientThread

            # raise NotImplementedError("Your implementation here.")

            # while True:
            # Accept incoming connections
            # send random eof token

    def get_working_directory_info(self, working_directory):
        """
        Creates a string representation of a working directory and its contents.
        :param working_directory: path to the directory
        :return: string of the directory and its contents.
        """
        dirs = "\n-- " + "\n-- ".join(
            [i.name for i in Path(working_directory).iterdir() if i.is_dir()]
        )
        files = "\n-- " + "\n-- ".join(
            [i.name for i in Path(working_directory).iterdir() if i.is_file()]
        )
        dir_info = f"Current Directory: {working_directory}:\n|{dirs}{files}"
        return dir_info

    def generate_random_eof_token(self):
        """Helper method to generates a random token that starts with '<' and ends with '>'.
        The total length of the token (including '<' and '>') should be 10.
        Examples: '<1f56xc5d>', '<KfOVnVMV>'
        return: the generated token.
        """
        charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^"
        global eof_token
        eof_token = '<' + ''.join(secrets.choice(charset) for _ in range(8)) + '>'
        return eof_token

    def receive_message_ending_with_token(self, active_socket, buffer_size, eof_token):
        """
        Same implementation as in receive_message_ending_with_token() in client.py
        A helper method to receives a bytearray message of arbitrary size sent on the socket.
        This method returns the message WITHOUT the eof_token at the end of the last packet.
        :param active_socket: a socket object that is connected to the server
        :param buffer_size: the buffer size of each recv() call
        :param eof_token: a token that denotes the end of the message.
        :return: a bytearray message with the eof_token stripped from the end.
        """
        data = active_socket.recv(buffer_size)
        return data.decode('utf-8').strip().split(eof_token)[0].strip().encode("utf-8")

    def handle_cd(self, current_working_directory, new_working_directory):
        """
        Handles the client cd commands. Reads the client command and changes the current_working_directory variable
        accordingly. Returns the absolute path of the new current working directory.
        :param current_working_directory: string of current working directory
        :param new_working_directory: name of the sub directory or '..' for parent
        :return: absolute path of new current working directory
        """
        if new_working_directory == "..":
            new_working_directory = os.path.join(current_working_directory, os.path.pardir)
        os.chdir(new_working_directory)
        curr_working_dir = os.getcwd()
        return curr_working_dir

    def handle_mkdir(self, current_working_directory, directory_name):
        """
        Handles the client mkdir commands. Creates a new sub directory with the given name in the current working directory.
        :param current_working_directory: string of current working directory
        :param directory_name: name of new sub directory
        """
        path = os.path.join(current_working_directory, directory_name)
        os.mkdir(path)
        curr_working_dir = os.getcwd()
        return curr_working_dir

    def handle_rm(self, current_working_directory, object_name):
        """
        Handles the client rm commands. Removes the given file or sub directory. Uses the appropriate removal method
        based on the object type (directory/file).
        :param current_working_directory: string of current working directory
        :param object_name: name of sub directory or file to remove
        """
        file_name = current_working_directory + "\\" + object_name
        if os.path.isfile(file_name):
            os.remove(file_name)
        elif os.path.isdir(file_name):
            shutil.rmtree(file_name)
        else:
            print("File not found..!")

    def handle_ul(
            self, current_working_directory, file_name, service_socket, eof_token
    ):
        """
        Handles the client ul commands. First, it reads the payload, i.e. file content from the client, then creates the
        file in the current working directory.
        Use the helper method: receive_message_ending_with_token() to receive the message from the client.
        :param current_working_directory: string of current working directory
        :param file_name: name of the file to be created.
        :param service_socket: active socket with the client to read the payload/contents from.
        :param eof_token: a token to indicate the end of the message.
        """
        file_data = service_socket.recv(409600)
        curr = os.path.join(current_working_directory, file_name)
        with open(curr, "wb") as file:
            file.write(file_data)
        return os.getcwd()
    def handle_dl(
            self, current_working_directory, file_name, service_socket, eof_token
    ):
        """
        Handles the client dl commands. First, it loads the given file as binary, then sends it to the client via the
        given socket.
        :param current_working_directory: string of current working directory
        :param file_name: name of the file to be sent to client
        :param service_socket: active service socket with the client
        :param eof_token: a token to indicate the end of the message.
        """
        file = open(os.path.join(current_working_directory, file_name), 'rb')
        service_socket.sendall(file.read())

    def handle_info(self, current_working_directory, file_name):
        """
        Handles the client info commands. Reads the size of a given file.
        :param current_working_directory: string of current working directory
        :param file_name: name of sub directory or file to remove
        """
        path = os.path.join(current_working_directory, file_name)
        file_stats = os.stat(path)

        return os.getcwd(), file_stats.st_size

    def handle_mv(self, current_working_directory, file_name, destination_name):
        """
        Handles the client mv commands. First, it looks for the file in the current directory, then it moves or renames
        to the destination file depending on the nature of the request.
        :param current_working_directory: string of current working directory
        :param file_name: name of the file tp be moved / renamed
        :param destination_name: destination directory or new filename
        """
        source_path = os.path.join(current_working_directory, file_name)
        destination_path = os.path.join(current_working_directory + "\\" + destination_name + "\\", file_name)
        if os.path.isdir(destination_name) and os.path.isdir(source_path):
            os.rename(source_path, destination_path)
        elif os.path.isfile(file_name):
            destination_path = os.path.join(current_working_directory, destination_name)
            os.rename(source_path, destination_path)
        return os.getcwd()

class ClientThread(Thread):
    def __init__(self, server: Server, service_socket: socket.socket, address: str, eof_token: str):
        Thread.__init__(self)
        self.server_obj = server
        self.service_socket = service_socket
        self.address = address
        self.eof_token = eof_token

    def run(self):
        print("Connection from : ", self.address)
        curr_working_dir = os.getcwd()
        formatted_working_dir = self.server_obj.get_working_directory_info(curr_working_dir)
        self.service_socket.sendall(str.encode(formatted_working_dir))
        while True:
            client_command = self.server_obj.receive_message_ending_with_token(self.service_socket, 1024, eof_token)
            print("Command: ", client_command)
            if client_command.decode() == "exit":
                break
            elif "cd" in client_command.decode():
                new_working_dir = client_command.decode().split("cd")[1].strip()
                curr_working_dir = self.server_obj.handle_cd(curr_working_dir, new_working_dir)
            elif "mkdir" in client_command.decode():
                new_working_dir = client_command.decode().split("mkdir")[1].strip()
                curr_working_dir = self.server_obj.handle_mkdir(curr_working_dir, new_working_dir)
            elif "rm" in client_command.decode():
                object_name = client_command.decode().split("rm")[1].strip()
                self.server_obj.handle_rm(curr_working_dir, object_name)
            elif "mv" in client_command.decode():
                arguments = client_command.decode().split("mv")[1].split(" ")
                curr_working_dir = self.server_obj.handle_mv(curr_working_dir, arguments[1], arguments[2])
            elif "info" in client_command.decode():
                arguments = client_command.decode().split("info")[1].strip()
                curr_working_dir, file_size = self.server_obj.handle_info(curr_working_dir, arguments)
                self.service_socket.sendall(str.encode(str(file_size)))
            elif "dl" in client_command.decode():
                arguments = client_command.decode().split("dl")[1].strip()
                self.server_obj.handle_dl(curr_working_dir, arguments, self.service_socket, eof_token)
            elif "ul" in client_command.decode():
                arguments = client_command.decode().split("ul")[1].strip()
                curr_working_dir = self.server_obj.handle_ul(curr_working_dir, arguments, self.service_socket, eof_token)

            time.sleep(1)
            formatted_working_dir = self.server_obj.get_working_directory_info(os.getcwd())
            self.service_socket.sendall(str.encode(formatted_working_dir) + eof_token.encode())
        # establish working directory

        # send the current dir info

        # while True:
        # get the command and arguments and call the corresponding method

        # sleep for 1 second

        # send current dir info

        print('Connection closed from:', self.address)
        self.service_socket.close()


def run_server():
    HOST = "127.0.0.1"
    PORT = 65432

    server = Server(HOST, PORT)
    server.start()


if __name__ == "__main__":
    run_server()
