'''
File: enum.py
Author: Damien Riquet <d.riquet@gmail.com>
Description: Enums don't exist in Python.
             This file let the user define enums.
Source: http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python
Usage:
    >>> Numbers = automatic_enum('ZERO', 'ONE', 'TWO')
    >>> Numbers.ZERO
    0
    >>> Numbers.ONE
    1
'''

def enum(**enums):
    return type('Enum', (), enums)

def automatic_enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)
