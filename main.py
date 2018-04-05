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
        self.x += dx
        self.y += dy

    def draw(self) :
        con.draw_char(self.x, self.y, self.char, self.color)

    def clear(self) :
        con.draw_char(self.x, self.y, ' ', self.color)


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

# Screen size
screen_width = 80
screen_height = 50

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

objects = [npc, player]

while not tdl.event.is_window_closed():

    # Write the entities to the screen
    for obj in objects:
        obj.draw()

    # Blit the console to the display
    root.blit(con, 0, 0, screen_width, screen_height, 0, 0)
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
