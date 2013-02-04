'''
File: server.py
Author: Damien Riquet <d.riquet@gmail.c>
Description: This file launches the server and manages arguments
'''

import argparse

import config
import arena
import game
import time


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Outbreak server.')
    parser.add_argument('--config', '-c', help='configuration file', default='conf/default.py')
    parser.add_argument('--arena', '-a', help='map used for this game', default='maps/map_2p_01.map')
    parser.add_argument('--trace', '-t', help='name of the trace file', default='trace_%s.data' % (time.strftime("%d-%m-%H-%M-%S")))

    args = parser.parse_args()

    c = config.load_config(args.config)
    m = arena.Arena(args.arena, c)
    g = game.OutbreakGame(m, c, args.trace)

    host = c.get('server', 'host') if c.has_option('server', 'host') else 'localhost'
    port = c.getint('server', 'port') if c.has_option('server', 'host') else 8080

    g.do_game(host, port)
