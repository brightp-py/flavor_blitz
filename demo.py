import json
import random
import numpy as np

from attack import ATTACK

with open("char.json", 'r', encoding = 'utf-8') as file:
    json_data = json.load(file)

with open("food.json", 'r', encoding = 'utf-8') as file:
    food_data = json.load(file)


class Player:
    SCORE_MOD = np.array([
        1, 2, -1, 1000, 10,
        25, 10, 10, 50, 2, -1, 2, -1,
        25, 10, 10, 50, 2, -1, 2, -1,
        25, 10, 10, 50, 2, -1, 2, -1
    ])

    def __init__(self, deck: list):
        self.deck = deck
        self.hand = []
        self.discard = []

        self.deck_size = len(deck)
        random.shuffle(self.deck)

        self.health = 100
        self.dfn = 100

        self.movementCooldown = False

        self.char_l = None
        self.char_c = None
        self.char_r = None
    
    def __str__(self):
        lines = [
            f"Health: {str(self.health)}",
            f"Hand: {str(len(self.hand))}",
            f"Deck: {str(len(self.deck))}"
        ]
        
        return '\n'.join(lines)

    def copy(self):
        res = Player(self.deck[:])

        res.deck = self.deck[:]
        res.hand = self.hand[:]
        res.discard = self.discard[:]

        res.deck_size = self.deck_size

        res.health = self.health
        res.dfn = self.health

        res.movementCooldown = self.movementCooldown

        res.char_l = None if self.char_l is None else self.char_l.copy()
        res.char_c = None if self.char_c is None else self.char_c.copy()
        res.char_r = None if self.char_r is None else self.char_r.copy()

        return res
    
    def asArray(self):
        res = np.zeros(29)

        res[:5] = np.array([
            len(self.deck) / self.deck_size,
            len(self.hand) / self.deck_size,
            len(self.discard) / self.deck_size,
            self.health / 100,
            self.dfn / 100
        ])

        for char, i in zip((self.char_l, self.char_c, self.char_r),
                           (5, 13, 21)):
            if char is not None:
                # print(char)
                res[i] = 1
                res[i+1:i+8] = char.asArray()
        
        # res[5] = 0 if self.char_l is None else 1
        # res[13] = 0 if self.char_c is None else 1
        # res[21] = 0 if self.char_r is None else 1

        # res[6:13] = self.char_l.data()
        # res[14:21] = self.char_l.data()
        # res[22:29] = self.char_l.data()

        return res

    def score(self):
        return np.sum(self.asArray() * self.SCORE_MOD)

    def charAt(self, pos):
        if pos == 'l':
            return self.char_l
        if pos == 'c':
            return self.char_c
        return self.char_r
    
    def rotate(self):
        self.char_l, self.char_c, self.char_r = (
            self.char_r, self.char_l, self.char_c
        )
        if self.char_r is not None:
            self.char_r.pos = 'r'
        if self.char_l is not None:
            self.char_l.pos = 'l'
        if self.char_c is not None:
            self.char_c.pos = 'c'
        self.movementCooldown = True
    
    def switch_l(self):
        self.char_l, self.char_c = self.char_c, self.char_l
        if self.char_l is not None:
            self.char_l.pos = 'l'
        if self.char_c is not None:
            self.char_c.pos = 'c'
        self.movementCooldown = True
    
    def switch_r(self):
        self.char_r, self.char_c = self.char_c, self.char_r
        if self.char_r is not None:
            self.char_r.pos = 'r'
        if self.char_c is not None:
            self.char_c.pos = 'c'
        self.movementCooldown = True
    
    # def refund(self, character, cost = None):
        # if cost is None:
        #     cost = character.food
        
        # for flavor, count in cost.items():
        #     self.hand.extend([flavor] * count)
        #     character.food[flavor] -= count
            # if character.food[flavor] <= 0:
            #     del character.food[flavor]
        
    def refund(self, character):
        self.hand.extend(food.ident for food in character.food_basic)
        self.hand.extend(food.ident for food in character.food_complex)
        character.food_basic = []
        character.food_complex = []
        self.movementCooldown = False
    
    def attack(self, attacker, opponent, secondary = False):
        attack_func = attacker.attack1
        if secondary:
            attack_func = attacker.attack2
        
        if attacker == self.char_l:
            defender = opponent.char_r
        elif attacker == self.char_r:
            defender = opponent.char_l
        else:
            defender = opponent.char_c

        attack_func(attacker, defender, self, opponent)
        # self.refund(attacker, attack_func.cost)
        self.hand.extend(attacker.applyAttackCost(secondary))
        self.movementCooldown = False
    
    def draw(self):
        if len(self.deck) == 0:
            self.health = 0
            return
        self.hand.append(self.deck[0])
        del self.deck[0]
        self.movementCooldown = False
    
    def attachFood(self, food, character):
        assert food in self.hand
        self.hand.remove(food)
        character.unlockFood()
        character.attachFood(food)
        # if food not in character.food:
        #     character.food[food] = 0
        # character.food[food] += 1
        self.movementCooldown = False
    
    def playCharacter(self, char_id, position):
        assert position in ('l', 'c', 'r')
        assert char_id in self.hand

        character = Character.fromJson(char_id, position)
        
        if position == 'l':
            self.char_l = character
        elif position == 'r':
            self.char_r = character
        else:
            self.char_c = character
        
        self.hand.remove(char_id)
        self.movementCooldown = False
    
    def discardCharacter(self, char):
        self.discard.append(char.ident)
        if char.pos == 'l':
            self.char_l = None
        elif char.pos == 'r':
            self.char_r = None
        elif char.pos == 'c':
            self.char_c = None
        # del char
        self.movementCooldown = False
    
    def takeDamage(self, damage):
        self.health -= damage
    
    def heal(self, healing):
        self.health += healing
        if self.health > 100:
            self.health = 100
    
    def endTurn(self):
        if self.char_l is not None:
            if self.char_l.health <= 0:
                print('l dead')
                self.discardCharacter(self.char_l)
            else:
                self.char_l.unlockFood()
        
        if self.char_r is not None:
            if self.char_r.health <= 0:
                print('r dead')
                self.discardCharacter(self.char_r)
            else:
                self.char_r.unlockFood()
        
        if self.char_c is not None:
            if self.char_c.health <= 0:
                print('c dead')
                self.discardCharacter(self.char_c)
            else:
                self.char_c.unlockFood()


class Food:
    IND2FLAV = ("sour", "sweet", "savory", "bitter", "spicy")
    FLAV2IND = {val: ind for ind, val in enumerate(IND2FLAV)}

    def __init__(self, flavor):
        self.ident = flavor
        self.name = flavor.capitalize()
        self.first = flavor
        
        self.bits = [0] * 5
        self.bits[Food.FLAV2IND[self.first]] = 1
        self.binary = tuple(self.bits)
    
    def __str__(self):
        return self.first.capitalize()
    
    def getTuple(self):
        return self.binary


class DoubleFood(Food):

    def __init__(self, ident, name, flavor1, flavor2):
        Food.__init__(flavor1)
        self.ident = ident
        self.name = name
        self.second = flavor2

        self.bits[Food.FLAV2IND[self.second]] = 1
        self.binary = tuple(self.bits)
    
    @staticmethod
    def fromData(ident, data):
        name = data['name']
        first = data['first']
        second = data['second']
        # trigger = data['trigger']
        # desc = data['desc']
        return DoubleFood(ident, name, first, second)

    def __str__(self):
        return self.name


class Character:

    def __init__(self, data: dict, ident: str, position: str):
        self.__dict__ |= data
        self.data = data
        self.ident = ident
        self.pos = position

        self.base_atk = self.atk
        self.base_dfn = self.dfn
        self.base_hp = self.health

        self.attack1 = Attack(self.attack1)
        if "attack2" in data:
            self.attack2 = Attack(self.attack2)
        else:
            self.attack2 = None
        
        self.locked_food = None
        self.lock_time = 0
        self.food_basic = []
        self.food_complex = []

    @staticmethod
    def fromJson(json_id: str, position: str):
        data = json_data[json_id]
        return Character(data, json_id, position)

    def __str__(self):
        lines = [
            self.name + " | " + str(self.health),
            f"{str(self.atk)} ATK | {str(self.dfn)} DFN",
            # ', '.join(f"{flav.capitalize()}: {c}"
            #         for flav, c in self.food.items())
            ', '.join(map(str, self.food_basic + self.food_complex))
        ]
        if self.locked_food is not None:
            lines[0] += f" | [{self.locked_food.name}]"
        return '\n'.join(lines)

    def copy(self):
        res = Character(self.data, self.ident, self.pos)

        res.atk = self.atk
        res.dfn = self.dfn
        res.base_hp = self.base_hp
        res.health = self.health

        res.locked_food = self.locked_food
        res.lock_time = self.lock_time
        res.food_basic = self.food_basic[:]
        res.food_complex = self.food_complex[:]

        return res
    
    def asArray(self):
        res = np.array([self.atk, self.dfn, self.health, 0.0, 0.0, 0.0, 0.0])
        res /= 100.0

        res[4] = sum(self.canAttack(False, True))
        if res[4] == 0:
            res[3] = 1
        
        if self.attack2 is not None:
            res[6] = sum(self.canAttack(True, True))
            if res[6] == 0:
                res[5] = 1
        
        return res

    def print(self):
        print(str(self))
    
    def takeDamage(self, damage):
        self.health -= damage
    
    def healCapped(self, healing):
        if self.health >= self.base_hp:
            return healing
        
        self.health += healing
        if self.health > self.base_hp:
            excess = self.health - self.base_hp
            self.health = self.base_hp
            return excess

        return 0
    
    def attachFood(self, food_name):
        if food_name in Food.FLAV2IND:
            self.locked_food = Food(food_name)
        else:
            data = food_data[food_name]
            self.locked_food = DoubleFood.fromData(data)
        self.lock_time = 2
    
    def attackCost(self, attack):
        cost = [attack.cost[flav] if flav in attack.cost else 0
                for flav in Food.IND2FLAV]

        if self.locked_food is not None:
            for flav, amount in enumerate(self.locked_food.getTuple()):
                if cost[flav] > 0:
                    cost[flav] -= amount
        
        return cost

    def canAttack(self, secondary = False, returnCost = False):
        if secondary and self.attack2 is None:
            return False
        
        attack = self.attack2 if secondary else self.attack1
        cost = self.attackCost(attack)

        for food in self.food_basic:
            i = Food.FLAV2IND[food.first]
            cost[i] -= 1
        
        for food in self.food_complex:
            i = Food.FLAV2IND[food.first]
            j = Food.FLAV2IND[food.second]
            cost[i] -= 1
            cost[j] -= 1
        
        if returnCost:
            return [(0 if flav < 0 else flav) for flav in cost]
        
        return all(flav <= 0 for flav in cost)

        # for flavor, count in attack.cost.items():
        #     if flavor not in self.food or self.food[flavor] < count:
        #         return False
        # return True
    
    def applyAttackCost(self, secondary = False):
        attack = self.attack2 if secondary else self.attack1
        cost = self.attackCost(attack)

        refund = []
        keep_basic = []
        keep_complex = []

        for food in self.food_basic[::-1]:
            i = Food.FLAV2IND[food.first]
            if cost[i] > 0:
                cost[i] -= 1
                refund.append(food.ident)
            else:
                keep_basic.append(food)
        
        if all(flav <= 0 for flav in cost):
            self.food_basic = keep_basic[::-1]
            return refund
        
        layer = {tuple(cost)}
        for food in self.food_complex[::-1]:
            nlayer = set()
            i = Food.FLAV2IND[food.first]
            j = Food.FLAV2IND[food.second]
            for branch in layer:
                if branch[i] > 0:
                    nbranch = branch[:i] + (branch[i] - 1,) + branch[i+1:]
                    nlayer.add(nbranch)
                if branch[j] > 0:
                    nbranch = branch[:j] + (branch[j] - 1,) + branch[j+1:]
                    nlayer.add(nbranch)
            if nlayer:
                layer = nlayer
                refund.append(food.ident)
            else:
                keep_complex.append(food)
        
        self.food_basic = keep_basic[::-1]
        self.food_complex = keep_complex[::-1]
        return refund

    def unlockFood(self):
        if self.locked_food is None:
            return
        
        if self.lock_time > 0:
            self.lock_time -= 1
            return
        
        if isinstance(self.locked_food, DoubleFood):
            self.food_complex.append(self.locked_food)
        else:
            self.food_basic.append(self.locked_food)

        self.locked_food = None


class Attack:
    
    def __init__(self, data: dict):
        self.__dict__ |= data

        if "id" in data:
            self.call = ATTACK[self.id]
        else:
            self.call = None
    
    def __call__(self, *args, **kwargs):
        if self.call is None:
            self.basic(*args, **kwargs)
        else:
            self.call(self, *args, **kwargs)
    
    def basic(self, attacker, defender, _, opponent):
        atk = attacker.atk

        if defender is None:
            defender = opponent
        
        dfn = defender.dfn
        ratio = (50 + atk) / (50 + dfn)
        damage = int(self.power * ratio)
        if damage < 1:
            damage = 1
        defender.takeDamage(damage)
        # if not self.quiet_attacks:
            # print(f"Dealt {str(damage)} damage!")
        return damage
