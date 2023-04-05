from demo import *

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
            if pos == 'c':
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
    user.printData(opponent, 81)
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
        "mushroomnavy": 2,
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

    deck1 = []
    for card, count in (sweet_base | sour_base).items():
        deck1 += [card] * count
    
    deck2 = []
    for card, count in (sweet_base | savory_base).items():
        deck2 += [card] * count
    
    player1 = Player(deck1)
    player2 = Player(deck2)

    for _ in range(5):
        player1.draw()
        player2.draw()

    user1 = TextUser(player1)
    user2 = TextUser(player2)
    
    while True:
        try:
            singleTurn(user1, player2)
            if player2.health <= 0 or player1.health <= 0:
                break
            singleTurn(user2, player1)
            if player2.health <= 0 or player1.health <= 0:
                break
        except KeyboardInterrupt:
            break
