#!venv/bin/python3
# -*- coding: utf-8 -*-

import colors
import math
import tdl
import textwrap
from random import randint


class BasicMonster:
    """AI for simple monsters.

    If the player can see the monster, the monster will chase the player.
    """

    def take_turn(self):
        monster = self.owner
        if (monster.x, monster.y) in visible_tiles:
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)
            elif player.fighter.hp > 0:
                monster.fighter.attack(player)


class Entity:
    """Base class for any entity in the dungeon.

    Keyword arguments:
    x -(int)- starting x coordinate on the dungeon map
    y -(int)- starting y coordinate on the dungeon map
    char -(str)- the alphanumeric character used to represent the entity
    name -(str)- name of the entity
    color -(tuple)- rgb value of the character's `char`
    blocks -(bool)- true sets entity walky, false blocky
    fighter -(object)- object to initialize entity's combat stats
    ai -(object)- object which holds ai instructions
    """

    def __init__(self, x, y, char, name, color, blocks=False, fighter=None,
                 ai=None, item=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self
        self.ai = ai
        if self.ai:
            self.ai.owner = self
        self.item = item
        if self.item:
            self.item.owner = self

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def move(self, dx, dy):
        # If the desired tile is blocked, do not move
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def draw(self):
        if (self.x, self.y) in visible_tiles:
            con.draw_char(self.x, self.y, self.char, self.color)

    def clear(self):
        con.draw_char(self.x, self.y, ' ', self.color)

    def send_to_back(self):
        global objects
        objects.remove(self)
        objects.insert(0, self)


class Fighter:
    """Properties for anything which may fight.

    Keyword Arguments:
    hp -(int)- the amount of health points the entity has
    defense -(int)- the amount by which incoming damage is reduced
    power -(int)- the amount the entity deals as outgoing damage
    death_func -(function)- in the event of death, call
    """

    def __init__(self, hp, defense, power, death_func=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_func = death_func

    def take_damage(self, damage):
        damage = damage

        if damage > 0:
            self.hp -= damage

        if self.hp <= 0:
            death = self.death_func
            if death is not None:
                death(self.owner)

    def attack(self, target):
        damage = self.power - target.fighter.defense

        if damage > 0:
            message(f"{self.owner.name} attacks {target.name} for {damage}",
                    colors.gray)
            target.fighter.take_damage(damage)
        else:
            print(f'{self.owner.name}\'s puny attack bounced off {target.name}')


class Item:
    """An item which can be used by the player"""

    def pick_up(self):
        if len(inventory) >= 26:
            message(f'Pockets are full, couldn\'t pick up {self.owner.name}',
                    colors.red)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message(f'You put a {self.owner.name} in your pocket.',
                    colors.green)


class Tile:
    """This represents a map tile.

    Keyword Arguments:
    blocked -(bool)- walkable if true, unwalkable if false
    block_sight -(bool)- for FOV, blocks LOS if true
    """
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


def get_names_under_mouse():
    global visible_tiles

    (x, y) = mouse_coord
    names = [obj.name for obj in objects
             if obj.x == x and obj.y == y and (obj.x, obj.y) in visible_tiles]
    names = ', '.join(names)
    return names.capitalize()

def handle_keys():
    global fov_recompute
    global mouse_coord

    keypress = False
    for event in tdl.event.get() :
        if event.type == 'KEYDOWN':
            user_input = event
            keypress = True
        if event.type == 'MOUSEMOTION':
            mouse_coord = event.cell

    if not keypress:
        return 'no-turn'



    if game_state == 'play':
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
            # Actions which do not take a turn
            # alt + enter : toggle fullscreen
            if user_input.key == 'ENTER' and user_input.alt :
                tdl.set_fullscreen(not tdl.get_fullscreen())
            # enter : pick up item beneath player
            elif user_input.key == 'ENTER':
                for obj in objects:
                    if obj.x == player.x and obj.y == player.y and obj.item:
                        obj.item.pick_up()
                        break
            elif user_input.key == 'ESCAPE':
                # escape : quit
                return 'exit'

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

    room_max = 13
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


def message(new_msg, color=colors.white):
    new_msg_lines = textwrap.wrap(new_msg, msg_width)

    for line in new_msg_lines:
        if len(game_msgs) == msg_height:
            del game_msgs[0]

        game_msgs.append((line, color))


# Death mechanics
def player_death(player):
    global game_state
    message('...and You Dead.')
    player.color = colors.dark_red
    player.char = 'F'
    # Game over, dood.
    game_state = 'dead'


def monster_death(monster):
    message(f'{monster.name.capitalize()} is slain!')
    monster.name = f'what remains of {monster.name}'
    monster.char = '%'
    monster.color = colors.dark_red
    monster.send_to_back()
    # Disable the important mechanics on this entity
    monster.blocks = False
    monster.fighter = None
    monster.ai = None


def place_objects(room):
    # Generate the monsters
    num_monsters = randint(0, monster_max)

    for i in range(num_monsters):
        x = randint(room.x1 + 1, room.x2 - 1)
        y = randint(room.y1 + 1, room.y2 - 1)
        fighter_monster = Fighter(
            hp=10, defense=0, power=3, death_func=monster_death)
        ai_monster = BasicMonster()

        if not is_blocked(x, y):
            # 20% orc, 30% troll, 50% kobold
            choice = randint(0, 100)
            if choice < 20:
                monster = Entity(x, y, 'o', 'orc',
                                 colors.desaturated_green, blocks=True,
                                 fighter=fighter_monster, ai=ai_monster)
            elif choice < 50:
                monster = Entity(x, y, 'T', 'troll',
                                 colors.darker_green, blocks=True,
                                 fighter=fighter_monster, ai=ai_monster)
            else:
                monster = Entity(x, y, 'k', 'kobold',
                                 colors.light_grey, blocks=True,
                                 fighter=fighter_monster, ai=ai_monster)

            objects.append(monster)

    # Generate the items
    num_items = randint(0, items_max)

    for i in range(num_items):
        x = randint(room.x1 + 1, room.x2 - 1)
        y = randint(room.y1 + 1, room.y2 - 1)

        # Do not place items on blocked areas
        if not is_blocked(x, y):
            item_component = Item()
            item = Entity(
                x, y, '!', 'healing potion', colors.violet, item=item_component)
            objects.append(item)
            item.send_to_back()


def player_move(dx, dy):
    global fov_recompute

    # Where are we trying to move?
    x = player.x + dx
    y = player.y + dy

    # Is there an entity there?
    target = None
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break

    # Attack if there's a target
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        fov_recompute = True


def render_bar(x, y,total_width, name, value, maximum,
               bar_color,bg_color, text_color):
    """Render a bar which visually represents some stat"""

    bar = int(float(value) / maximum * total_width)

    panel.draw_rect(x, y, total_width, 1, None, bg=bg_color)

    if bar > 0:
        panel.draw_rect(x, y, bar, 1, None, bg=bar_color)

    text = f'{name}: {str(value)} / {str(maximum)}'
    x_centered = x + (total_width - len(text)) // 2
    panel.draw_str(x_centered, y, text, fg=text_color, bg=None)


def render_all():
    global fov_recompute
    global visible_tiles

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
        if obj != player:
            obj.draw()
    player.draw()

    # Blit the field `con` to the main screen `root`
    root.blit(con, 0, 0, screen_width, screen_height, 0, 0)

    # Clear the GUI `panel`
    panel.clear(fg=colors.white, bg=colors.black)

    # Render messages
    y = 1
    for (line, color) in game_msgs:
        panel.draw_str(msg_x, y, line, bg=None, fg=color)
        y += 1

    # Rerender the bars
    # Player's HP
    render_bar(1, 1, bar_width, 'HP', player.fighter.hp, player.fighter.max_hp,
               colors.light_red, colors.darker_red, colors.white)

    panel.draw_str(1, 0, get_names_under_mouse(), bg=None, fg=colors.light_gray)

    # Blit the newly rendered bars to `root`
    root.blit(panel, 0, panel_y, screen_width, panel_height, 0, 0)


# Screen size
screen_width = 80
screen_height = 50

# FPS
fps_limit = 20
tdl.setFPS(fps_limit)

# Field size
field_width = 80
field_height = 43

# HUD settings
# Stats
bar_width = 20
panel_height = 7
panel_y = screen_height - panel_height
# Messages
msg_x = bar_width + 2
msg_width = screen_width - bar_width -2
msg_height = panel_height -1
game_msgs = []

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

# The maximum number of monsters in a single room
monster_max = 3

# The maximum number of items to spawn in a single room
items_max = 2

# Initialize the main display
root = tdl.init(screen_width,
                   screen_height,
                   title="giraffelike",
                   fullscreen=False)

# & Helper main undisplay
con = tdl.Console(field_width, field_height)

# & helper GUI undisplay
panel = tdl.Console(screen_width, panel_height)

# misc globals
game_state = 'play'
player_action = None

# Create the player object
fighter_mod = Fighter(hp=30, defense=2, power=5, death_func=player_death)
player = Entity(
    0, 0, '@', 'player', colors.white, blocks=True, fighter=fighter_mod)

objects = [player]

make_field()

fov_recompute = True

mouse_coord = (0, 0)

inventory = []

# Welcome message
message('Welcome to the Warehouse, nerd.', colors.red)

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
            if obj.ai:
                obj.ai.take_turn()

    # Quit on esc
    if player_action == 'exit':
        break
