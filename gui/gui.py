'''
File: gui.py
Author: Damien Riquet <d.riquet@gmail.com>
Description: This file contain the GUI of outbreak
'''

import gtk
import random
import math
import glib
import argparse

SQUARE_SIZE = 4

WATER = (0.7,0.7,0.7)
HUMAN = (1,1,1)
COP = (1,1,0)
BZK = (1,0,0)
# We consider that there is at most 4 players
ZOMBIES = [(0,1,0), (0,0,1), (0,1,1), (1,0,1)]

class Arena(gtk.DrawingArea):
    
    def __init__(self, rows, cols):
        super(Arena, self).__init__()
            
        self.rows = rows
        self.cols = cols
        self.arena = []

        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(0,0,0))
        self.set_size_request(cols * SQUARE_SIZE, rows * SQUARE_SIZE)

        self.connect("expose-event", self.expose)

    def expose(self, widget, event):
        cr = widget.window.cairo_create()

        for row in xrange(self.rows):
            for col in xrange(self.cols):
                cell = self.arena[row][col]

                if cell == 'w':
                    # Water
                    cr.set_source_rgb(*WATER)
                    cr.rectangle(col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                    cr.fill()

                elif cell == 'h':
                    cr.set_source_rgb(*HUMAN)
                    cr.rectangle(col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                    cr.fill()

                elif cell == 'c':
                    cr.set_source_rgb(*COP)
                    cr.rectangle(col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                    cr.fill()

                elif cell == 'b':
                    cr.set_source_rgb(*BZK)
                    cr.rectangle(col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                    cr.fill()

                elif cell.isdigit():
                    player = int(cell)
                    cr.set_source_rgb(*ZOMBIES[player-1])
                    cr.arc(col*SQUARE_SIZE + SQUARE_SIZE/2, row*SQUARE_SIZE + SQUARE_SIZE/2, SQUARE_SIZE/2, 0, 2*math.pi)
                    cr.fill()


    def update_data(self, arena):
        self.arena = arena

class PlayerCircle(gtk.DrawingArea):

    def __init__(self, width, height, color):
        super(PlayerCircle, self).__init__()
        self.width, self.height = width, height
        self.color = color

        self.connect("expose-event", self.expose)

    def expose(self, widget, event):
        cr = widget.window.cairo_create()

        cr.set_source_rgb(*self.color)
        cr.arc(self.width / 2, self.height / 2, self.width / 2 , 0, 2*math.pi)
        cr.fill()


class OutbreakGUI(gtk.Window):

    def __init__(self, trace, timeout):
        super(OutbreakGUI, self).__init__()

        # Read the file to know the number of players or the size of the window
        self.trace = open(trace, 'r')
        self.read_initial_data()

        self.set_title('Outbreak')
        # self.set_size_request(self.width, self.height)
        self.set_resizable(False)
        self.set_position(gtk.WIN_POS_CENTER)

        # Main box ((Arena + players) + status bar)
        self.main_box = gtk.VBox(False, 0)
        self.central_box = gtk.HBox(False, 5)

        self.player_box = self.build_player_box()
        self.arena = Arena(self.rows, self.cols)
        self.statusbar = gtk.Statusbar()
        self.statusbar.set_has_resize_grip(False)

        self.central_box.pack_start(self.arena, False, False, 0)
        self.central_box.pack_start(self.player_box, False, False, 0)

        self.main_box.pack_start(self.central_box, False, False, 0)
        self.main_box.pack_start(self.statusbar, False, False, 0)

        self.add(self.main_box)

        self.connect("destroy", gtk.main_quit)
        self.show_all()

        self.update_gui()

        glib.timeout_add(timeout, self.update_gui)

    
    def read_initial_data(self):
        # First line: players
        players = self.trace.readline().strip().split(' ')
        self.nb_players = len(players)
        self.players = {}
        
        for i in xrange(self.nb_players):
            self.players[i+1] = players[i]

        arena_data = self.trace.readline().split(' ')
        self.rows = int(arena_data[0])
        self.cols = int(arena_data[1])
            
        self.width = self.cols * SQUARE_SIZE
        self.height = self.rows * SQUARE_SIZE


    def build_player_box(self):
        box = gtk.VBox(False, 5)
        self.scores = []

        for idx,name in self.players.items():
            pbox = gtk.HBox(True,0)
            pbox.set_size_request(256,-1)

            # Display circle
            circle = PlayerCircle(SQUARE_SIZE*2, SQUARE_SIZE*2, ZOMBIES[idx-1])
            circle.set_size_request(SQUARE_SIZE*2, SQUARE_SIZE*2)
            pbox.pack_start(circle, False, False, 0)

            # Label with name of the player
            p_name = gtk.Label(name)
            pbox.pack_start(p_name, False, False, 0)

            # Score
            p_score = gtk.Label('0')
            self.scores.append(p_score)
            pbox.pack_start(p_score, False, False, 0)

            box.pack_start(pbox, False, False, 5)

        return box



    def update_gui(self):
        # First line: turn number
        data = self.trace.readline()
        if data == "": return False

        turn_data = int(data.strip())
        self.statusbar.push(0, 'turn %d' % turn_data)

        # Second line: scores
        data = self.trace.readline()
        if data == "": return False
        scores = [int(elt) for elt in data.strip().split(' ')]

        for i in xrange(0, len(scores)):
            self.scores[i].set_text(str(scores[i]))

        # Read map
        arena_repr = []
        for row in xrange(self.rows):
            data = self.trace.readline()
            if data == "": return False
            arena_repr.append(data.strip())

        # Update drawing area
        self.arena.update_data(arena_repr)

        self.queue_draw()
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Outbreak GUI.')
    parser.add_argument('--trace', '-t', help='trace file - game to be viewed', required=True)
    parser.add_argument('--timeout', type=int, help='timeout between each turn', default=250)

    args = parser.parse_args()

    OutbreakGUI(args.trace, args.timeout)
    gtk.main()
        
