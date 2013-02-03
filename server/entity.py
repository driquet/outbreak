'''
File: entity.py
Author: Damien Riquet <d.riquet@gmail.com>
Description: This file contains Entity class that represents any character (playable or not) of the game
'''

# imports
from math import sqrt
from enum import automatic_enum, enum

# enums
Genre = automatic_enum('HUMAN', 'COP', 'ZOMBIE', 'BERZERK')

class EntityManager:
    def __init__(self, nb_players):
        self._entities = {} 
        
        # Create containers for entities
        self._entities['all'] = []
        self._entities['humans'] = []
        self._entities['zombies'] = []
        self._entities['cops'] = []
        self._entities['berzerks'] = []

        for i in xrange(1, nb_players + 1):
            self._entities[i] = {}
            self._entities[i]['id'] = 1
            self._entities[i]['zombies'] = []

    def get_all(self):
        return list(set(self._entities['all']))

    def get_humans(self):
        return self._entities['humans']

    def get_zombies(self):
        return self._entities['zombies']

    def get_cops(self):
        return self._entities['cops']

    def get_berzerks(self):
        return self._entities['berzerks']
    
    def get_player_zombies(self, player):
        return self._entities[player]['zombies']

    def add_np_entity(self, entity):
        """ Add a non playable entity """
        if entity._type == Genre.HUMAN:
            self._entities['humans'].append(entity)

        elif entity._type == Genre.COP:
            self._entities['cops'].append(entity)

        elif entity._type == Genre.BERZERK:
            self._entities['berzerks'].append(entity)

        if entity not in self._entities['all']:
            self._entities['all'].append(entity)

    def add_zombie(self, entity):
        """ Add a playable entity """
        if entity not in self._entities['all']:
            self._entities['all'].append(entity)
        self._entities['zombies'].append(entity)
        self._entities[entity._team]['zombies'].append(entity)
        entity.set_id(self._entities[entity._team]['id'])
        self._entities[entity._team]['id'] += 1



    def contaminate_human(self, zombie, entity, contagion):
        """ A zombie contaminate an entity (a human) """
        zombie.remove_contagion()
        self._entities['humans'].remove(entity) # First, remove from humans list 
        entity.create_zombie(zombie._team, contagion) # Create the zombie
        self.add_zombie(entity) # Add the zombie to correct lists
            

    def create_berzerk(self, entity, berzerk_delay):
        self._entities['humans'].remove(entity) # Remove the human from the list
        self._entities['berzerks'].append(entity)
        entity.create_berzerk(berzerk_delay) # Create the berzerk


    def make_human_from_cop(self, entity):
        entity.create_human()
        self._entities['cops'].remove(entity)
        self._entities['humans'].append(entity)


    def die(self, entity):
        if entity._type == Genre.ZOMBIE:
            print 'team %d zombie %d' % (entity._team, entity._id)
            self._entities[entity._team]['zombies'].remove(entity)
            self._entities['zombies'].remove(entity)

        elif entity._type == Genre.HUMAN:
            self._entities['humans'].remove(entity)

        elif entity._type == Genre.COP:
            self._entities['cops'].remove(entity)

        elif entity._type == Genre.BERZERK:
            self._entities['berzerks'].remove(entity)

        self._entities['all'].remove(entity)


    def get_nearest_zombies(self, entity, radius):
        ret = []
        for zombie in self._entities['zombies']:
            if entity != zombie:
                if entity.distance_to(zombie) <= radius:
                    ret.append(zombie)
        return ret

    def get_nearest_ennemy_zombies(self, entity, radius):
        ret = []
        for zombie in self._entities['zombies']:
            if entity != zombie:
                if entity._team != zombie._team and entity.distance_to(zombie) <= radius:
                    ret.append(zombie)
        return ret


    def get_nearest_entities(self, entity, radius):
        ret = []
        for elt in self._entities['all']:
            if entity != elt:
                if entity.distance_to(elt) <= radius:
                    ret.append(elt)
        return ret

    def get_nearest_ennemy_entities(self, entity, radius):
        ret = []
        for elt in self._entities['all']:
            if entity != elt:
                if entity._team != elt._team and entity.distance_to(elt) <= radius:
                    ret.append(elt)
        return ret


class Entity:
    def __init__(self, row, col, entity_type=Genre.HUMAN):
        self._type = entity_type
        self._id = 0
        self._team = 0
        self._row, self._col = row, col
        self._contagion = 0 # Number of contagions left
        self._bullet = 0 # Number of bullets left
        self._berzerk = 0 # Number of turns left

    
    def create_human(self):
        """ Transform the current entity to an human """
        self._type = Genre.HUMAN
        self._team = 0


    def create_cop(self, bullets):
        """ Transform the current entity to a cop """
        self._type = Genre.COP
        self._team = 0
        self._bullet = bullets

    
    def create_zombie(self, team, contagion):
        """ Transform the current entity to a zombie """
        self._type = Genre.ZOMBIE
        self._team = team
        self._contagion = contagion


    def create_berzerk(self, berzerk_delay):
        """ Transform the current entity to a berzerk """
        self._type = Genre.BERZERK
        self._team = 0
        self._berzerk = berzerk_delay


    def get_contagion(self):
        return self._contagion

    def remove_contagion(self):
        self._contagion -= 1


    def has_bullet(self):
        return self._bullet > 0


    def remove_bullet(self):
        self._bullet -= 1


    def explode_berzerk(self):
        """ if _berzerk == 0, return True, otherwise False and decrement _berzerk """
        if self._berzerk == 0:
            return True
        else:
            self._berzerk -= 1
            return False


    def set_id(self, id):
        self._id = id


    def move_to(self, row, col):
        self._row, self._col = row, col

    
    def distance_to(self, other):
        """ Compute the euclidian distance between two entities """
        return float(sqrt(pow(self._row - other._row, 2) + pow(self._col - other._col, 2)))

    def __repr__(self):
        return '(team %d - id %d - pos %d:%d)' % (self._team, self._id, self._row, self._col)

    
    def get_char_repr(self):
        if self._type == Genre.ZOMBIE:
            return str(self._team)
        elif self._type == Genre.HUMAN:
            return 'h'
        elif self._type == Genre.COP:
            return 'c'
        else:
            return 'b'
