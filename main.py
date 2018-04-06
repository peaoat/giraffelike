#!venv/bin/python3
# -*- coding: utf-8 -*-

import colors
import tdl
from random import randint


class Entity:
    def __init__(self, x, y, char, name, color, blocks=False):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks

    def move(self, dx, dy):
        # If the desired tile is blocked, do not move
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def draw(self):
        if (self.x, self.y) in visible_tiles:
            con.draw_char(self.x, self.y, self.char, self.color)

    def clear(self):
        con.draw_char(self.x, self.y, ' ', self.color)


class Tile:
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked
        self.explored = False

        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight


class Rect:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.x2 = x + w
        self.y1 = y
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)

    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)


def create_room(room):
    # Pass this a Rect and it will make it a walkable space
    global field
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            field[x][y].blocked = False
            field[x][y].block_sight = False


def create_h_tunnel(x1, x2, y):
    global field
    for x in range(min(x1, x2), max(x1, x2) + 1):
        field[x][y].blocked = False
        field[x][y].block_sight = False


def create_v_tunnel(y1, y2, x):
    global field
    for y in range(min(y1, y2), max(y1, y2) + 1):
        field[x][y].blocked = False
        field[x][y].block_sight = False


def handle_keys():
    global fov_recompute

    user_input = tdl.event.key_wait()

    # Quit on esc
    if user_input.key == 'ESCAPE':
        return 'exit'

    # Shift player on arrow key
    if user_input.key == 'UP':
        player_move(0, -1)
    elif user_input.key == 'DOWN':
        player_move(0, 1)
    elif user_input.key == 'LEFT':
        player_move(-1, 0)
    elif user_input.key == 'RIGHT':
        player_move(1, 0)
    else:
        return 'no-turn'


def is_blocked(x, y):
    if field[x][y].blocked:
        return True

    for obj in objects:
        if obj.blocks and obj.x == x and obj.y == y:
            return True

    return False


def is_visible_tile(x, y):
    global field

    if x >= field_width or x < 0:
        return False
    elif y >= field_height or y < 0:
        return False
    elif field[x][y].blocked == True:
        return False
    elif field[x][y].block_sight == True:
        return False
    else:
        return True


def make_field():
    global field

    # Create a 2D array of Tiles
    field = [
        [Tile(True) for y in range(field_height)] for x in range(field_width)]

    room_max = 15
    room_min = 5
    room_num = 30
    rooms = []

    for r in range(room_num):
        w = randint(room_min, room_max)
        h = randint(room_min, room_max)
        x = randint(0, field_width - w -1)
        y = randint(0, field_height - h - 1)

        this_room = Rect(x, y, w, h)
        fail = False

        for other_room in rooms:
            if this_room.intersect(other_room):
                fail = True
                break

        if not fail:
            # If this room doesn't overlap others, use it
            create_room(this_room)

            try:
                (prevx, prevy) = rooms[len(rooms) - 1].center()
            except IndexError:
                (prevx, prevy) = this_room.center()

            thisx, thisy = this_room.center()
            create_h_tunnel(prevx, thisx, prevy)
            create_v_tunnel(prevy, thisy, thisx)

            place_objects(this_room)
            rooms.append(this_room)

    (startx, starty) = rooms[0].center()
    player.x, player.y = startx, starty


def place_objects(room):
    num_monsters = randint(0, monster_max)

    for i in range(num_monsters):
        x = randint(room.x1, room.x2)
        y = randint(room.y1, room.y2)

        if not is_blocked(x, y):
            # 20% orc, 30% troll, 50% kobold
            choice = randint(0, 100)
            if choice < 20:
                monster = Entity(
                    x, y, 'o', 'orc', colors.desaturated_green, blocks=True)
            elif choice < 50:
                monster = Entity(
                    x, y, 'T', 'troll', colors.darker_green, blocks=True)
            else:
                monster = Entity(
                    x, y, 'k', 'kobold', colors.light_grey, blocks=True)

            objects.append(monster)


def player_move(dx, dy):
    global fov_recompute

    # Where are we trying to move?
    x = player.x + dx
    y = player.y + dy

    # Is there an entity there?
    # TODO what if there's an item under a monster?
    target = None
    for obj in objects:
        if obj.x == x and obj.y == y:
            target = obj
            break

    # Attack if there's a target
    if target is not None:
        print('Placeholder attack message')
    else:
        player.move(dx, dy)
        fov_recompute = True



def render_all():
    global fov_recompute
    global visible_tiles

    # # This block will draw the whole map as if it has been explored
    # for y in range(field_height):
    #     for x in range(field_width):
    #         # Get the walls from the field generated in @make_field()
    #         wall = field[x][y].block_sight
    #         # Render walls as a different color
    #         if wall:
    #             con.draw_char(x, y, None, fg=None, bg=c_dark_wall)
    #         else:
    #             con.draw_char(x, y, None, fg=None, bg=c_dark_gnd)

    if fov_recompute:
        fov_recompute = False
        visible_tiles = tdl.map.quickFOV(player.x, player.y,
                                         is_visible_tile,
                                         fov=fov_algo,
                                         radius=fov_radius,
                                         lightWalls=fov_light_walls)

    for y in range(field_height):
        for x in range(field_width):
            visible = (x, y) in visible_tiles
            wall = field[x][y].block_sight

            if not visible:
                if field[x][y].explored:
                    if wall:
                        con.draw_char(x, y, None, fg=None, bg=c_dark_wall)
                    else:
                        con.draw_char(x, y, None, fg=None, bg=c_dark_gnd)
            else:
                if wall:
                    con.draw_char(x, y, None, fg=None, bg=c_light_wall)
                else:
                    con.draw_char(x, y, None, fg=None, bg=c_light_gnd)

                field[x][y].explored = True

    for obj in objects:
        obj.draw()

    root.blit(con, 0, 0, screen_width, screen_height, 0, 0)


# Screen size
screen_width = 80
screen_height = 50

# Field size
field_width = 80
field_height = 50

# Tile colors
# Unlit tiles
c_dark_wall = (0, 0, 100)
c_dark_gnd = (50, 50, 150)
# Lit tiles
c_light_wall = (130, 110, 50)
c_light_gnd = (200, 180, 50)

# Set the font
# tdl.set_font('fontfile.png', greyscale=True, altLayout=True)

# tdl FOV settings
fov_algo = 'SHADOW'
fov_light_walls = True
fov_radius = 10

# Monster settings
# The maximum number of monsters in a single room
monster_max = 3

# Initialize the main display
root = tdl.init(screen_width,
                   screen_height,
                   title="giraffelike",
                   fullscreen=False)
# & Helper undisplay
con = tdl.init(screen_width, screen_height)

# misc globals
game_state = 'play'
player_action = None

# Create the player object
player = Entity(0, 0, '@', 'player', colors.white, blocks=True)

# list which holds all entities
objects = [player]

# Create the field
make_field()

fov_recompute = True

while not tdl.event.is_window_closed():
    render_all()
    tdl.flush()

    for obj in objects:
        obj.clear()

    # Wait for player action
    player_action = handle_keys()

    # Monsters' turn
    if game_state == 'play' and player_action != 'no-turn':
        for obj in objects:
            if obj != player:
                print(f'The {obj.name} makes a terrible noise.')

    # Quit on esc
    if player_action == 'exit':
        break
