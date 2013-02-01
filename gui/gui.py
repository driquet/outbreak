'''
File: gui.py
Author: Damien Riquet <d.riquet@gmail.com>
Description: This file contain the GUI of outbreak
'''

import gtk
import random
import math
import glib

SQUARE_SIZE = 4

WATER = (0.7,0.7,0.7)
HUMAN = (1,1,1)
COP = (1,1,0)
BZK = [(1,1,0), (0,1,0)]
ZOMBIES = [(1,0,0), (0,1,0), (0,0,1), (0,1,1), (1,0,1)]

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
                    cr.arc(col*SQUARE_SIZE + SQUARE_SIZE/2, row*SQUARE_SIZE + SQUARE_SIZE/2, SQUARE_SIZE/2, 0, 2*math.pi)
                    cr.fill()

                elif cell == 'c':
                    cr.set_source_rgb(*COP)
                    cr.rectangle(col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                    cr.fill()

                elif cell == 'b':
                    cr.set_source_rgb(*BZK[0])
                    cr.arc(col*SQUARE_SIZE + SQUARE_SIZE/2, row*SQUARE_SIZE + SQUARE_SIZE/2, SQUARE_SIZE/2, 0, 2*math.pi)
                    cr.fill()
                    cr.set_source_rgb(*BZK[1])
                    cr.arc(col*SQUARE_SIZE + SQUARE_SIZE/2, row*SQUARE_SIZE + SQUARE_SIZE/2, SQUARE_SIZE/2, 0, math.pi)
                    cr.fill()

                elif cell.isdigit():
                    player = int(cell)
                    cr.set_source_rgb(*ZOMBIES[player-1])
                    cr.arc(col*SQUARE_SIZE + SQUARE_SIZE/2, row*SQUARE_SIZE + SQUARE_SIZE/2, SQUARE_SIZE/2, 0, 2*math.pi)
                    cr.fill()



        

    def update_data(self, arena):
        self.arena = arena


class OutbreakGUI(gtk.Window):

    def __init__(self, trace):
        super(OutbreakGUI, self).__init__()

        # Read the file to know the number of players or the size of the window
        self.trace = open(trace, 'r')

        # First line: players
        players = self.trace.readline().split(' ')
        self.nb_players = len(players)
        self.players = {}
        
        for i in xrange(self.nb_players):
            self.players[i+1] = players[i]

        arena_data = self.trace.readline().split(' ')
        self.rows = int(arena_data[0])
        self.cols = int(arena_data[1])
            
        self.width = self.cols * SQUARE_SIZE
        self.height = self.rows * SQUARE_SIZE

        self.set_title('Outbreak')
        self.set_size_request(self.width, self.height)
        self.set_resizable(False)
        self.set_position(gtk.WIN_POS_CENTER)

        self.arena = Arena(self.rows, self.cols)
        self.add(self.arena)

        self.connect("destroy", gtk.main_quit)
        self.show_all()

        self.update_gui()

        glib.timeout_add(250, self.update_gui)


    def update_gui(self):
        # First line: turn number

        data = self.trace.readline()
        if data == "": return False

        turn_data = int(data.strip())
        print 'turn %d', turn_data

        # Second line: scores
        data = self.trace.readline()
        if data == "": return False
        scores = [int(elt) for elt in data.strip().split(' ')]

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





OutbreakGUI("trace")
gtk.main()
        
