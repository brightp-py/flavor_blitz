import json

from attack import ATTACK

with open("char.json", 'r', encoding = 'utf-8') as file:
    json_data = json.load(file)


class Player:

    def __init__(self, deck: list):
        self.deck = deck
        self.hand = []
        self.discard = []

        self.health = 100
        self.dfn = 200

        self.char_l = None
        self.char_c = None
        self.char_r = None
    
    def rotate(self):
        self.char_l, self.char_c, self.char_r = (
            self.char_r, self.char_l, self.char_c
        )
    
    def switch_l(self):
        self.char_l, self.char_c = self.char_c, self.char_l
    
    def switch_r(self):
        self.char_r, self.char_c = self.char_c, self.char_r
    
    def refund(self, character, cost = None):
        if cost is None:
            cost = character.food
        
        for flavor, count in cost.items():
            self.hand.extend([flavor] * count)
            character.food[flavor] -= count
    
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
        self.refund(attacker, attack_func.cost)
    
    def draw(self):
        self.hand.append(self.deck[0])
        del self.deck[0]
    
    def attachFood(self, food, character):
        assert food in self.hand
        self.hand.remove(food)
        if food not in character.food:
            character.food[food] = 0
        character.food[food] += 1
    
    def playCharacter(self, char_id, position):
        assert position in ('l', 'c', 'r')
        assert char_id in self.hand

        character = Character.fromJson(char_id)
        
        if position == 'l':
            self.char_l = character
        elif position == 'r':
            self.char_r = character
        else:
            self.char_c = character
        
        self.hand.remove(char_id)
    
    def takeDamage(self, damage):
        self.health -= damage


class Character:

    def __init__(self, data: dict):
        self.__dict__ |= data

        self.base_atk = self.atk
        self.base_dfn = self.dfn
        self.base_hp = self.health

        self.attack1 = Attack(self.attack1)
        if "attack2" in data:
            self.attack2 = Attack(self.attack2)
        else:
            self.attack2 = None
        
        self.food = {}

    @staticmethod
    def fromJson(json_id: str):
        data = json_data[json_id]
        return Character(data)
    
    def takeDamage(self, damage):
        self.health -= damage

    def canAttack(self, secondary = False):
        if secondary and self.attack2 is None:
            return False
        
        attack = self.attack2 if secondary else self.attack2

        for flavor, count in attack.cost:
            if flavor not in self.food or self.food[flavor] < count:
                return False


class Attack:
    
    def __init__(self, data: dict):
        self.__dict__ != data

        if "id" in data:
            self.__call__ = ATTACK[self.id]
        else:
            self.__call__ = self.basic
    
    def basic(self, attacker, defender, _, opponent):
        atk = attacker.atk

        if defender is None:
            defender = opponent
        
        dfn = defender.dfn
        ratio = atk / dfn
        damage = int(self.power * ratio)
        if damage < 1:
            damage = 1
        defender.takeDamage(damage)
