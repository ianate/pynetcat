# python 3.4
import sys
import socket
import getopt
import threading
import subprocess

listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0
byte_encoding_set = 'gbk'


def usage():
    print('####pynetcat v0.1####')
    # print('')
    print('Usage: pynetcat.py -t target_host -p port')
    print('')
    print('-l --listen             - listen on [HOST]:[PORT] for incoming connections')
    print('-e --execute=FILE       - execute the given file upon receiving a connection')
    print('-c --command            - initialize a command shell')
    print('-u --upload=DESTINATION - upon receiving connection upload a file and write'
          '                               to [DESTINATION]')


def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((target, port))
        if len(buffer):
            buffer = bytes(buffer, encoding=byte_encoding_set)

            while True:

                recv_len = 1
                response = b''

                while recv_len:
                    data = client.recv(4096)
                    recv_len = len(data)
                    response += data

                    if recv_len < 4096:
                        break
                print(str(response, encoding=byte_encoding_set), )
                buffer = input()
                buffer += '\n'

                client.send(bytes(buffer, encoding=byte_encoding_set))
    except:
        print('[*]Exit for exception or command.')
        client.close()


def server_loop():
    global target

    if not len(target):
        target = '0.0.0.0'
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))

    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()


def run_command(command):
    command = command.rstrip()
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = 'Failed to execute command.\n'

    return output


def client_handler(client_socket):
    global upload
    global execute
    global command

    if len(upload_destination):
        file_buffer = b''
        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            file_buffer += data

        try:
            file_descriptor = open(upload_destination, 'wb')
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            client_socket.send(b'Success save file to %s\r\n' % upload_destination)
        except:
            client_socket.send(b'Failed to save file to %s\r\n' % upload_destination)

    if len(execute):
        output = run_command(execute)
        client_socket.send(output)

    if command:
        while True:
            client_socket.send(b'<BHP:#>')

            cmd_buffer = b''
            while b'\n' not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)
                response = run_command(str(cmd_buffer, encoding=byte_encoding_set))
                client_socket.send(response)


def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:",
                                   ['help', 'listen', 'execute',
                                    'target', 'port', 'command', 'upload'])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for o, a in opts:
        if o in ('-h', '-help'):
            usage()
            break
        elif o in ('-l', '--listen'):
            listen = True
        elif o in ('-e', '--execute'):
            execute = a
        elif o in ('-c', '--command'):
            command = True
        elif o in ('-u', '--upload'):
            upload_destination = a
        elif o in ('-t', '--target'):
            target = a
        elif o in ('-p', '--port'):
            port = int(a)
        else:
            assert False, 'Unhandled Option'
            usage()

    if not listen and len(target) and port > 0:
        buffer = sys.stdin.read()
        client_sender(buffer)

    if listen:
        server_loop()


if __name__ == '__main__':
    print(sys.version)
    if sys.version_info < (3, 2):
        raise Exception("The tool requires Python 3.2 or later version.")
    main()
