# Python 3.6
# -*- coding: utf-8 -*-

import tdl


class Entity:
    def __init__(self, x, y, char, color) :
        self.x = x
        self.y = y
        self.char = char
        self.color = color

    def move(self, dx, dy) :
        # If the desired tile is blocked, do not move
        if not field[self.x + dx][self.y + dy].blocked:
            self.x += dx
            self.y += dy

    def draw(self) :
        con.draw_char(self.x, self.y, self.char, self.color)

    def clear(self) :
        con.draw_char(self.x, self.y, ' ', self.color)

class Tile:
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked

        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight


def handle_keys():
    user_input = tdl.event.key_wait()

    # Quit on esc
    if user_input.key == 'ESCAPE':
        return True

    # Shift player on arrow key
    if user_input.key == 'UP':
        player.move(0, -1)
    elif user_input.key == 'DOWN':
        player.move(0, 1)
    elif user_input.key == 'LEFT':
        player.move(-1, 0)
    elif user_input.key == 'RIGHT':
        player.move(1, 0)


def make_field():
    global field

    # Create a 2D array of Tiles
    field = [
        [Tile(False) for y in range(field_height)] for x in range(field_width)]

    # Mark walls as blocked
    field[30][22].blocked = True
    field[30][22].block_sight = True
    field[50][22].blocked = True
    field[50][22].block_sight = True


def render_all():
    for y in range(field_height):
        for x in range(field_width):
            # Get the walls from the field generated in @make_field()
            wall = field[x][y].block_sight
            # Render walls as a different color
            if wall:
                con.draw_char(x, y, None, fg=None, bg=c_dark_wall)
            else:
                con.draw_char(x, y, None, fg=None, bg=c_dark_gnd)

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
c_dark_wall = (0, 0, 100)
c_dark_gnd = (50, 50, 150)

# Set the font
# tdl.set_font('arial110x10.png', greyscale=True, altLayout=True)

# Initialize the main display
root = tdl.init(screen_width,
                   screen_height,
                   title="giraffelike",
                   fullscreen=False)
# & Helper undisplay
con = tdl.init(screen_width, screen_height)

# Create the player object
player = Entity(screen_width // 2, screen_height // 2, '@', (255, 255, 255))

# Create an npc
npc = Entity(screen_width // 2 - 5, screen_height // 2, '@', (255, 255, 0))

# list all of the entities
objects = [npc, player]

# Create the field
make_field()

while not tdl.event.is_window_closed():

    # Write the entities to the screen
    render_all()
    # Push the display
    tdl.flush()

    # Clear the entities from the display
    for obj in objects:
        obj.clear()

    # Wait for input
    exit_game = handle_keys()
    # Quit on esc
    if exit_game:
        break
