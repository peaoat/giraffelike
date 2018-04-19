# Python 3.6
# -*- coding: utf-8 -*-

import colors
import math
# pip3 install tdl
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


# # # # # # # # # # # # # # # # # # # #
# Entities and Entity Modules
# # # # # # # # # # # # # # # # # # # #


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
    item -(object)- object which holds item instructions
    """

    def __init__(self, x, y, char, name, color, blocks=False,
                 always_visible=False, fighter=None, ai=None, item=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.always_visible = always_visible

        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self
        self.ai = ai
        if self.ai:
            self.ai.owner = self
        self.item = item
        if self.item:
            self.item.owner = self

    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

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
        if (self.x, self.y) in visible_tiles or \
                (self.always_visible and field[self.x][self.y].explored):
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
    xp -(int)- the amount of experience the entity has
        xp is yielded to the entity's murderer upon death
    death_func -(function)- in the event of death, call

    Functions:
    attack(<target>) - attempts to deal damage to <target> Entity
    heal(<amount>) - attempts to heal self by <amount>
        if amount healed exceeds maximum, hp is set to maximum
    take_damage(<amount>) - subtracts <amount> hp from self
    """

    # TODO: Magic Defense

    def __init__(self, hp, defense, power, xp, mp=0, mag=0, death_func=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.xp = xp
        self.max_mp = mp
        self.mp = mp
        self.mag = mag
        self.death_func = death_func

    def attack(self, target):
        damage = self.power - target.fighter.defense

        if damage > 0:
            message(f"{self.owner.name} attacks {target.name} for {damage}",
                    colors.gray)
            target.fighter.take_damage(damage)
        else:
            atk_msg = f'{self.owner.name}\'s puny'
            atk_msg += f' attack bounced off {target.name}'
            message(atk_msg, colors.light_gray)

    def heal(self, health, mana=0):
        self.hp += health
        self.mp += mana
        # No over-healing
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        if self.mp > self.max_mp:
            self.mp = self.max_mp

    def take_damage(self, damage):
        damage = damage

        if damage > 0 :
            self.hp -= damage

        if self.hp <= 0 :
            if self.owner != player:
                player.fighter.xp += self.xp

            death = self.death_func
            if death is not None:
                death(self.owner)


class Item:
    """An item which can be used by the player

    Keyword Arguments:
    use_func -(function)- the function to call when using this item
    kwargs -(dict)- the arguments to pass to use_func
    """

    def __init__(self, use_func=None, kwargs=None):
        self.use_func = use_func
        self.kwargs = kwargs

    def drop(self):
        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message(f'You place the {self.owner.name} on the ground', colors.yellow)

    def pick_up(self):
        # Add to inventory
        if len(inventory) >= 26:
            message(f'Pockets are full, couldn\'t pick up {self.owner.name}',
                    colors.red)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message(f'You put a {self.owner.name} in your pocket.',
                    colors.green)

    def use(self):
        # If there's no function to call, you can't use this item
        if self.use_func is None:
            message(f'You cant use a {self.owner.name}')
        else:
            # This calls use_func and checks the return
            if self.use_func(**self.kwargs) != 'cancel':
                # Remove the item from inventory unless it shouldn't be removed
                inventory.remove(self.owner)


def closest_monster(max_range):
    closest_enemy = None
    closest_dist = max_range + 1
    for obj in objects:
        if obj.fighter \
                and not obj == player \
                and (obj.x, obj.y) in visible_tiles:
            dist = player.distance_to(obj)
            if dist < closest_dist:
                closest_enemy = obj
                closest_dist = dist
    return closest_enemy


# # Spells and Items # #

def healing(hp_lower, hp_upper, mp_cost):
    """Item and spell module for restoring player HP

    Keyword Arguments:
    hp_lower -(int)- lower limit of healing
    hp_upper -(int)- upper limit of healing
    mp_cost -(int)- the amount of mp required to cast the spell
    """

    if player.fighter.hp == player.fighter.max_hp:
        message('You are already at full HP', colors.light_red)
        return 'cancel'

    if player.fighter.mp < mp_cost:
        message(f'Not enough mp! ({mp_cost})', colors.yellow)
        return 'cancel'

    player.fighter.mp -= mp_cost

    heal_amount = randint(hp_lower, hp_upper)
    healmsg = f'On a scale of 0 to {player.fighter.max_hp}, you\'re feeling'
    healmsg += f' about {heal_amount} better than you did.'
    message(healmsg, colors.azure)
    player.fighter.heal(heal_amount)


def magic_missile(damage, mp_cost):
    """Deals damage to the nearest enemy in the FOV

    Keyword Arguments:
    damage -(int)- Amount of damage to deal to the foe
    mp_cost -(int)- the amount of mp required to cast the spell
    """

    if player.fighter.mp < mp_cost:
        message('You do not have enough MP to cast this spell')
        return 'cancel'

    monster = closest_monster(fov_radius)

    if monster is None:
        message('You cannot cast Magic Missile at the Darkness', colors.red)
        return 'cancel'

    player.fighter.mp -= mp_cost
    atk_msg = f'A pale blue energy violently strikes the {monster.name}'
    atk_msg += f' for {damage} points of damage'
    message(atk_msg, colors.light_blue)
    monster.fighter.take_damage(damage)


def mana_recovery(mp_lower, mp_upper):
    """Item module for restoring the player's MP

    Keyword Arguments:
    mp_lower -(int)- lower limit of mp to restore
    mp_upper -(int)- upper limit of mp to restore
    """

    if player.fighter.mp == player.fighter.max_mp:
        message("You don't need to recover any MP", colors.red)
        return 'cancel'

    rec_mp = randint(mp_lower, mp_upper)
    player.fighter.heal(health=0, mana=rec_mp)
    message(f'You recovered {rec_mp} MP.')


def player_death(player):
    """Displays player's corpse and a Game Over message"""

    global game_state
    message('...and You Dead.')
    player.color = colors.dark_red
    player.char = 'F'
    # Game over, dood.
    game_state = 'dead'


def monster_death(monster):
    """Displays the monster's corpse and a death message"""

    message(f'{monster.name.capitalize()} is slain!')
    monster.name = f'what remains of {monster.name}'
    monster.char = '%'
    monster.color = colors.dark_red
    monster.send_to_back()
    # Disable the important mechanics on this entity
    monster.blocks = False
    monster.fighter = None
    monster.ai = None


# # # # # # # # # # # # # # # # # # # #
#   Dungeon Generation
# # # # # # # # # # # # # # # # # # # #


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
    rooms = []

    # # Settings
    # The largest height or width of a room
    room_max = 13
    # The smallest h or w
    room_min = 5
    # Maximum number of rooms a map may generate
    room_num = 30

    # Create a 2D array of Tiles
    field = [
        [Tile(True) for y in range(field_height)] for x in range(field_width)]

    for r in range(room_num):
        w = randint(room_min, room_max)
        h = randint(room_min, room_max)
        x = randint(0, field_width - w -1)
        y = randint(0, field_height - h - 1)

        this_room = Rect(x, y, w, h)
        fail = False

        # Check for overlapping rooms
        for other_room in rooms:
            if this_room.intersect(other_room):
                fail = True
                break

        # If this room doesn't overlap others, use it
        if not fail:
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

    # The player starts in the first room in the list
    (startx, starty) = rooms[0].center()
    player.x, player.y = startx, starty

    # The stairs on in the last room in the list
    (endx, endy) = rooms[-1].center()
    stairs = Entity(endx, endy, '\\', 'stairs', colors.white,
                    always_visible=True)
    objects.append(stairs)
    stairs.send_to_back()


monster_dict = {
    'kobold' : {
        'char' : 'k',
        'color' : colors.dark_azure,
        'fighter': {
            'hp' : 8,
            'defense' : 0,
            'power' : 3,
            'xp' : 500,
            'mp' : 0,
            'mag' : 0,
            'death_func' : monster_death
        },
        'name' : 'kobold',
    },
    'orc' : {
        'char' : 'o',
        'color' : colors.desaturated_green,
        'fighter': {
            'hp' : 12,
            'defense' : 1,
            'power' : 3,
            'xp' : 40,
            'mp' : 0,
            'mag' : 0,
            'death_func' : monster_death
        },
        'name' : 'orc',
    },
    'troll' : {
        'char' : 'T',
        'color' : colors.darker_green,
        'fighter': {
            'hp' : 15,
            'defense' : 2,
            'power' : 5,
            'xp' : 50,
            'mp' : 0,
            'mag' : 0,
            'death_func' : monster_death
        },
        'name' : 'troll',
    }
}


def place_objects(room):
    global dungeon_level

    # Generate the monsters
    # TODO: Method for generating long dungeon escalation?
    # TODO: dungeon escalation for monster stats
    monster_max = dungeon_escalation([[2, 1], [3, 4], [5, 6]])
    num_monsters = randint(0, monster_max)

    monster_chances = {'kobold' : 60,
                       'orc' : dungeon_escalation([[20, 3], [30, 5], [60, 7]]),
                       'troll' : dungeon_escalation(
                           [[15, 4], [30, 6], [45, 8]])}

    for i in range(num_monsters):
        x = randint(room.x1 + 1, room.x2 - 1)
        y = randint(room.y1 + 1, room.y2 - 1)

        if not is_blocked(x, y):
            this_monster = monster_dict[randomizer(monster_chances)]
            this_ai = BasicMonster()

            monster = Entity(x, y,
                             this_monster['char'],
                             this_monster['name'],
                             this_monster['color'],
                             blocks=True,
                             fighter=Fighter(**this_monster['fighter']),
                             ai=this_ai)

            objects.append(monster)

    # Generate the items

    # TODO: Store and retrieve items from a dict
    # eg item_dict = {'item name' : {'item_char' : '#'}}
    # item_dict['item']['item_char'] == '#'

    max_items = dungeon_escalation([[1, 1], [2, 5], [3, 10]])
    num_items = randint(0, max_items)

    item_chances = {'Minor Healing Potion' : 30,
                    'Minor Mana Potion' : dungeon_escalation(
                        [[15, 5], [20, 10]]),
                    'Scroll of Minor Magic Missile' : dungeon_escalation(
                        [[15, 3], [20, 5], [25, 10]])}

    for i in range(num_items):
        x = randint(room.x1 + 1, room.x2 - 1)
        y = randint(room.y1 + 1, room.y2 - 1)

        # Do not place items on blocked areas
        if not is_blocked(x, y):
            this_item = randomizer(item_chances)

            if this_item == 'Minor Healing Potion':
                # healing(hp_lower=int,hp_upper=int, mp_cost=int)
                hp_lower = int(player.fighter.max_hp * 0.05)
                hp_upper = int(player.fighter.max_hp * 0.12)
                if hp_lower < 1:
                    hp_lower = 1
                if hp_upper <= hp_lower:
                    hp_upper = hp_lower + 4

                minor_potion = {'hp_lower': hp_lower,
                                'hp_upper': hp_upper,
                                'mp_cost': 0}

                item_char = '!'
                item_color = colors.light_red
                item_name = 'Minor Healing Potion'
                item_module = Item(use_func=healing,
                                   kwargs=minor_potion)

            elif this_item == 'Minor Mana Potion':
                # mana_recovery(mp_lower=int, mp_upper=int)
                mp_lower = int(player.fighter.max_mp * 0.05)
                mp_upper = int(player.fighter.max_mp * 0.12)
                if mp_lower < 1:
                    mp_lower = 1
                if mp_upper <= mp_lower:
                    mp_upper = mp_lower + 1
                minor_mana = {'mp_lower': mp_lower,
                              'mp_upper': mp_upper}

                item_char = '!'
                item_color = colors.light_azure
                item_name = 'Minor Mana Potion'
                item_module = Item(use_func=mana_recovery,
                                   kwargs=minor_mana)

            else:
                # if this_item == 'Scroll of Minor Magic Missile':
                # # magic_missile(damage=int, mp_cost=int)
                damage = (dungeon_level // 2) + 7
                minor_missile = {'damage': damage,
                                 'mp_cost': 0}

                item_char = '#'
                item_color = colors.light_blue
                item_name = 'Scroll of Minor Magic Missile'
                item_module = Item(use_func=magic_missile,
                                   kwargs=minor_missile)

            item = Entity(x, y, item_char, item_name,
                          item_color, always_visible=True, item=item_module)
            objects.append(item)
            item.send_to_back()


def random_index(chances):
    """Returns the index which matches a randomized choice

    Keyword Arguments:
    chances -(list of ints)- each int represents the likelyhood of being chosen
        compared to the sum of the list
    """
    die = randint(1, sum(chances))
    total = 0

    for index, c in enumerate(chances):
        total += c
        if die <= total:
            return index


def randomizer(chance_dict):
    """Wraps random_index and returns the dict entry it chooses randomly"""
    chances = list(chance_dict.values())
    strings = list(chance_dict.keys())

    return strings[random_index(chances)]


def dungeon_escalation(table):
    for (value, level) in reversed(table):
        if dungeon_level >= level:
            return value
    return 0


def next_level():
    global dungeon_level, fov_recompute, objects

    fov_recompute = True
    dungeon_level += 1
    objects = [player]

    regen_hp, regen_mp = player_regen()
    player.fighter.heal(health=regen_hp, mana=regen_mp)

    message('During a calm moment, you find time to rest...', colors.white)
    message(f'You regained {regen_hp} hp.', colors.light_red)
    message(f'and {regen_mp} mp.', colors. light_blue)
    message('Back to work...', colors.chartreuse)

    con.clear(fg=colors.black, bg=colors.black)
    root.clear(fg=colors.black, bg=colors.black)
    make_field()


# # # # # # # # # # # # # # # # # # # #
#   Player Interaction
# # # # # # # # # # # # # # # # # # # #


def player_regen():
    """ The player regenerates health between each floor
    """

    regen_hp = int(player.fighter.max_hp
                   * (0.14 + (player.regen_factor * 0.01)))
    regen_mp = int(player.fighter.max_mp
                   * (0.14 + (player.regen_factor * 0.01)))

    return regen_hp, regen_mp


def cast_spell():
    if len(player.spells) == 0:
        spell_menu = ["You don't know any spells"]
    else:
        spell_menu = [s for s in player.spells]

    spell = menu("Choose a spell to cast\n",
                 spell_menu,
                 40)

    if spell is None or len(player.spells) == 0:
        return 'cancel'
    elif player.spells[spell] == 'Magic Missile':
        magic_missile(damage=int(player.fighter.mag * 0.5),
                      mp_cost=5)

    elif player.spells[spell] == 'Minor Heal':
        healing(hp_lower=int(player.fighter.mag * 0.25),
                hp_upper=int(player.fighter.mag * 0.75),
                mp_cost=3)

    else:
        return 'cancel'


def check_level_up():
    level_up_xp = level_up_base + player.level * level_up_factor
    if player.fighter.xp >= level_up_xp:
        player.level += 1
        player.fighter.xp -= level_up_xp
        message('You feel stronger!', colors.yellow)

        # Scaling stat advancement

        # HP
        adv_hp_count = 0
        adv_hp = (player.fighter.max_hp * 0.15) - (adv_hp_count * 0.005)
        if adv_hp < player.fighter.max_hp * 0.04:
            adv_hp = int(player.fighter.max_hp * 0.04)
        else:
            adv_hp = int(adv_hp)

        # MP
        adv_mp_count = 0
        adv_mp = (player.fighter.max_mp * 0.2) - (adv_mp_count * 0.0075)
        if adv_mp < player.fighter.max_mp * 0.04:
            adv_mp = int(player.fighter.max_mp * 0.04)
        else:
            adv_mp = int(adv_mp)

        # STR
        # TODO:
        adv_str_count = 0
        adv_str = 2 if count % 0 == 0 else 1

        choice_list = [f'HP : {player.fighter.max_hp} (+ {adv_hp})',
                       f'MP : {player.fighter.max_mp} (+ {adv_mp})',
                       f'STR: {player.fighter.power} (+ {adv_str})',
                       f'MAG: {player.fighter.mag} (+ 1)',
                       f'DEF: {player.fighter.defense} (+ 1)',
                       f'REG: {player.regen_factor} (+ 1)']

        # Add available skills and spells
        if player.level >= 2 and 'Minor Heal' not in player.spells:
            choice_list.append('Minor Heal')
        if player.level >= 5 and 'Magic Missile' not in player.spells:
            choice_list.append('Magic Missile')

        choice = 'cancel'
        while choice is 'cancel':
            choice = menu('Promotion Get!\n',
                          choice_list,
                          level_screen_width)

            if choice == 0:
                player.fighter.max_hp += adv_hp
                player.fighter.hp += adv_hp
                adv_hp_count += 1
            elif choice == 1:
                player.fighter.max_mp += adv_mp
                player.fighter.mp += adv_mp
                adv_mp_count += 1
            elif choice == 2:
                player.fighter.power += adv_str
                adv_str_count += 1
            elif choice == 3:
                player.fighter.mag += 1
            elif choice == 4:
                player.fighter.defense += 1
            elif choice == 5:
                player.regen_factor += 1
            elif choice is 'cancel':
                pass
            elif choice_list[choice] not in player.spells:
                player.spells.append(choice_list[choice])


# def get_names_under_mouse():
#     """Returns the name of an Entity underneath the player's mouse"""
#
#     global visible_tiles
#
#     (x, y) = mouse_coord
#     names = [obj.name for obj in objects
#              if obj.x == x and obj.y == y and (obj.x, obj.y) in visible_tiles]
#     names = ', '.join(names)
#     return names.capitalize()


def handle_keys():
    """Checks the player's inputs every frame.
    Returns 'no-turn' if the player did not take an action.
    """

    global fov_recompute, mouse_coord, game_state

    user_input = tdl.event.key_wait()

    # esc : quit
    if user_input.key == 'ESCAPE':
        return 'exit'

    if game_state == 'play':
        # # Actions which take a turn

        # Move the player with the arrow keys
        if user_input.key == 'UP':
            player_move(0, -1)
        elif user_input.key == 'DOWN':
            player_move(0, 1)
        elif user_input.key == 'LEFT':
            player_move(-1, 0)
        elif user_input.key == 'RIGHT':
            player_move(1, 0)
        elif user_input.key == 'SPACE':
            message('You twiddle your thumbs')

        # s : cast a spell
        elif user_input.char == 's':
            if cast_spell() == 'cancel':
                return 'no-turn'

        # i : use an item from inventory
        elif user_input.char == 'i':
            chosen_item = inventory_menu(
                'Choose an item to use, esc to cancel\n')
            if chosen_item == 'cancel':
                return 'no-turn'
            else:
                chosen_item.use()

        # actions which do not consume a turn
        else:
            # \ : descend to the next level
            if user_input.char == '\\':
                next_level()

            # shift : pick up item beneath player
            elif user_input.key == 'SHIFT':
                for item in objects:
                    if item.x == player.x and item.y == player.y and item.item:
                        item.item.pick_up()
                        break

            # d : drop an item from inventory
            elif user_input.char == 'd':
                chosen_item = inventory_menu(
                    'Choose an item to drop, esc to cancel\n')
                if chosen_item is not None:
                    chosen_item.drop()

            return 'no-turn'

    elif game_state == 'dead':
        # esc : quit
        if user_input.key == 'ESCAPE':
            return 'exit'


def inventory_menu(header):
    """Displays the character's inventory as a selectable menu
    Returns the index of the item selected
    Returns 'cancel' if no selection or no items
    """

    if len(inventory) == 0:
        options = ['Inventory is empty']
    else:
        options = [item.name for item in inventory]

    index = menu(header, options, inventory_width)

    if index is 'cancel' or len(inventory) == 0:
        return 'cancel'
    return inventory[index].item


def menu(header, options, width):
    """Creates a menu screen which is displayed over the main game
    Returns the index of the option selected
    """

    if len(options) > 26:
        raise ValueError('Cannot have more than 26 options')

    header_wrapped = []
    for header_line in header.splitlines():
        header_wrapped.extend(textwrap.wrap(header_line, width))
    header_height = len(header_wrapped)
    height = len(options) + header_height

    window = tdl.Console(width, height)
    window.draw_rect(0, 0, width, height, None, fg=colors.white, bg=None)
    for i, line in enumerate(header_wrapped):
        window.draw_str(0, 0+i, header_wrapped[i])

    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = f'({chr(letter_index)}) {option_text}'
        window.draw_str(0, y, text, bg=None)
        y += 1
        letter_index += 1

    x = screen_width // 2 - width // 2
    y = screen_height // 2 - height // 2
    root.blit(window, x, y, width, height, 0, 0)

    tdl.flush()

    key = tdl.event.key_wait()
    while key.key == 'TEXT':
        key = tdl.event.key_wait()
    key_char = key.char

    if len(key_char) != 1:
        key_char = ' '

    index = ord(key_char) - ord('a')

    if 0 <= index < len(options):
        return index
    return 'cancel'


def message(new_msg, color=colors.white):
    """Displays a message on the HUD in the color passed

    Keyword Arguments:
    new_msg -(str)- String which will be displayed in the messages hud
    color -(tuple)- rgb value to display for this message
    """

    new_msg_lines = textwrap.wrap(new_msg, msg_width)

    for line in new_msg_lines:
        if len(game_msgs) == msg_height:
            del game_msgs[0]

        game_msgs.append((line, color))


# def target_tile(max_range=None):
#     """Returns the position of a tile on left-click if in FOV or Range
#     Returns (None, None) on right click or esc
#     """
#
#     global mouse_coord
#
#     while True:
#         tdl.flush()
#         clicked = False
#
#         for event in tdl.event.get():
#             if event.type == 'MOUSEMOTION':
#                 mouse_coord = event.cell
#             if event.type == 'MOUSEDOWN' and event.button == 'LEFT':
#                 clicked = True
#             elif ((event.type == 'MOUSEDOWN' and event.button == 'RIGHT')
#                or (event.type == 'KEYDOWN' and event.key == 'ESCAPE')):
#                 return (None, None)
#         render_all()
#
#         x = mouse_coord[0]
#         y = mouse_coord[1]
#         if (clicked
#               and mouse_coord in visible_tiles
#               and (max_range is None or player.distance(x, y) <= max_range)):
#             return mouse_coord
#
#
# def target_monster(max_range=None):
#     while True:
#         (x, y) = target_tile(max_range)
#         if x is None:
#             return None
#
#         for obj in objects:
#             if obj == x and obj.y == y and obj.fighter and obj != player:
#                 return obj


def player_move(dx, dy):
    global fov_recompute

    # Where are we trying to move?
    x = player.x + dx
    y = player.y + dy

    # Is there a fighter there to target?
    target = None
    for thing in objects:
        if thing.fighter and thing.x == x and thing.y == y:
            target = thing
            break

    # Attack if there's a target
    if target is not None:
        player.fighter.attack(target)
    # Move there if there's no target
    else:
        player.move(dx, dy)
        fov_recompute = True


def render_bar(x, y, total_width, name, value, maximum,
               bar_color,bg_color, text_color):
    """Render a bar which visually represents some stat
    and draw it to the `panel` HUD element"""

    bar = int(float(value) / maximum * total_width)

    panel.draw_rect(x, y, total_width, 1, None, bg=bg_color)

    if bar > 0:
        panel.draw_rect(x, y, bar, 1, None, bg=bar_color)

    text = f'{name}: {str(value)} / {str(maximum)}'
    x_centered = x + (total_width - len(text)) // 2
    panel.draw_str(x_centered, y, text, fg=text_color, bg=None)


def render_all():
    """render everything to the screen"""

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

    # Re-render the stats displays

    # Monster under mouse
    # panel.draw_str(1, 0, get_names_under_mouse(), bg=None, fg=colors.light_gray)

    # Player's HP
    render_bar(1, 1, bar_width, 'HP', player.fighter.hp, player.fighter.max_hp,
               colors.light_red, colors.darker_red, colors.white)

    # Player's MP
    render_bar(1, 2, bar_width, 'MP', player.fighter.mp, player.fighter.max_mp,
               colors.light_blue, colors.darker_red, colors.white)

    # Dungeon Level
    panel.draw_str(10, 6, f'Floor: {dungeon_level}',
                   bg=colors.white, fg=colors.black)

    # Player Level
    panel.draw_str(1, 6, f'Level: {player.level}',
                   bg=colors.white, fg=colors.black)

    # Player XP
    panel.draw_str(1, 5, f'xp: {player.fighter.xp} / '
                         + f'{level_up_base + player.level * level_up_factor}',
                   bg=colors.white, fg=colors.black)

    # Blit the newly rendered bars to `root`
    root.blit(panel, 0, panel_y, screen_width, panel_height, 0, 0)


# Screen size
screen_width = 80
screen_height = 60

# FPS
# irrelevant in turn-based, but not harmful
fps_limit = 20
tdl.setFPS(fps_limit)

# Field size
field_width = screen_width
field_height = screen_height - 7

# # HUD settings
# Stats
bar_width = 20
panel_height = 7
panel_y = screen_height - panel_height
# Messages
msg_x = bar_width + 2
msg_width = screen_width - bar_width -2
msg_height = panel_height -1
game_msgs = []
# Inventory
inventory_width = 50

# # Tile colors
# Unlit tiles
c_dark_wall = (0, 0, 100)
c_dark_gnd = (50, 50, 150)
# Lit tiles
c_light_wall = (130, 110, 50)
c_light_gnd = (200, 180, 50)

# Set the font
tdl.set_font('arial12x12.png', greyscale=True, altLayout=True)

# tdl FOV settings
fov_algo = 'SHADOW'
fov_light_walls = True
fov_radius = 10

# Initialize the main display
root = tdl.init(screen_width,
                   screen_height,
                   title="giraffelike",
                   fullscreen=False)

# & Helper main undisplay
con = tdl.Console(field_width, field_height)

# & helper GUI undisplay
panel = tdl.Console(screen_width, panel_height)

# Create the player object
fighter_mod = Fighter(hp=50, defense=1, power=5, xp=349,
                      mp=15, mag=5, death_func=player_death)
player = Entity(
    0, 0, '@', 'player', colors.white, blocks=True,
    fighter=fighter_mod)

# Player settings
inventory = []
player.spells = []
level_up_base = 200
level_up_factor = 150
level_screen_width = 40
# mouse_coord = (0, 0)
player_action = None
player.level = 1
player.regen_factor = 1

# initialize the field
dungeon_level = 1
fov_recompute = True
objects = [player]
make_field()

# Welcome message
message('Welcome to the Warehouse, nerd.', colors.red)

game_state = 'play'
while not tdl.event.is_window_closed():
    render_all()
    tdl.flush()

    check_level_up()

    for obj in objects:
        obj.clear()

    player_action = handle_keys()

    # Quit on esc
    if player_action == 'exit':
        break

    # # Actions which only happen after the player acts
    # Monsters' turn
    if game_state == 'play' and player_action != 'no-turn':
        player_regen()
        for obj in objects:
            if obj.ai:
                obj.ai.take_turn()
