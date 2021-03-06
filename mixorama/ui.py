import logging

from mixorama.bartender import BartenderState
from mixorama.io import Button

logger = logging.getLogger(__name__)


def request_drink(bartender, recipe):
    def ui():
        print('Making a {}'.format(recipe.name))
        if bartender.make_drink(recipe=recipe):
            print('Your drink is ready! Please take it from the tray')
            bartender.serve()
        else:
            print('Could not make a drink')
    return ui


def cli_run(menu, bartender):
    bartender.on_sm_transition(
        lambda tostate, component, volume, done, target:
            print('The Bartender is now {} {} ({}/{})'.format(tostate.name, component, done, volume)),
        BartenderState.POURING_PROGRESS
    )

    while True:
        print('Ready to make cocktails!')
        print('Pick one of: ')
        for c in menu:
            print(c)
        choice = input('Which one would you like? ')

        if choice in menu:
            drink = menu[choice]
            print(drink.name)
            print('-' * len(drink.name))
            print('Volume: %.2f' % drink.volume())
            print('Strength: %.2f' % drink.strength())
            confirmed = input('Make it? y/n ')
            if confirmed.startswith('y'):
                request_drink(bartender, drink)()
        else:
            print('Unknown cocktail: ' + choice)


def bind_hw_buttons(menu, bartender, cfg):
    logger.debug('Assigning buttons')
    for btn, recpie_name in cfg.items():
        if recpie_name is False or recpie_name == 'abort':
            Button(btn, lambda: bartender.abort() and print('Please discard the glass contents'))
        else:
            Button(btn, request_drink(bartender, menu[recpie_name]))
