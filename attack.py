ATTACK = {}

def identify(name):
    def inner(func):
        ATTACK[name] = func
        return func
    return inner


@identify("switchToCenter")
def switchToCenter(self, a, d, u, o):
    self.basic(a, d, u, o)
    
    if a.pos == 'l':
        u.switch_l()
    elif a.pos == 'r':
        u.switch_r()

@identify("wide")
def wideAttack(self, a, d, u, o):
    power_save = self.power

    self.basic(a, d, u, o)

    self.power = self.power / 2
    if a.pos in ('l', 'r') and o.char_c is not None:
        print('c', o.char_c)
        self.basic(a, o.char_c, u, o)
    if a.pos == 'c':
        if o.char_l is not None:
            print('l', o.char_l)
            self.basic(a, o.char_l, u, o)
        if o.char_r is not None:
            print('r', o.char_r)
            self.basic(a, o.char_r, u, o)
    self.power = power_save

@identify("lure")
def lureDefender(self, a, d, u, o):
    if d is None:

        # left ally fights right opponent
        #  - center -> right means switch right
        #  X left   -> right is NOT allowed
        if a.pos == 'l':
            if o.char_c is not None:
                o.switch_r()
            d = o.char_r
        
        # center ally fights center opponent
        #  - left  -> center means switch left
        #  - right -> center means switch right
        if a.pos == 'c':
            if o.char_l is not None:
                o.switch_l()
            elif o.char_r is not None:
                o.switch_r()
            d = o.char_c
        
        # right ally fights left opponent
        #  - center -> left means switch left
        #  - right  -> left means rotate
        if a.pos == 'r':
            if o.char_c is not None:
                o.switch_l()
            elif o.char_r is not None:
                o.rotate()
            d = o.char_l

    self.basic(a, d, u, o)

@identify("sporousBlast")
def sporousBlast(self, a, d, u, o):
    self.basic(a, d, u, o)
    
    health_before = a.health
    self.basic(a, a, u, o)
    healing = health_before - a.health

    if a.pos == 'l' or a.pos == 'r':
        if u.char_c is not None:
            u.char_c.healCapped(healing)
    elif a.pos == 'c':
        if u.char_l is not None:
            u.char_l.healCapped(healing)
        if u.char_r is not None:
            u.char_r.healCapped(healing)

@identify("lifeSteal50")
def lifeSteal50(self, a, d, u, o):
    if d is None:
        self.basic(a, d, u, o)
        return

    health_before = d.health
    self.basic(a, d, u, o)
    healing = int((health_before - d.health) / 2)
    excess = a.healCapped(healing)
    u.heal(excess)

@identify("draw")
def draw(self, a, d, u, o):
    self.basic(a, d, u, o)
    u.draw()

@identify("overwhelm")
def overwhelm(self, a, d, u, o):
    if d is None:
        self.basic(a, d, u, o)
        return

    health = d.health
    dmg = self.basic(a, d, u, o)
    if d.health <= 0:
        o.takeDamage(dmg - health)

@identify("recall")
def recall(self, a, d, u, o):
    self.basic(a, d, u, o)
    u.refund(a)
    u.hand.append(a.ident)

    if a.pos == 'l':
        u.char_l = None
    elif a.pos == 'r':
        u.char_r = None
    elif a.pos == 'c':
        u.char_c = None

@identify("incinerate")
def incinerate(self, a, d, u, o):
    nfood = len(a.food_basic)
    i = 0
    while i < nfood:
        food = a.food_basic[i]
        if food.ident == "sweet":
            self.basic(a, d, u, o)
            u.discard.append("sweet")
            del a.food_basic[i]
            nfood -= 1
        else:
            i += 1

    # if "sweet" not in a.food:
    #     return

    # for _ in range(a.food["sweet"]):
    #     self.basic(a, d, u, o)
    #     u.discard.append("sweet")
