class Component:
    name = 'Weird Ingridient'

    def __init__(self, name=None, density=1, strength=0, volume=1000):
        """
        :param density: grams per milliliter
        :param strength: ABV, %
        """
        self.density = density
        self.strength = strength
        self.volume = volume
        self.spent = 0
        if name:
            self.name = name

    def use(self, volume_used):
        can_use = self.can_use(volume_used)
        if can_use:
            self.spent += volume_used
        return can_use

    def can_use(self, volume):
        return self.volume > self.spent + volume

    def refill(self, value=None):
        self.spent = self.volume - (self.volume if value is None else value)

    def __str__(self):
        return self.name


class Recipe:
    name = 'Mystery Booze'
    sequence = []
    ''':type: List[Tuple[Component, int]]'''
    image = None
    ''':type: str'''
    description = None
    ''':type: str'''

    def __init__(self, name=None, sequence=None, **meta):
        self.sequence = sequence or []
        if name:
            self.name = name
        for k, v in meta.items():
            setattr(self, k, v)

    def volume(self):
        return sum([component[1] for component in self.sequence])

    def weight(self):
        return sum([c[1] * c[0].density for c in self.sequence])

    def strength(self):
        return sum([c[1] * c[0].strength for c in self.sequence]) \
               / self.volume()

    def __iter__(self):
        return iter(self.sequence)

    def __str__(self):
        return "\n".join(['{} ml of {}'.format(v, str(c))
                          for c, v in self.sequence])
