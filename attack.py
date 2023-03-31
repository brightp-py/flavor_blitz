ATTACK = {}

def identify(name):
    def inner(func):
        ATTACK[name] = func
        return func
    return inner


@identify("switchToCenter")
def switchToCenter(self, a, d, u, o):
    self.basic(a, d, u, o)
    
    if self == u.char_l:
        u.switch_l()
    elif self == u.char_r:
        u.switch_r()

@identify("wide")
def wideAttack(self, a, d, u, o):
    power_save = self.power

    self.basic(a, d, u, o)

    self.power = self.power / 2
    if (self == u.char_l or self == u.char_r) and o.char_c is not None:
        self.basic(a, o.char_c, u, o)
    if self == u.char_c:
        if o.char_l is not None:
            self.basic(a, o.char_l, u, o)
        if o.char_r is not None:
            self.basic(a, o.char_r, u, o)
    self.power = power_save


print(ATTACK)