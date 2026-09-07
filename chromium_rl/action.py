"""Complete held-button states. License: Clarified Artistic, game/COPYING."""
from enum import IntEnum


class Action(IntEnum):
    IDLE = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    UP_LEFT = 5
    UP_RIGHT = 6
    DOWN_LEFT = 7
    DOWN_RIGHT = 8
    FIRE = 9
    UP_FIRE = 10
    DOWN_FIRE = 11
    LEFT_FIRE = 12
    RIGHT_FIRE = 13
    UP_LEFT_FIRE = 14
    UP_RIGHT_FIRE = 15
    DOWN_LEFT_FIRE = 16
    DOWN_RIGHT_FIRE = 17
