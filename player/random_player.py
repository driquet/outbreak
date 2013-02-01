'''
File: player.py
Author: Damien Riquet <d.riquet@gmail.com>
Description: A basic player (with random moves) - MESSY IMPLEMENTATION - DO NOT IMPLEMENT YOUR PLAYER LIKE THIS ONE
'''

import socket
import re
import random
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Basic player with random moves.')
    parser.add_argument('--host', help='name of the server', default='localhost')
    parser.add_argument('--port', type=int, help='port of the server', default=8080)

    args = parser.parse_args()

    # Trying to connect to the server
    print 'Connection to the server (%s, %d) ...' % (args.host, args.port)
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    conn.connect((args.host, args.port))

    # Initial phase
    # 1) Sends nick
    # 2) Receives global data

    nick = 'django'
    conn.sendall('nick %s\n' % (nick))
    data = conn.recv(1024) # Answer of the server (we don't care for this player)
    print '>', data,

    data = ''
    print 'receiving initial data ...'
    while not 'end' in data:
        data = conn.recv(1024)
        print '>', data,

    finished = False
    zombies = []
    
    while not finished:
        # 1) Receives turn data
        data = ''
        print 'receiving turn data ...'

        # Receives data (at first)
        # Processing will be done later
        while 'end' not in data:
            data += conn.recv(1024)

        for l in data.strip().split('\n'):
            print '>', l

        if data.strip().startswith('end'):
            # End of the game
            finished = True
            continue
            

        for m in re.finditer(r"zombie\s+(\d+)", data):
            z_id = int(m.group(1))
            if z_id not in zombies:
                zombies.append(z_id)

        for m in re.finditer(r"contagion\s+(\d+)\s+(\d+)", data):
            z_id = int(m.group(2))
            if z_id not in zombies:
                zombies.append(z_id)

        for m in re.finditer(r"dead\s+(\d+)", data):
            z_id = int(m.group(1))
            if z_id in zombies:
                zombies.remove(z_id)


        # 2) Sends moves for zombies
        for z in zombies:
            dir_choice = random.choice(['N', 'S', 'E', 'W'])
            conn.sendall('move %d %s\n' % (z, dir_choice))
            print '< move', z, dir_choice

        conn.sendall('end\n')


    # Receives final data
    data = conn.recv(1024)
    data += conn.recv(1024)
    print data

    end_re = r"final\s+(\d)\s+(\d+)"
    m = re.search(end_re, data)
    if m:
        result = int(m.group(1))
        if result:
            print 'Winner !'
        else:
            print 'Looser :\'('

    # Finally, close the connection
    conn.close()

