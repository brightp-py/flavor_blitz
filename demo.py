import json
import random

from attack import ATTACK

with open("char.json", 'r', encoding = 'utf-8') as file:
    json_data = json.load(file)

with open("food.json", 'r', encoding = 'utf-8') as file:
    food_data = json.load(file)


class Player:

    def __init__(self, deck: list):
        self.deck = deck
        self.hand = []
        self.discard = []

        random.shuffle(self.deck)

        self.health = 100
        self.dfn = 100

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
    
    def switch_l(self):
        self.char_l, self.char_c = self.char_c, self.char_l
        if self.char_l is not None:
            self.char_l.pos = 'l'
        if self.char_c is not None:
            self.char_c.pos = 'c'
    
    def switch_r(self):
        self.char_r, self.char_c = self.char_c, self.char_r
        if self.char_r is not None:
            self.char_r.pos = 'r'
        if self.char_c is not None:
            self.char_c.pos = 'c'
    
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
    
    def draw(self):
        self.hand.append(self.deck[0])
        del self.deck[0]
    
    def attachFood(self, food, character):
        assert food in self.hand
        self.hand.remove(food)
        character.unlockFood()
        character.attachFood(food)
        # if food not in character.food:
        #     character.food[food] = 0
        # character.food[food] += 1
    
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
    
    def discardCharacter(self, char):
        self.discard.append(char.ident)
        if char.pos == 'l':
            self.char_l = None
        elif char.pos == 'r':
            self.char_r = None
        elif char.pos == 'c':
            self.char_c = None
        # del char
    
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

    def canAttack(self, secondary = False):
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
        print(f"Dealt {str(damage)} damage!")
        return damage

if __name__ == "__main__":
    sour_base = {
        "LemonGuard": 2,
        "LemonTurret": 2,
        "LemonBard": 2,
        "sour": 6
    }

    savory_base = {
        "MushroomNavy": 2,
        "ScuffedMushroom": 2,
        "ToughMushroom": 2,
        "savory": 6
    }

    sweet_base = {
        "PeachBabe": 2,
        "PeachCobbler": 2,
        "PeachWisp": 2,
        "sweet": 6
    }

    deck1 = []
    for card, count in (sweet_base | sour_base).items():
        deck1 += [card] * count
    
    deck2 = []
    for card, count in (sweet_base | savory_base).items():
        deck2 += [card] * count
    
    player1 = Player(deck1)
    player2 = Player(deck2)

    player1.hand.append("001lemonguard")
    player1.playCharacter("001lemonguard", 'l')
    print(str(player1.char_l))
    player1.hand.append("sour")
    player1.attachFood("sour", player1.char_l)
    print(str(player1.char_l))
    print(player1.char_l.canAttack())
    player1.attack(player1.char_l, player2)
    print(player2.health)
