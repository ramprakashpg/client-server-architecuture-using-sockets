from client.client import Client
from server.server import run_server as Server_main
import multiprocessing
import time
import shutil
import os




# exit_flag = threading.Event()

if __name__ == '__main__':

    """ Starting Server """
    server_process = multiprocessing.Process(target=Server_main)
    server_process.start()

    time.sleep(1)
    HOST = "127.0.0.1"
    PORT = 65432

    print('-'*8,'TESTING CLIENT','-'*8)

    sub_client = Client(HOST,PORT)
    sub_client_socket, eof_token = sub_client.initialize(HOST,PORT)
    command_and_arg = ['mkdir test_dir',
                       'cd test_dir',
                       'ul jellyfish.jpg',
                       'dl jellyfish.jpg',
                       'cd ..',
                       'rm test_dir'
                       ]

    """ Clear existing files """
    if os.path.exists('test_dir'):
        shutil.rmtree('test_dir')
    time.sleep(0.5)

    """ Testing mkdir """
    sub_client.issue_mkdir(command_and_arg[0], sub_client_socket,eof_token)
    time.sleep(0.5)
    assert os.path.exists(os.path.join(os.getcwd(),'test_dir')), 'mkdir failed'

    """ Testing cd """
    sub_client.issue_cd(command_and_arg[1], sub_client_socket,eof_token)
    time.sleep(0.5)


    """ Testing ul """
    sub_client.issue_ul(command_and_arg[2], sub_client_socket,eof_token)
    time.sleep(0.5)
    assert os.path.exists(os.path.join(os.getcwd(),'test_dir','jellyfish.jpg')) , 'ul failed'
    os.remove('jellyfish.jpg')
    time.sleep(0.5)

    """ Testing dl """
    sub_client.issue_dl(command_and_arg[3], sub_client_socket,eof_token)
    time.sleep(0.5)
    assert os.path.exists(os.path.join(os.getcwd(),'jellyfish.jpg')) , 'dl failed'

    """ Testing rm"""
    sub_client.issue_cd(command_and_arg[4],sub_client_socket,eof_token)
    sub_client.issue_rm(command_and_arg[5], sub_client_socket,eof_token)
    assert not os.path.exists(os.path.join(os.getcwd(),'test_dir')), 'rm failed'
    time.sleep(0.5)

    print('*'*8,' CLIENT COMPLETE ','*'*8)
    sub_client_socket.close()
    server_process.terminate()
    del sub_client,sub_client_socket

    print('Script completed gracefully!')
