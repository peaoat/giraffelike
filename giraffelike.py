# Python 3.6
# -*- coding: utf-8 -*-

import colors
import math
import sys
import tdl
import textwrap
from random import randint

if sys.version_info.major != 3 or sys.version_info.minor != 6:
    print("This game requires Python version 3.6.")
    sys.exit(1)

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
    equipment -(object)- object which holds equipment instructions
    """

    def __init__(self, x, y, char, name, color, blocks=False,
                 always_visible=False, fighter=None, ai=None, item=None,
                 equipment=None):
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
        self.equipment = equipment
        if self.equipment:
            self.equipment.owner = self
            self.item = Item(use_func=self.equipment.toggle_equip)
            self.item.owner = self

    def clear(self):
        con.draw_char(self.x, self.y, ' ', self.color)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def draw(self):
        # Display this entity if it is in the player's FOV
        # Some entities are 'always visible' after they've been found
        if (self.x, self.y) in visible_tiles or \
                (self.always_visible and field[self.x][self.y].explored):
            con.draw_char(self.x, self.y, self.char, self.color)

    def move(self, dx, dy):
        # If the desired tile is blocked, do not move
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    # TODO: A* movement
    def move_smart(self, target_x, target_y):
        # Don't let those pesky corners stop you from your goal
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        gotox = self.x + dx
        gotoy = self.y + dy
        if is_blocked(gotox, gotoy) and gotox != player.x and gotoy != player.y:
            if gotoy == self.y:
                if target_y > self.y:
                    if not is_blocked(gotox, gotoy + 1):
                        dy += 1
                elif target_y < self.y:
                    if not is_blocked(gotox, gotoy - 1):
                        dy -= 1
            elif gotox == self.x:
                if target_x > self.x and not is_blocked(gotox + 1, gotoy):
                    dx += 1
                elif target_x < self.x and not is_blocked(gotox - 1, gotoy):
                    dx -= 1
        self.move(dx, dy)

    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def send_to_back(self):
        global objects
        objects.remove(self)
        objects.insert(0, self)

    def closest_monster(self, max_range) :
        closest_enemy = None
        closest_dist = max_range + 1
        for obj in objects:
            if obj.fighter \
                    and obj != player \
                    and obj != self \
                    and (obj.x, obj.y) in visible_tiles:
                if (self.name == 'Your ally' or self == player) \
                        and obj.name == 'Your ally':
                    continue
                dist = player.distance_to(obj)
                if dist < closest_dist:
                    closest_enemy = obj
                    closest_dist = dist
        return closest_enemy


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

    def __init__(self, hp, defense, power, xp,
                 mp=0, mag=0, regen=0,
                 death_func=None):
        self.base_max_hp = hp
        self.base_max_mp = mp
        self.base_defense = defense
        self.base_power = power
        self.base_mag = mag
        self.base_regen = regen

        self.hp = hp
        self.mp = mp
        self.xp = xp
        self.death_func = death_func

    @property
    def max_hp(self):
        bonus = sum(eq.max_hp for eq in get_all_equipped())
        return self.base_max_hp + bonus

    @property
    def defense(self):
        bonus = sum(eq.defense for eq in get_all_equipped())
        return self.base_defense + bonus

    @property
    def power(self):
        bonus = sum(eq.power for eq in get_all_equipped())
        return self.base_power + bonus

    @property
    def max_mp(self):
        bonus = sum(eq.max_mp for eq in get_all_equipped())
        return self.base_max_mp + bonus

    @property
    def mag(self):
        bonus = sum(eq.magick for eq in get_all_equipped())
        return self.base_mag + bonus

    @property
    def regen(self):
        bonus = sum(eq.regen for eq in get_all_equipped())
        return self.base_regen + bonus

    def attack(self, target):
        damage = self.power - target.fighter.defense

        if self.owner == player:
            msg_color = colors.light_blue
        elif self.owner.name == 'Your ally':
            msg_color = colors.gold
        else:
            msg_color = colors.light_red

        if damage < 1:
            damage = 1

        message(f"{self.owner.name} attacks {target.name} for {damage}",
                msg_color)
        target.fighter.take_damage(damage)

    def heal(self, health, mana=0):
        self.hp += health
        self.mp += mana
        # No over-healing
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        if self.mp > self.max_mp:
            self.mp = self.max_mp

    def take_damage(self, damage):
        self.hp -= damage

        if self.hp <= 0:
            # TODO: xp goes to the killer even if it's a monster?
            if self.owner != player:
                player.fighter.xp += self.xp

            death = self.death_func
            if death is not None:
                death(self.owner)


class Item:
    """ An item which can be used by the player

    Keyword Arguments:
    use_func -(function)- the function to call when using this item
    kwargs -(dict)- the arguments to pass to use_func
    """

    def __init__(self, use_func=None, kwargs={}):
        self.use_func = use_func
        self.kwargs = kwargs

    def drop(self):
        objects.append(self.owner)
        if self.owner.equipment:
            self.owner.equipment.unequip()
            equipment.remove(self.owner)
        else:
            inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message(f'You place the {self.owner.name} on the ground', colors.yellow)

    def pick_up(self):
        # If it's equipment, put it in your equipment menu
        if self.owner.equipment:
            if len(equipment) >= 26:
                message(
                    f'Your pack is full, couldn\'t pick up {self.owner.name}',
                    colors.red)
                return
            else:
                equipment.append(self.owner)
                objects.remove(self.owner)
                message(f'You put the {self.owner.name} in your pack.',
                        colors.light_green)
            return

        # Add to inventory
        if len(inventory) >= 26:
            message(f'Pockets are full, couldn\'t pick up {self.owner.name}',
                    colors.red)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message(f'You put a {self.owner.name} in your pocket.',
                    colors.light_green)

    def use(self):
        # If this is equipment, toggle equip
        if self.owner.equipment:
            self.owner.equipment.toggle_equip()
            return

        # If there's no function to call, you can't use this item
        if self.use_func is None:
            message(f'You cant use a {self.owner.name}')
        else:
            # This calls use_func and checks the return
            if self.use_func(**self.kwargs) != 'cancel':
                # Remove the item from inventory unless it shouldn't be removed
                inventory.remove(self.owner)


class Equipment:
    """ An item which can be equipped by the user

    Keyword Arguments:
    slot -(string)- exclusive slot to which this item may be equipped"""

    def __init__(self, slot,
                 max_hp=0, max_mp=0, power=0, defense=0, magick=0, regen=0):
        self.slot = slot
        self.max_hp = max_hp
        self.max_mp = max_mp
        self.power = power
        self.defense = defense
        self.magick = magick
        self.regen = regen
        self.is_equipped = False

    def toggle_equip(self):
        if self.is_equipped:
            self.unequip()
        else:
            self.equip()

    def equip(self):
        old_equipment = get_equipped_in_slot(self.slot)
        if old_equipment is not None:
            old_equipment.unequip()

        self.is_equipped = True
        message(f'{self.owner.name} equipped to {self.slot}')

    def unequip(self):
        if not self.is_equipped:
            return
        self.is_equipped = False
        message(f'{self.owner.name} unequipped from {self.slot}')


def get_equipped_in_slot(slot):
    for item in equipment:
        if item.equipment.slot == slot and item.equipment.is_equipped:
            return item.equipment
    return None


def get_all_equipped():
    equipped = []
    for equip in equipment:
        if equip.equipment.is_equipped:
            equipped.append(equip.equipment)
    return equipped


# TODO: more AI options
""" Archer - Runs from the player if possible, attacks if player moves within
range or if cornered.
    Swarmer - Follows the player at a distance of 3 tiles if possible, moves in
to attack when there are three or more swarmers nearby.
    Wizard - Charges up and casts spells at the player, does not move?
"""


class BasicMonster:
    """AI for simple monsters.

    If the player can see the monster, the monster will chase the player
    and attack.
    Basic monster will attack any allies or the player based on who has the most
    HP remaining.
    """

    def take_turn(self):
        monster = self.owner

        if (monster.x, monster.y) in visible_tiles :
            target = player
            if self.owner.closest_monster(4) is not None:
                other = self.owner.closest_monster(4)
                if (other.name == 'Your ally'
                        and other.fighter.hp >= player.fighter.hp):
                    target = other

            if monster.distance_to(target) >= 2:
                monster.move_towards(target.x, target.y)
            elif player.fighter.hp > 0:
                monster.fighter.attack(target)


class Behemoth:
    """AI for Behemoth-style monsters

    If the player comes within a few tiles of the creature, it will follow
    and attack the player. Otherwise it will remain still.
    Behemoths pay no heed to allies.
    """

    def __init__(self):
        # Behemoth has a 3 starburst danger zone
        #                                (0, -3),
        #            (-2, -2), (-1, -2), (0, -2), (+1, -2), (+2, -2),
        #            (-2, -1), (-1, -1), (0, -1), (+1, -1), (+2, -1),
        #  (-3,  0), (-2,  0), (-1,  0),          (+1,  0), (+2,  0), (+3,  0),
        #            (-2, +1), (-1, +1), (0, +1), (+1, +1), (+2, +1),
        #            (-2, +2), (-1, +2), (0, +2), (+1, +2), (+2, +2),
        #                                (0, +3)
        self.aura = [
                                       (0, -3),
                   (-2, -2), (-1, -2), (0, -2), (+1, -2), (+2, -2),
                   (-2, -1), (-1, -1), (0, -1), (+1, -1), (+2, -1),
         (-3,  0), (-2,  0), (-1,  0),          (+1,  0), (+2,  0), (+3,  0),
                   (-2, +1), (-1, +1), (0, +1), (+1, +1), (+2, +1),
                   (-2, +2), (-1, +2), (0, +2), (+1, +2), (+2, +2),
                                       (0, +3)
        ]

    def danger_zone(self):
        if (self.owner.x, self.owner.y) in visible_tiles:

            con.draw_char(self.owner.x, self.owner.y,
                          self.owner.char, self.owner.color)

            for tx, ty in self.aura:
                if not is_blocked(self.owner.x + tx, self.owner.y + ty) and \
                        field[self.owner.x + tx][self.owner.y + ty].explored:
                    con.draw_char(self.owner.x + tx, self.owner.y + ty, None,
                                  fg=None, bg=colors.light_flame)

    def draw(self):
        # Dislpay this entity if it is in the player's FOV
        # Some entities are 'always visible' after they've been found
        if (self.owner.x, self.owner.y) in visible_tiles or \
                (self.owner.always_visible and
                 field[self.owner.x][self.owner.y].explored):
            con.draw_char(self.owner.x, self.owner.y,
                          self.owner.char, self.owner.color)

    # TODO: fix this death_func shit so behemoths have their own death_func
    # instead of this nonsense
    def death(self, monster):
        monster.draw = self.draw
        message(f'{monster.name.capitalize()} is slain!')
        monster.name = f'what remains of {monster.name}'
        monster.char = '%'
        monster.color = colors.dark_red
        monster.send_to_back()
        monster.blocks = False
        monster.fighter = None
        monster.ai = None

    def take_turn(self):
        self.owner.draw = self.danger_zone
        self.owner.fighter.death_func = self.death

        monster = self.owner
        if (monster.x, monster.y) in visible_tiles:

            if monster.distance_to(player) > 3:
                pass
            elif monster.distance_to(player) >= 2:
                monster.move_smart(player.x, player.y)
            elif player.fighter.hp > 0:
                monster.fighter.attack(player)


# TODO: Allies should maybe be in a special list?
# TODO: Limited number of allies? - probably in enthrall()
# TODO: Ally command states - passive, aggressive, defensive
# TODO: display ally stats - maybe under a?
class Ally:
    """AI for allied monsters

    This monster will attack nearby enemy monsters.
    If there are no enemies, it will follow the player instead.
    Ally stats are boosted 25% above normal
    """

    def take_turn(self):
        ally = self.owner
        enemy = self.owner.closest_monster(5)
        if enemy is not None:
            if ally.distance_to(enemy) >= 2:
                ally.move_smart(enemy.x, enemy.y)
            else:
                ally.fighter.attack(enemy)
        else:
            if ally.distance_to(player) >= 2:
                ally.move_smart(player.x, player.y)


# # Spells and Items # #
# TODO: MOAR spells and items!
""" Push - force enemies away from the player
    a-z targeting for aggressive spells
    summon familiar - summons a spirit to fight by your side for one floor
    some way to heal your allies"""


def enthrall():
    """Item module for enthralling the nearest monster

    The nearest monster enters the service of the player
    """

    target = player.closest_monster(5)
    if target is None:
        return 'cancel'

    target.ai = Ally()
    target.ai.owner = target
    message(f'The {target.name} is now your ally!', colors.gold)
    target.name = 'Your ally'
    target.color = colors.gold
    target.fighter.base_max_hp = int(1.25 * target.fighter.max_hp)
    target.fighter.hp = target.fighter.max_hp
    target.fighter.base_power = int(round(target.fighter.power * 1.25))
    target.fighter.base_defense = int(round(target.fighter.defense * 1.25))
    target.send_to_back()


def healing(hp_lower, hp_upper, mp_cost):
    """Item and spell module for restoring player HP

    Keyword Arguments:
    hp_lower -(int)- lower limit of healing
    hp_upper -(int)- upper limit of healing
    mp_cost -(int)- the amount of mp required to cast the spell
    """

    if player.fighter.hp == player.fighter.max_hp:
        message('You don\'t need to recover any HP', colors.yellow)
        return 'cancel'

    if player.fighter.mp < mp_cost:
        message(f'Your spell fizzles. You need at least {mp_cost} MP.',
                colors.yellow)
        return 'cancel'

    player.fighter.mp -= mp_cost

    heal_amount = randint(hp_lower, hp_upper)
    message(f'On a scale of 0 to {player.fighter.max_hp}, you feel...',
            colors.light_red)
    message(f'{heal_amount} better than you did.',
            colors.red)
    player.fighter.heal(heal_amount)


def magic_missile(caster, damage, mp_cost):
    """Deals damage to the nearest enemy in the FOV

    Keyword Arguments:
    caster -(Entity())- the entity who casts the spell
    damage -(int)- Amount of damage to deal to the foe
    mp_cost -(int)- the amount of mp required to cast the spell
    """

    if player.fighter.mp < mp_cost:
        message(f'Your spell fizzles. You need at least {mp_cost} MP.',
                colors.yellow)
        return 'cancel'

    monster = caster.closest_monster(fov_radius)

    if monster is None:
        message('You can\'t cast Magic Missile at the Darkness', colors.yellow)
        return 'cancel'

    player.fighter.mp -= mp_cost
    message(f'A pale blue energy violently strikes the {monster.name}!',
            colors.light_azure)
    message(f'You deal {damage} points of damage!', colors.light_blue)
    monster.fighter.take_damage(damage)


def mana_recovery(mp_lower, mp_upper):
    """Item module for restoring the player's MP

    Keyword Arguments:
    mp_lower -(int)- lower limit of mp to restore
    mp_upper -(int)- upper limit of mp to restore
    """

    if player.fighter.mp == player.fighter.max_mp:
        message("You don't need to recover any MP", colors.yellow)
        return 'cancel'

    rec_mp = randint(mp_lower, mp_upper)
    player.fighter.heal(health=0, mana=rec_mp)
    message(f'You recovered {rec_mp} MP.', colors.azure)


def teleport(ent, mp_cost) :
    """Item and spell module for teleporting the player to a random tile

    Keyword Arguments:
    ent -(Entity Instance)- the Entity to teleport somewhere
    mp_cost -(int)- the amount of mp required to cast the spell
    """

    if player.fighter.mp < mp_cost :
        message(f'Your spell fizzles. You need at least {mp_cost} MP.',
                colors.yellow)
        return 'cancel'
    else :
        player.fighter.mp -= mp_cost

    x, y = randint(0, field_width - 1), randint(0, field_height - 1)

    while is_blocked(x, y) :
        x, y = randint(0, field_width - 1), randint(0, field_height - 1)

    ent.x, ent.y = x, y
    if ent == player :
        global fov_recompute
        fov_recompute = True


def player_death(the_player):
    """Displays player's corpse and a Game Over message"""

    global game_state
    message('...and You Dead.', colors.brass)
    the_player.color = colors.dark_red
    the_player.char = 'F'
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
        return center_x, center_y

    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

    def random_tile(self):
        tilex, tiley = randint(self.x1, self.x2), randint(self.y1, self.y2)

        while is_blocked(tilex, tiley):
            tilex, tiley = randint(self.x1, self.x2), randint(self.y1, self.y2)

        return tilex, tiley


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
    # global field
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            field[x][y].blocked = False
            field[x][y].block_sight = False


def create_h_tunnel(x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        field[x][y].blocked = False
        field[x][y].block_sight = False


def create_v_tunnel(y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        field[x][y].blocked = False
        field[x][y].block_sight = False


def create_random_tunnel(room1, room2):
    thisx, thisy = room1.random_tile()
    prevx, prevy = room2.random_tile()

    if randint(0, 1):
        create_h_tunnel(prevx, thisx, prevy)
        create_v_tunnel(prevy, thisy, thisx)
    else:
        create_v_tunnel(prevy, thisy, thisx)
        create_h_tunnel(prevx, thisx, prevy)


def is_blocked(x, y):
    if field[x][y].blocked:
        return True

    for obj in objects:
        if obj.blocks and obj.x == x and obj.y == y:
            return True

    return False


def is_visible_tile(x, y):
    # global field

    if x >= field_width or x < 0:
        return False
    elif y >= field_height or y < 0:
        return False
    elif field[x][y].blocked:
        return False
    elif field[x][y].block_sight:
        return False
    else:
        return True


def make_field():
    global field
    rooms = []

    # TODO: more complex room generation?
    # TODO: minimum number of rooms?
    # TODO: new room shapes
    # TODO: Special rooms, shops, genies, etc.

    # The largest height or width of a room
    room_max = 13
    # The smallest h or w
    room_min = 5
    # Maximum number of rooms a map may generate
    room_num = 50

    # Create a 2D array of Tiles
    field = [
        [Tile(True) for _ in range(field_height)] for _ in range(field_width)]

    for r in range(room_num):
        w = randint(room_min, room_max)
        h = randint(room_min, room_max)
        x = randint(0, field_width - w - 1)
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
                prev_room = rooms[len(rooms) - 1]
                # (prevx, prevy) = rooms[len(rooms) - 1].random_tile()
            except IndexError:
                place_objects(this_room)
                rooms.append(this_room)
                continue

            # thisx, thisy = this_room.random_tile()
            create_random_tunnel(this_room, prev_room)

            # coin = randint(0, 1)
            # if coin:
            #     create_h_tunnel(prevx, thisx, prevy)
            #     create_v_tunnel(prevy, thisy, thisx)
            # else:
            #     create_v_tunnel(prevy, thisy, thisx)
            #     create_h_tunnel(prevx, thisx, prevy)

            place_objects(this_room)
            rooms.append(this_room)

    # The player starts in a random tile in a random room
    start_room = randint(0, len(rooms) - 1)
    startx, starty = rooms[start_room].random_tile()
    while is_blocked(startx, starty):
        startx, starty = rooms[start_room].random_tile()

    player.x, player.y = startx, starty

    # TODO: random stair placement?
    # The stairs are in the last room in the list
    stairs.x, stairs.y = rooms[-1].center()
    stairs.send_to_back()


def place_objects(room):
    global dungeon_level

    # Generate the monsters
    # TODO: Method for generating long dungeon escalation?
    # TODO: monster stat leveling formulae adjustment
    # exponential increase instead of linear?

    every_five = lambda base : int(dungeon_level * 0.2 + base)
    every_four = lambda base : int(dungeon_level * 0.25 + base)

    xp_gain = lambda base : base + dungeon_level * player.level / 2

    monster_dict = {
        'kobold' : {
            'ai' : BasicMonster,
            'char' : 'k',
            'color' : colors.dark_azure,
            'fighter' : {
                'hp' : every_five(6),
                'defense' : every_five(0),
                'power' : every_five(3),
                'xp' : xp_gain(30),
                'mp' : 0,
                'mag' : 0,
                'death_func' : monster_death
            },
            'name' : 'kobold',
        },
        'orc' : {
            'ai' : BasicMonster,
            'char' : 'o',
            'color' : colors.desaturated_green,
            'fighter' : {
                'hp' : every_five(12),
                'defense' : every_five(1),
                'power' : every_five(3),
                'xp' : xp_gain(40),
                'mp' : 0,
                'mag' : 0,
                'death_func' : monster_death
            },
            'name' : 'orc',
        },
        'troll' : {
            'ai' : Behemoth,
            'char' : 'T',
            'color' : colors.darker_green,
            'fighter' : {
                'hp' : every_four(15),
                'defense' : every_four(2),
                'power' : every_four(5),
                'xp' : xp_gain(50),
                'mp' : 0,
                'mag' : 0,
                'death_func' : monster_death
            },
            'name' : 'troll',
        }
    }
    monster_max = dungeon_escalation([[2, 1], [3, 4], [5, 6]])
    num_monsters = randint(0, monster_max)

    monster_chances = {'kobold' : dungeon_escalation(
                        [[100, 1], [90, 3], [84, 5], [78, 7], [60, 9]]),

                       'orc' : dungeon_escalation(
                           [[10, 3], [15, 5], [20, 7], [35, 9]]),

                       'troll' : dungeon_escalation(
                           [[1, 5], [2, 7], [5, 9]])}

    for i in range(num_monsters):
        x = randint(room.x1 + 1, room.x2 - 1)
        y = randint(room.y1 + 1, room.y2 - 1)

        if not is_blocked(x, y):
            this_monster = monster_dict[randomizer(monster_chances)]

            monster = Entity(x, y,
                             this_monster['char'],
                             this_monster['name'],
                             this_monster['color'],
                             blocks=True,
                             fighter=Fighter(**this_monster['fighter']),
                             ai=this_monster['ai']())

            objects.append(monster)

    # Generate the items

    # TODO: Add more potion variations?
    # TODO: More random potions -- like other RLs
    # TODO: random equipment -- with keywords?
    # make a method that generates stats combinations based on dungeon level
    # TODO: clean up item storage and selection
    # Would rather have a dict of dicts with more readability
    # item_dict = { heal, mana, etc }
    # randomizer(item_dict) == { 'item_name' : 'health potion', ... }
    # possibly a method for creating a random item, this section is getting big

    max_items = dungeon_escalation([[1, 1], [2, 5], [3, 10]])
    num_items = randint(0, max_items)
    item_chances = {
        'Healing Potion' : dungeon_escalation(
            [[100, 1], [90, 3], [80, 5], [70, 7], [60, 9]]),
        'Mana Potion' : dungeon_escalation(
            [[1, 1], [5, 3], [15, 5], [20, 7], [25, 9]]),
        'Magic Missile' : dungeon_escalation(
            [[1, 1], [10, 3], [15, 7]]),
        'Blink' : dungeon_escalation(
            [[1, 1], [5, 3], [10, 5], [15, 7]]),
        'Friendship' : dungeon_escalation(
            [[1, 1], [2, 5], [4, 9]]),
        'Sword' : 5,
        'Shield' : 5,
        'Staff' : 5,
        'Orb' : 5,
        'Bangle' : 5,
        'Cloak' : 5
        }

    # item_dict literal entry template
    """
    '' : {
        'item_name' : '',
        'item_char' : '',
        'item_color' : colors.,
        'item' : {
            'use_func' : ,
            'kwargs' : {}
            },
        'equipment' : {
            'slot' : '',
            'max_hp' : 0,
            'max_mp' : 0,
            'power' : 0,
            'defense' : 0,
            'magick' : 0,
            'regen' : 0
            }
        },
    """

    item_dict = {
        'Healing Potion': {
            'item_name': 'Healing Potion',
            'item_char': '!',
            'item_color': colors.light_red,
            'item': {
                'use_func': healing,
                'kwargs': {
                    'hp_lower': int(round(player.fighter.max_hp
                                    * (0.04 + player.fighter.regen * 0.011), 1)),
                    'hp_upper': int(player.fighter.max_hp
                                    * (0.12 + (player.fighter.regen * 0.01))
                                    ),
                    'mp_cost': 0
                }
            },
            'equipment': None
        },
        'Mana Potion' : {
            'item_name' : 'Mana Potion',
            'item_char' : '!',
            'item_color' : colors.light_azure,
            'item' : {
                'use_func' : mana_recovery,
                'kwargs' : {
                    'mp_lower' : int(player.fighter.max_mp * 0.05),
                    'mp_upper' : int(player.fighter.max_mp * 0.12)
                    }
                },
            'equipment' : None
            },
        'Magic Missile': {
            'item_name': 'Scroll of Magic Missile',
            'item_char': '#',
            'item_color': colors.light_blue,
            'item': {
                'use_func': magic_missile,
                'kwargs': {
                    'caster': player,
                    'damage': dungeon_level // 2 + 7,
                    'mp_cost': 0
                }
            },
            'equipment': None
            },
        'Blink' : {
            'item_name' : 'Scroll of Blink',
            'item_char' : '#',
            'item_color' : colors.light_violet,
            'item' : {
                'use_func' : teleport,
                'kwargs' : {'ent' : player,
                            'mp_cost' : 0}
                },
            'equipment' : None
            },
        'Friendship' : {
            'item_name' : 'Scroll of Friendship',
            'item_char' : '#',
            'item_color' : colors.gold,
            'item' : {
                'use_func' : enthrall,
                'kwargs' : {}
                },
            'equipment' : None
            },
        'Sword' : {
            'item_name' : f'Lv{dungeon_level - 1} Sword',
            'item_char' : 'l',
            'item_color' : colors.light_sky,
            'item' : None,
            'equipment' : {
                'slot' : 'right hand',
                'max_hp' : 0,
                'max_mp' : 0,
                'power' : int(round(dungeon_level * 1.1)),
                'defense' : 0,
                'magick' : 0,
                'regen' : 0
                }
            },
        'Shield' : {
            'item_name' : f'Lv{dungeon_level - 1} Shield',
            'item_char' : 'u',
            'item_color' : colors.light_sky,
            'item' : None,
            'equipment' : {
                'slot' : 'left hand',
                'max_hp' : 0,
                'max_mp' : 0,
                'power' : 0,
                'defense' : int(round(dungeon_level * 1.3)),
                'magick' : 0,
                'regen' : 0
                }
            },
        'Staff' : {
            'item_name' : f'Lv{dungeon_level - 1} Staff',
            'item_char' : 'Y',
            'item_color' : colors.light_sky,
            'item' : None,
            'equipment' : {
                'slot' : 'right hand',
                'max_hp' : 0,
                'max_mp' : 0,
                'power' : 0,
                'defense' : 0,
                'magick' : int(round(dungeon_level * 1.1)),
                'regen' : 0
                }
            },
        'Orb' : {
            'item_name' : f'Lv{dungeon_level - 1} Orb',
            'item_char' : 'o',
            'item_color' : colors.light_sky,
            'item' : None,
            'equipment' : {
                'slot' : 'left hand',
                'max_hp' : 0,
                'max_mp' : int(round(player.fighter.base_max_mp *
                                     (0.09 + dungeon_level * 0.01))),
                'power' : 0,
                'defense' : 0,
                'magick' : 0,
                'regen' : 0
                }
            },
        'Bangle' : {
            'item_name' : f'Lv{dungeon_level - 1} Bangle',
            'item_char' : 'c',
            'item_color' : colors.light_sky,
            'item' : None,
            'equipment' : {
                'slot' : 'accessory',
                'max_hp' : int(round(player.fighter.max_hp *
                                     (0.04 + dungeon_level * 0.01))),
                'max_mp' : 0,
                'power' : 0,
                'defense' : 0,
                'magick' : 0,
                'regen' : 0
                }
            },
        'Cloak' : {
            'item_name' : f'Lv{dungeon_level - 1} Cloak',
            'item_char' : '&',
            'item_color' : colors.light_sky,
            'item' : None,
            'equipment' : {
                'slot' : 'shoulders',
                'max_hp' : 0,
                'max_mp' : 0,
                'power' : 0,
                'defense' : 0,
                'magick' : 0,
                'regen' : int(1 + round(dungeon_level / 2))
                }
            }
        }

    for _ in range(num_items):
        x = randint(room.x1 + 1, room.x2 - 1)
        y = randint(room.y1 + 1, room.y2 - 1)

        # Do not place items on blocked areas
        if not is_blocked(x, y):
            item_chosen = item_dict[randomizer(item_chances)]

            item = Entity(x, y, item_chosen['item_char'],
                          item_chosen['item_name'],
                          item_chosen['item_color'],
                          always_visible=True,

                          item=Item(**item_chosen['item'])
                          if item_chosen['item'] is not None else None,

                          equipment=Equipment(**item_chosen['equipment'])
                          if item_chosen['equipment'] is not None else None)

            objects.append(item)
            item.send_to_back()


def random_index(chances):
    """Returns the index which matches a randomized choice

    Keyword Arguments:
        chances -(list of ints)- each int represents the likelihood of being
    chosen compared to the sum of the list"""

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
    """ Picks the pair with the highest 1th entry that is <= dungeon_level and
    returns the 0th entry in that pair or 0

    Keyword Arguments:
        table -(list)- this list must contain entries which consist of two
    values, either as tuples or lists in the order [value, level], where
    value represents that item's portion of the drop pool and
    level represents which floor to start having that likelihood"""

    for (value, level) in reversed(table):
        if dungeon_level >= level:
            return value
    return 0


def next_level():
    global dungeon_level, fov_recompute, objects

    fov_recompute = True
    dungeon_level += 1
    objects = [player, stairs]

    regen_hp, regen_mp = player_regen()
    player.fighter.heal(health=regen_hp, mana=regen_mp)

    message('During a calm moment, you find time to rest...', colors.white)
    message(f'You regained {regen_hp} hp.', colors.light_red)
    message(f'You regained {regen_mp} mp.', colors. light_blue)
    message('Back to work...', colors.chartreuse)

    con.clear(fg=colors.black, bg=colors.black)
    root.clear(fg=colors.black, bg=colors.black)
    make_field()


# # # # # # # # # # # # # # # # # # # #
#   Player Interaction
# # # # # # # # # # # # # # # # # # # #


def player_regen():
    """ The player regenerates health and mana between each floor

    [HP(MP)_MAX] * (14% + [REG%])
    """

    regen_hp = int(player.fighter.max_hp
                   * (0.14 + (player.fighter.regen * 0.01)))
    regen_mp = int(player.fighter.max_mp
                   * (0.14 + (player.fighter.regen * 0.01)))

    return regen_hp, regen_mp


def cast_spell():
    if len(player.spells) == 0:
        spell_menu = ["You don't know any spells"]
    else:
        spell_menu = [s for s in player.spells]

    spell = menu("Choose a spell to cast\n",
                 spell_menu,
                 spell_width)

    if spell is None or len(player.spells) == 0:
        return 'cancel'
    elif player.spells[spell] == 'Magic Missile':
        magic_missile(caster=player, damage=int(player.fighter.mag * 0.5),
                      mp_cost=5)

    elif player.spells[spell] == 'Minor Heal':
        healing(hp_lower=int(player.fighter.mag * 0.25),
                hp_upper=int(player.fighter.mag * 0.75),
                mp_cost=3)
    elif player.spells[spell] == 'Blink':
        teleport(ent=player,
                 mp_cost=2)

    else:
        return 'cancel'


adv_hp_count = 0
adv_mp_count = 0
adv_str_count = 0
adv_mag_count = 0


def check_level_up():
    global adv_hp_count, adv_mp_count, adv_str_count, adv_mag_count

    level_up_xp = level_up_base + player.level * level_up_factor

    if player.fighter.xp >= level_up_xp:
        player.level += 1
        player.fighter.xp -= level_up_xp
        message('You feel stronger!', colors.yellow)

        # Scaling stat advancement

        # HP
        adv_hp = (player.fighter.base_max_hp * 0.15) - (adv_hp_count * 0.005)
        if adv_hp < player.fighter.base_max_hp * 0.04:
            adv_hp = int(player.fighter.base_max_hp * 0.04)
        else:
            adv_hp = int(adv_hp)

        # MP
        adv_mp = (player.fighter.base_max_mp * 0.2) - (adv_mp_count * 0.0075)
        if adv_mp < player.fighter.base_max_mp * 0.04:
            adv_mp = int(player.fighter.base_max_mp * 0.04)
        else:
            adv_mp = int(adv_mp)

        # TODO: Better formula for str & mag advancement?
        # STR
        adv_str = 2 if adv_str_count % 2 == 0 else 1

        # MAG
        adv_mag = 2 if adv_mag_count % 2 == 0 else 1

        # TODO: def & reg formulae?

        choice_list = [f'HP : {player.fighter.base_max_hp} (+ {adv_hp})',
                       f'MP : {player.fighter.base_max_mp} (+ {adv_mp})',
                       f'STR: {player.fighter.base_power} (+ {adv_str})',
                       f'MAG: {player.fighter.base_mag} (+ {adv_mag})',
                       f'DEF: {player.fighter.base_defense} (+ 1)',
                       f'REG: {player.fighter.base_regen} (+ 1)']

        # Add available skills and spells
        if player.level >= 2 and 'Minor Heal' not in player.spells:
            choice_list.append('Minor Heal')
        if player.level >= 5 \
                and 'Magic Missile' not in player.spells \
                and 'Blink' not in player.spells:
            choice_list.append('Magic Missile')
            choice_list.append('Blink')
        elif player.level >= 7 \
                and 'Magic Missile' not in player.spells:
            choice_list.append('Magic Missile')
        elif player.level >= 7 \
                and 'Blink' not in player.spells:
            choice_list.append('Blink')

        choice = 'cancel'
        while choice is 'cancel':
            choice = menu('Promotion Get!\n',
                          choice_list,
                          level_up_width)

            if choice == 0:
                player.fighter.base_max_hp += adv_hp
                player.fighter.hp += adv_hp
                adv_hp_count += 1
            elif choice == 1:
                player.fighter.base_max_mp += adv_mp
                player.fighter.mp += adv_mp
                adv_mp_count += 1
            elif choice == 2:
                player.fighter.base_power += adv_str
                adv_str_count += 1
            elif choice == 3:
                player.fighter.base_mag += adv_mag
                adv_mag_count += 1
            elif choice == 4:
                player.fighter.base_defense += 1
            elif choice == 5:
                player.fighter.base_regen += 1
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

    global fov_recompute, game_state
    # global mouse_coord

    user_input = tdl.event.key_wait()

    # esc : quit
    if user_input.key == 'ESCAPE':
        return 'exit'

    # TODO: do we even need the play and dead states?
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

        # TODO: Ultimate Thumb Attack?
        elif user_input.key == 'SPACE':
            message('You twiddle your thumbs')

        # s : cast a spell
        elif user_input.char == 's':
            if cast_spell() == 'cancel':
                return 'no-turn'

        # i : use an item from inventory
        elif user_input.char == 'i':
            chosen_item = inventory_menu(
                'Choose an item to use, esc to cancel\n', inventory)
            if chosen_item != 'cancel' :
                chosen_item.use()
            else:
                return 'no-turn'
        elif user_input.char == 'e':
            chosen_item = inventory_menu(
                'Equipment\n', equipment)
            if chosen_item != 'cancel':
                chosen_item.use()
            else:
                return 'no-turn'

        # actions which do not consume a turn
        else:
            # \ : descend to the next level
            if user_input.char == '.':
                if player.x == stairs.x and player.y == stairs.y:
                    next_level()

            # shift : pick up item beneath player
            elif user_input.key == 'SHIFT':
                for item in objects:
                    if item.x == player.x and item.y == player.y and item.item:
                        item.item.pick_up()
                        break

            # o : drop an item from inventory
            elif user_input.char == 'o':
                chosen_item = inventory_menu(
                    'Choose an item to drop, esc to cancel\n', inventory)
                if chosen_item is not 'cancel':
                    chosen_item.drop()

            # r : drop an item from equipment
            elif user_input.char == 'r':
                chosen_equip = inventory_menu(
                    'Choose an item to drop, esc to cancel\n', equipment)
                if chosen_equip is not 'cancel':
                    chosen_equip.drop()

            return 'no-turn'


def inventory_menu(header, inv=[]):
    """Displays the character's inventory as a selectable menu
    Returns the index of the item selected
    Returns 'cancel' if no selection or no items
    """

    if len(inv) == 0:
        options = ['Nothing to see here']
    else:
        options = [item.name for item in inv]

    index = menu(header, options, inventory_width)

    if index is 'cancel' or len(inv) == 0:
        return 'cancel'
    return inv[index].item


def get_notable_feature(equip):
    notable_feature = None
    stats = {
        'MAX HP': equip.equipment.max_hp,
        'MAX MP': equip.equipment.max_mp,
        'STR': equip.equipment.power,
        'MAG': equip.equipment.magick,
        'DEF': equip.equipment.defense,
        'REG': equip.equipment.regen
    }

    notable_feature = max(stats, key= lambda key: stats[key])

    return f'{notable_feature}: {stats[notable_feature]}'


def menu(header, options, width):
    """Creates a menu screen which is displayed over the main game
    Returns the index of the option selected
    """

    if len(options) > 26:
        raise ValueError('Cannot have more than 26 options')

    header_wrapped = []
    for header_line in header.splitlines():
        header_wrapped.extend(textwrap.wrap(header_line, width - 2))
    header_height = len(header_wrapped)
    height = len(options) + header_height + 2

    window = tdl.Console(width, height)
    window.draw_rect(0, 0, width, height, None, bg=colors.dark_gray)
    for i, line in enumerate(header_wrapped):
        window.draw_str(1, 0+i, header_wrapped[i], fg=colors.light_gray)

    y = header_height + 1
    letter_index = ord('a')
    try:
        if options[0] == equipment[0].name:
            for i, option in enumerate(options):
                text = f'({chr(letter_index)}) {option} ' \
                       f'({get_notable_feature(equipment[i])})'
                window.draw_str(0, y, text, fg=colors.white, bg=None)
                y += 1
                letter_index += 1
        else:
            for option in options :
                text = f'({chr(letter_index)}) {option}'
                window.draw_str(0, y, text, fg=colors.white, bg=None)
                y += 1
                letter_index += 1
    except IndexError:
        for option in options:
            text = f'({chr(letter_index)}) {option}'
            window.draw_str(0, y, text, fg=colors.white, bg=None)
            y += 1
            letter_index += 1

    x = screen_width // 2 - width // 2
    y = screen_height // 2 - height // 2
    root.blit(window, x, y, width, height, 0, 0)

    tdl.flush()

    # This usually catches a text type event
    key = tdl.event.key_wait()
    # So we wait for the next non-text event
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

    new_msg_lines = textwrap.wrap(new_msg, panel_width)

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
    for obj in objects:
        if obj.fighter and obj.x == x and obj.y == y:
            target = obj
            break

    if target is not None:
        # If target is your ally, swap places with it
        if target.name == 'Your ally' :
            player.x, target.x = target.x, player.x
            player.y, target.y = target.y, player.y
        # Attack otherwise
        else:
            player.fighter.attack(target)

    # Move there if there's no target
    else:
        player.move(dx, dy)
        fov_recompute = True


def render_bar(x, y, total_width, name, value, maximum,
               bar_color, bg_color, text_color):
    """Render a bar which visually represents some stat
    and draw it to the `panel` HUD element"""

    bar = int(float(value) / maximum * total_width)

    panel.draw_rect(x, y, total_width, 1, None, bg=bg_color)

    if bar > 0:
        panel.draw_rect(x, y, bar, 1, None, bg=bar_color)

    text = f'{name}: {str(value)} / {str(maximum)}'
    x_centered = x + (total_width - len(text)) // 2
    panel.draw_str(x_centered, y, text, fg=text_color, bg=None)


def render_stat(x, y, name, base_stat, stat) :
    if base_stat < stat :
        color = colors.light_green
    else :
        color = colors.white

    panel.draw_str(x, y, f'{name}:', bg=None, fg=colors.white)
    panel.draw_str(x + 4, y, str(stat), bg=None, fg=color)


def render_all():
    """render everything to the screen"""

    global fov_recompute, visible_tiles

    # Write the background
    root.blit(background)

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

            # If this tile is not in the player's FOV
            if not visible:
                # Display it as dark if they've been there
                if field[x][y].explored:
                    if wall:
                        con.draw_char(x, y, None, fg=None, bg=c_dark_wall)
                    else:
                        con.draw_char(x, y, None, fg=None, bg=c_dark_gnd)
                # # Uncomment this block to see the map outline
                # if wall :
                #     con.draw_char(x, y, None, fg=None, bg=c_dark_wall)
                # else :
                #     con.draw_char(x, y, None, fg=None, bg=c_dark_gnd)

            # If this tile is in the player;s FOV
            else:
                # Display it as a lit area
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
    root.blit(con, 1, 1, screen_width, screen_height, 0, 0)

    # Clear the GUI `panel`
    panel.clear(fg=colors.white, bg=colors.black)

    # Render messages
    messages.clear()
    y = 0
    for (line, color) in game_msgs:
        messages.draw_str(0, y, line, bg=None, fg=color)
        y += 1

    # Blit the message panel to `root`
    root.blit(messages, field_width + 2, 1)
    # Re-render the stats displays

    # Monster under mouse
    # panel.draw_str(1, 0, get_names_under_mouse(),
    #                bg=None, fg=colors.light_gray)

    # Player's HP
    render_bar(1, 1, bar_width, 'HP', player.fighter.hp, player.fighter.max_hp,
               colors.light_red, colors.darker_red, colors.white)

    # Player's MP
    render_bar(1, 3, bar_width, 'MP', player.fighter.mp, player.fighter.max_mp,
               colors.light_blue, colors.darker_red, colors.white)

    # Dungeon Level
    panel.draw_str(panel_width - 11, panel_height - 2,
                   f'Floor: {dungeon_level}', bg=colors.white, fg=colors.black)

    # STR
    render_stat(1, 5, 'STR',
                player.fighter.base_power, player.fighter.power)

    # MAG
    render_stat(1, 7, 'MAG',
                player.fighter.base_mag, player.fighter.mag)

    # DEF
    render_stat(1, 9, 'DEF',
                player.fighter.base_defense, player.fighter.defense)

    # REG
    render_stat(1, 11, 'REG',
                player.fighter.base_regen, player.fighter.regen)

    # Player Level & XP
    render_bar(1, panel_height - 2, bar_width, f'Lv{player.level}',
               int(player.fighter.xp),
               level_up_base + player.level * level_up_factor,
               colors.light_violet, colors.desaturated_violet, colors.white)

    # Blit the newly rendered bars to `root`
    root.blit(panel, panel_x, panel_y, screen_width, panel_height, 0, 0)


# FPS
# irrelevant in turn-based, but not harmful
fps_limit = 20
tdl.setFPS(fps_limit)

# Screen size
screen_width = 100
screen_height = 60

# Field size
field_width = 60
field_height = screen_height - 2

# # HUD settings
panel_width = screen_width - field_width - 3
# Messages
msg_height = int(screen_height * 0.59)
game_msgs = []
# Stats
bar_width = 20
panel_height = screen_height - msg_height - 3
panel_x = field_width + 2
panel_y = msg_height + 2
# Menus
inventory_width = 40
level_up_width = 20
spell_width = 30

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
root = tdl.init(screen_width, screen_height,
                title="giraffelike", fullscreen=False)

# & Game field
con = tdl.Console(field_width, field_height)

# & Message Box
messages = tdl.Console(panel_width, msg_height)

# & Stats panel
panel = tdl.Console(panel_width, panel_height)

# & bg
background = tdl.Console(screen_width, screen_height)
background.draw_rect(0, 0, screen_width, screen_height, ' ',
                     bg=colors.darker_gray)

# Create the player object
fighter_mod = Fighter(hp=50, defense=1, power=5, xp=0,
                      mp=15, mag=5, regen=1, death_func=player_death)
player = Entity(
    0, 0, '@', 'player', colors.white, blocks=True,
    fighter=fighter_mod)

# Player settings
equipment = []
inventory = []
player.spells = []
level_up_base = 200
level_up_factor = 150
level_screen_width = 40
# mouse_coord = (0, 0)
player_action = None
player.level = 1

# initialize the field
dungeon_level = 1
fov_recompute = True
stairs = Entity(1, 1, '>', 'stairs', colors.white,
                always_visible=True)
objects = [player, stairs]
make_field()

# Welcome message
message('Welcome to the Warehouse, nerd.', colors.red)

game_state = 'play'
while not tdl.event.is_window_closed():
    render_all()
    tdl.flush()

    check_level_up()

    for thing in objects:
        thing.clear()

    player_action = handle_keys()

    # Quit on esc
    if player_action == 'exit':
        break

    # # Actions which only happen after the player acts
    # Monsters' turn
    if game_state == 'play' and player_action != 'no-turn':
        player_regen()
        for thing in objects:
            if thing.ai:
                thing.ai.take_turn()
