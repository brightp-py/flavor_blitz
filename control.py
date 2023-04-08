import numpy as np
import random
import time
import matplotlib.pyplot as plt

from demo import *

class ScoreAI:

    def __init__(self, player: Player, name: str):
        self.player = player
        self.name = name
    
    def runCommand(self, opponent: Player):
        QUIET_ATTACKS = True

        options = {}
        opp_score = opponent.score()

        char_cards = []
        food_cards = []
        for card in self.player.hand:
            if card in json_data:
                char_cards.append(card)
            else:
                food_cards.append(card)

        # draw a card
        p0 = self.player.copy()
        p0.draw()
        options["draw"] = p0.score() - opp_score
        del p0

        # reposition
        if any(char is not None for char in (self.player.char_l,
                                             self.player.char_c,
                                             self.player.char_r)) and \
            not self.player.movementCooldown:
            p0 = self.player.copy()
            p0.rotate()
            options["rotate"] = p0.score() - opp_score
            del p0

            if any(char is not None for char in (self.player.char_l,
                                                 self.player.char_c)):
                p0 = self.player.copy()
                p0.switch_l()
                options["swap l"] = p0.score() - opp_score
                del p0

            if any(char is not None for char in (self.player.char_c,
                                                 self.player.char_r)):
                p0 = self.player.copy()
                p0.switch_r()
                options["swap r"] = p0.score() - opp_score
                del p0

        # per-character actions
        for pos, char in (('l', self.player.char_l),
                          ('c', self.player.char_c),
                          ('r', self.player.char_r)):
            
            if char is not None:
                # attach food
                for card in food_cards:
                    p0 = self.player.copy()
                    p0.attachFood(card, p0.charAt(pos))
                    options[f"{card} {pos}"] = p0.score() - opp_score
                    del p0

                # attack 1
                if char.canAttack(False):
                    p0 = self.player.copy()
                    o0 = opponent.copy()
                    p0.attack(p0.charAt(pos), o0)
                    options[f"1 {pos}"] = p0.score() - o0.score()
                    del p0
                    del o0

                # attack 2
                if char.attack2 is not None and char.canAttack(True):
                    p0 = self.player.copy()
                    o0 = opponent.copy()
                    p0.attack(p0.charAt(pos), o0, True)
                    options[f"2 {pos}"] = p0.score() - o0.score()
                    del p0
                    del o0

                # refund
                # if len(char.food_basic) + len(char.food_complex) > 0:
                #     p0 = self.player.copy()
                #     p0.refund(p0.charAt(pos))
                #     options[f"refund {pos}"] = p0.score() - opp_score
                #     del p0
            
            # play character
            else:
                for card in char_cards:
                    p0 = self.player.copy()
                    p0.playCharacter(card, pos)
                    options[f"{card} {pos}"] = p0.score() - opp_score
                    del p0
        
        # print(options)

        QUIET_ATTACKS = False

        phrases, scores = zip(*options.items())

        scores = np.array(scores)
        if np.min(scores) != np.max(scores):
            scores -= np.min(scores)
        scores /= np.sum(scores)
        scores = scores ** 2

        # print(phrases)
        # print(scores)

        decision = random.choices(phrases, scores, k=1)[0]

        # draw
        if decision == "draw":
            self.player.draw()
            print(f"{self.name} drew a card.")
            return True
        
        # reposition
        ## rotate
        if decision == "rotate":
            self.player.rotate()
            print(f"{self.name} rotated the board.")
            return True
        
        decision, pos = decision.split(' ')

        ## swap
        if decision == "swap":
            if pos == "l":
                self.player.switch_l()
                print(f"{self.name} swapped their Left side.")
            elif pos == "r":
                self.player.switch_r()
                print(f"{self.name} swapped their Right side.")
            return True

        # attack
        if decision in ("1", "2"):
            print(f"{self.name} attacked on position {pos.upper()}.")
            self.player.attack(
                self.player.charAt(pos),
                opponent,
                decision == '2')
            return True
        
        # refund
        if decision == "refund":
            print(f"{self.name} refunded position {pos.upper()}.")
            self.player.refund(self.player.charAt(pos))
            return True
        
        # play character
        if decision in json_data:
            print(f"{self.name} played {decision} on position {pos.upper()}.")
            self.player.playCharacter(decision, pos)
            return True
        
        # play food
        print(f"{self.name} played a {decision} on position {pos.upper()}.")
        self.player.attachFood(decision, self.player.charAt(pos))
        return True

    def endTurn(self):
        self.player.endTurn()


class TextUser:
    divider = "----------"

    def __init__(self, player: Player):
        self.player = player
    
    def twoColumns(self, left: str, right: str, width = 51):
        if width % 2 == 0:
            width += 1
        
        left = left.split('\n')
        right = right.split('\n')

        side_width = (width - 1) // 2
        res = []
        for l, r in zip(left, right):
            l = " " * ((side_width - len(l)) // 2) + l
            r = " " * ((side_width - len(r)) // 2) + r
            res.append(l + " " * (side_width - len(l)) + "*" + r)
        
        return '\n'.join(res)

    def printData(self, opponent: Player, width = 51):
        print("State Score:", int(self.player.score()), "|",
              int(opponent.score()))
        print(self.twoColumns(str(self.player), str(opponent), width))

        for char1, char2 in ((self.player.char_l, opponent.char_r),
                             (self.player.char_c, opponent.char_c),
                             (self.player.char_r, opponent.char_l)):
            print(self.twoColumns(self.divider, self.divider, width))
            if char1 is None:
                char1 = "\n" * 2
            if char2 is None:
                char2 = "\n" * 2
            print(self.twoColumns(str(char1), str(char2), width))
        
        print("Hand:")
        print(', '.join(c_name.capitalize() for c_name in self.player.hand))
    
    def fitToWidth(self, text, width):
        lines = []
        nline = ""
        for word in text.split():
            if nline == "":
                nline = word
            else:
                if len(nline) + len(word) >= width:
                    lines.append(nline)
                    nline = word
                else:
                    nline += ' ' + word
        lines.append(nline)
        return lines
    
    def viewCard(self, json_id, width = 51):
        data = json_data[json_id]
        lines = [
            f"{data['primary'].capitalize()} {data['name']}",
            f"{str(data['atk'])} ATK | {str(data['health'])} HP | {str(data['dfn'])} DFN"
        ]

        lines = [
            " " * ((width - len(line)) // 2) + line for line in lines
        ]
        
        print('\n'.join(lines))
        
        att1 = data['attack1']
        lines1 = [
            f"{att1['name']} - {str(att1['power'])}",
            ', '.join(f'{flav.capitalize()}: {cost}' for flav, cost in att1['cost'].items())
        ]

        if 'attack2' not in data:
            lines1.extend(self.fitToWidth(att1['desc'], width))
            lines1 = [
                " " * ((width - len(line)) // 2) + line for line in lines1
            ]
            print('\n'.join(lines1))
        
        else:
            half_width = (width - 5) // 2

            att2 = data['attack2']
            lines2 = [
                f"{att2['name']} - {str(att2['power'])}",
                ', '.join(f'{flav}: {cost}' for flav, cost in att2['cost'].items())
            ]

            lhalf, rhalf = [], []

            if 'desc' in att1:
                lhalf = self.fitToWidth(att1['desc'], half_width)
            if 'desc' in att2:
                rhalf = self.fitToWidth(att2['desc'], half_width)

            lines1.extend(lhalf)
            lines2.extend(rhalf)

            if len(lines1) < len(lines2):
                lines1 += [""] * (len(lines2) - len(lines1))
            elif len(lines2) < len(lines1):
                lines2 += [""] * (len(lines1) - len(lines2))
            
            print(self.twoColumns('\n'.join(lines1), '\n'.join(lines2), width))
    
    def runCommand(self, opponent: Player):
        """
        The user should be able to:
         - Draw a card
         - Play a character
         - Play a food
         - Refund all food from a character
         - Reposition
         - Attack with a character
        """
        comm = input("Action: ").lower()

        if comm == "draw" or comm == "d":
            self.player.draw()
            return True

        if comm == "rotate":
            if self.player.movementCooldown:
                return False
            self.player.rotate()
            return True
        
        if comm.count(' ') != 1:
            return False
        
        comm, pos = comm.split(' ')

        if comm in ("view", "v", "?"):
            self.viewCard(pos, 71)
            return False

        if pos == 'l':
            char = self.player.char_l
        elif pos == 'r':
            char = self.player.char_r
        elif pos == 'c':
            char = self.player.char_c
        else:
            return False

        if comm in self.player.hand:
            if comm in ("sour", "sweet", "spicy", "savory", "bitter"):
                if char is None:
                    return False
                self.player.attachFood(comm, char)
            else:
                if char is not None:
                    return False
                self.player.playCharacter(comm, pos)
            return True

        if comm == "refund":
            if char is None:
                return False
            self.player.refund(char)
            return True

        if comm == "swap":
            if self.player.movementCooldown or pos == 'c':
                return False
            if pos == 'l':
                self.player.switch_l()
            elif pos == 'r':
                self.player.switch_r()
            return True
        
        if comm == "attack" or comm == "a":
            if char.attack2 is None:
                if not char.canAttack():
                    return False
                self.player.attack(char, opponent)
                return True
            print(f"1: {char.attack1.name} | 2: {char.attack2.name}")
            att = input("Attack: ")
            if att == "1" and char.canAttack():
                self.player.attack(char, opponent)
                return True
            if att == "2" and char.canAttack(True):
                self.player.attack(char, opponent, True)
                return True
            return False

        return False

    def endTurn(self):
        self.player.endTurn()


def singleTurn(user, opponent):
    if isinstance(user, TextUser):
        user.printData(opponent, 81)
    else:
        print("Thinking...")
        time.sleep(0.75)
    while True:
        if user.runCommand(opponent):
            user.endTurn()
            opponent.endTurn()
            break


if __name__ == "__main__":
    sour_base = {
        "lemonguard": 2,
        "lemonturret": 2,
        "lemonbard": 2,
        "sour": 6
    }

    savory_base = {
        "mushroomgrave": 2,
        "scuffedmushroom": 2,
        "toughmushroom": 2,
        "savory": 6
    }

    sweet_base = {
        "peachbabe": 2,
        "peachclobbler": 2,
        "peachwisp": 2,
        "sweet": 6
    }

    spicy_base = {
        "peppercourt": 2,
        "pepperminister": 2,
        "habenhero": 2,
        "spicy": 6
    }

    deck1 = []
    for card, count in (spicy_base | savory_base).items():
        deck1 += [card] * count
    
    deck2 = []
    for card, count in (sour_base | sweet_base).items():
        deck2 += [card] * count
    player1 = Player(deck1)
    player2 = Player(deck2)

    for _ in range(5):
        player1.draw()
        player2.draw()
    
    names = ["Alex", "Bunny", "Claire", "Dan", "Evan", "Felipe", "Green",
             "Hafu", "Isaac", "Jayce", "Kory", "Link", "Ms. Terry",
             "Newt", "Olive", "Paul", "Quinton", "Rory", "Scott", "Thomas",
             "Victor", "Winston", "X", "Yuko", "Zoe"]

    # user1 = TextUser(player1)
    # user2 = ScoreAI(player2, random.choice(names))
    
    # while True:
    #     try:
    #         singleTurn(user1, player2)
    #         if player2.health <= 0 or player1.health <= 0:
    #             break
    #         singleTurn(user2, player1)
    #         if player2.health <= 0 or player1.health <= 0:
    #             break
    #     except KeyboardInterrupt:
    #         break

    user1 = ScoreAI(player1, "Player 1")
    user2 = ScoreAI(player2, "Player 2")

    data = []

    while True:
        try:
            user1.runCommand(player2)
            user1.endTurn()
            user2.endTurn()
            if player2.health <= 0:
                print("Player 1 wins")
                break
            if player1.health <= 0:
                print("Player 2 wins")
                break
            data.append([player1.score(), player2.score()])

            user2.runCommand(player1)
            user1.endTurn()
            user2.endTurn()
            if player2.health <= 0:
                print("Player 1 wins")
                break
            if player1.health <= 0:
                print("Player 2 wins")
                break
            data.append([player1.score(), player2.score()])

        except KeyboardInterrupt:
            break
    
    # print(data)
    # print(*zip(data))
    plt.plot(range(len(data)), *zip(*data))
    plt.show()
