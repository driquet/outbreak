'''
File: network.py
Author: Damien Riquet <d.riquet@gmail.com>
Description: This file contains all network related functions
'''

# imports
import socket
import time
import sys

class DisconnectedPlayerException(Exception):
    pass 


def get_player_connection(host, port, timeout=2):
    """
        This function awaits a player connection
        It creates a tcp server that waits for connection establishement

        @returns the established connection

    """
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(1) 
    connection, client_address = sock.accept()

    # Set timeout option
    connection.settimeout(timeout)
    
    return connection


def get_player_message(conn):
    """
        This function receives a message from a player

    """
    data = ""

    try: 
        data = conn.recv(1024)
    except socket.timeout:
        pass

    return data


def get_player_message_sequence(conn, timing_limit):
    """
        This function receives a sequence of message
        This sequence is ended by the message 'end'

    """
    data = ""
    
    time_begin = time.clock()
    while True:
        try:
            more = conn.recv(1024)
            if more:
                data += more
                if more.startswith('end'):
                    break
            else:
                break
        except socket.timeout:
            break
    time_end = time.clock()

    if time_end - time_begin > timing_limit:
        return ''

    return data
    



def send_player_message(conn, msg):
    """
        This function sends a message to a player

    """
    conn.sendall(msg)



if __name__ == '__main__':
    c = get_player_connection(8080, 2)
    while True:
        msgs = get_player_message(c)
        print msgs
        if len(msgs) >= 1:
            for msg in msgs:
                msg += '\n'
                send_player_message(c, msg)
