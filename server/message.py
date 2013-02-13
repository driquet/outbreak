'''
File: message.py
Author: Damien Riquet <d.riquet@gmail.com>
Description: This file introduces messages.
             Messages are string-based information that are sent
             at the beginning of each turn of the game
'''

class Message(object):
    """ A message stores information about the current data of the game
        Its only purpose is to be sent to a player """
    def __init__(self):
        print self

    def __str__(self):
        """ The only method that matters : how to describe the message """
        pass

class WaterMessage(Message):
    """ A new water cell has been discovered """
    def __init__(self, row, col):
        self.row, self.col = row, col
        super(WaterMessage, self).__init__()

    def __str__(self):
        return "water %d %d" % (self.row, self.col)


class EntityMessage(Message):
    """ An entity is visible for this player """
    def __init__(self, row, col, e_type, e_team):
        self.row, self.col = row, col
        self.e_type = e_type
        self.e_team = e_team
        super(EntityMessage, self).__init__()

    def __str__(self):
        return "entity %d %d %d %d" % (self.row, self.col, self.e_type, self.e_team)


class ShotMessage(Message):
    """ A zombie cop has shot a zombie """
    def __init__(self, e_id):
        self.e_id = e_id
        super(ShotMessage, self).__init__()

    def __str__(self):
        return "shot %d" % self.e_id


class ContagionMessage(Message):
    """ A zombie has infected a human """
    def __init__(self, zombie_id, new_id, row, col, nb_bullets):
        self.zombie_id = zombie_id
        self.new_id = new_id
        self.row, self.col = row, col
        self.nb_bullets = nb_bullets
        super(ContagionMessage, self).__init__()

    def __str__(self):
        return "contagion %d %d %d %d %d" % (self.zombie_id, self.new_id, self.row, self.col, self.nb_bullets)


class ZombieMessage(Message):
    """ A zombie has moved """
    def __init__(self, e_id, row, col):
        self.e_id = e_id
        self.row, self.col = row, col
        super(ZombieMessage, self).__init__()

    def __str__(self):
        return "zombie %d %d %d" % (self.e_id, self.row, self.col)


class DeadMessage(Message):
    """ A zombie is dead - sniff """
    def __init__(self, e_id):
        self.e_id = e_id
        super(DeadMessage, self).__init__()

    def __str__(self):
        return "dead %d" % self.e_id

