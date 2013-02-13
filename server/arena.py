'''
File: arena.py
Author: Damien Riquet <d.riquet@gmail.com>
Description: The map is defined in this class.
             As well, there is some functions related to the map
'''

# imports
import re
import random
from math import sqrt


from enum import automatic_enum, enum
from entity import EntityManager, Entity

# enums
Direction = enum(NORTH='N', EAST='E', SOUTH='S', WEST='W')
Surface = automatic_enum('WATER', 'GROUND')

class MapException(Exception):
    pass


class Cell:
    def __init__(self, surface=Surface.GROUND):
        self.surface = surface

class Arena:
    def __init__(self, filename, config):
        self.filename = filename
        self.entities = None
        self.read_map(config)

    def read_map(self, config):
        try:
            with open(self.filename) as f:
                lines = f.readlines()
                related_data = ''.join(lines[0:3])
                map_data = lines[3:]

                # First line: rows \d+
                # Second line: cols \d+
                # Third line: players \d+

                related_data_re = "rows\s+(\d+)\s+cols\s+(\d+)\s+players\s+(\d)"
                m = re.match(related_data_re, related_data, re.DOTALL)
                if not m:
                    raise MapException("Map file '%s' is not valid - header not correct", self.filename)


                self.rows = int(m.group(1))
                self.cols = int(m.group(2))
                self.nb_players = int(m.group(3))
                self.entities = EntityManager(self.nb_players)

                view_radius = config.getint('initial', 'view_radius')
                view_radiusf = config.getfloat('initial', 'view_radius')
                self.relative_visible_cells = []

                # Compute relative visible cells
                for row in xrange(-view_radius, view_radius + 1):
                    for col in xrange(-view_radius, view_radius + 1):
                        if row == 0 and col == 0:
                            continue
                        if sqrt(row*row + col*col) <= view_radiusf:
                            self.relative_visible_cells.append((row, col))


                self.arena = [[Cell() for i in xrange(self.cols)] for j in xrange(self.rows)]

                try:
                    for row in xrange(self.rows):
                        for col in xrange(self.cols):
                            if map_data[row][col] == '%':
                                # Water cell
                                self.arena[row][col].surface = Surface.WATER

                            elif map_data[row][col] == '+':
                                # Human on this cell
                                entity = Entity(row, col)
                                entity.create_human()
                                self.entities.add_np_entity(entity)

                            elif map_data[row][col] == '*':
                                # Cop on this cell
                                entity = Entity(row, col)
                                entity.create_cop(config.getint('initial', 'bullet_amount'))
                                self.entities.add_np_entity(entity)

                            elif map_data[row][col] == '$':
                                # Berzerk on this cell
                                entity = Entity(row, col)
                                entity.create_berzerk(config.getint('initial', 'berzerk_delay'))
                                self.entities.add_np_entity(entity)

                            elif ord(map_data[row][col]) in range(ord('1'), ord('8')):
                                # Initial zombie for a player
                                team = int(map_data[row][col])
                                entity = Entity(row, col)
                                entity.create_zombie(team, config.getint('initial', 'contagion_amount'))
                                self.entities.add_zombie(entity)

                            else:
                                # Probability to spawn a human or a cop
                                if random.random() <= 0.09:
                                    if random.random() <= 0.05:
                                        # Cop on this cell
                                        entity = Entity(row, col)
                                        entity.create_cop(config.getint('initial', 'bullet_amount'))
                                        self.entities.add_np_entity(entity)
                                    else:
                                        # Human on this cell
                                        entity = Entity(row, col)
                                        entity.create_human()
                                        self.entities.add_np_entity(entity)



                except IndexError:
                    raise MapException("Map file '%s' not valid - col/row problem", self.filename)


        except IOError:
            raise MapException("Can't open map file '%s'", self.filename)


    def get_targeted_cell(self, entity, direction):
        # Compute the targeted cell
        if direction == Direction.NORTH:
            t_row, t_col = entity._row - 1, entity._col
        elif direction == Direction.SOUTH:
            t_row, t_col = entity._row + 1, entity._col
        elif direction == Direction.EAST:
            t_row, t_col = entity._row, entity._col + 1
        elif direction == Direction.WEST:
            t_row, t_col = entity._row, entity._col - 1

        return t_row, t_col


    def is_valid_move(self, entity, direction):
        """ Return whether or not the move is valid for this entity """
        t_row, t_col = self.get_targeted_cell(entity, direction)

        # Valid move = target inside the map and the cell is not water
        if t_row < 0 or t_row >= self.rows or \
           t_col < 0 or t_col >= self.cols or \
           self.arena[t_row][t_col].surface == Surface.WATER:
            return False
        return True

    def get_opposite_dirs(self, entity, avoid):
        """ Return directions that get away entity from avoid entity """
        possible_dir = ['N', 'S', 'W', 'E']
        ret = []

        for dir in possible_dir:
            target = self.get_targeted_cell(entity, dir)
            if entity.distance_to(avoid) < avoid.distance_to_location(*target):
                ret.append(dir)

        return ret

    def get_towards_dirs(self, entity, avoid):
        possible_dir = ['N', 'S', 'W', 'E']
        ret = []

        for dir in possible_dir:
            target = self.get_targeted_cell(entity, dir)
            if entity.distance_to(avoid) < avoid.distance_to_location(*target):
                ret.append(dir)

        return ret

