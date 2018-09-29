import sys
import logging
from time import sleep

import yaml
import click
import attr

from mixorama.factory import create_bartender, create_bar, create_menu, create_shelf
from mixorama.ui import cli_run, bind_hw_buttons
from mixorama.io import cleanup

CONFIG_PATH = 'mixorama.yaml'


@attr.s
class Context:
    cfg = attr.ib()
    ''':type: Dict[str, Dict[str,object]]'''
    shelf = attr.ib()
    ''':type: Dict[str, Component]'''
    bar = attr.ib()
    ''':type: Dict[Component, Valve]'''
    bartender = attr.ib()
    ''':type: mixorama.bartender.Bartender'''
    menu = attr.ib()
    ''':type: Dict[str, Recipe]'''


@click.group()
@click.option('--conf', default=CONFIG_PATH, type=click.Path(dir_okay=False))
@click.pass_context
def cli(ctx: click.Context, conf: str) -> None:
    with open(conf) as cfg_file:
        cfg = yaml.load(cfg_file)

    loglevel = cfg.get('logging', {}).get('level', 'INFO')
    logging.basicConfig(stream=sys.stdout, level=getattr(logging, loglevel))

    shelf = create_shelf(cfg.get('shelf'))
    bar = create_bar(shelf, cfg.get('bar'))
    bartender = create_bartender(bar, cfg.get('bartender'))
    menu = create_menu(shelf, cfg.get('menu'))

    ctx.obj = Context(cfg, shelf, bar, bartender, menu)


@cli.command(name='run')
@click.option('--gui/--no-gui', 'gui', is_flag=True, default=True)
@click.pass_context
def run(ctx: click.Context, gui: bool):
    ctx = ctx.obj
    ''':type: Context'''

    try:
        bind_hw_buttons(ctx.menu, ctx.bartender, ctx.cfg.get('buttons', {}))

        if gui:
            from mixorama.gui import is_gui_available, gui_config, gui_run
            if is_gui_available():
                gui_config(ctx.cfg.get('kivy', {}))
                gui_run(ctx.menu, ctx.bartender)
            else:
                print('GUI is not available on this system')
        else:
            cli_run(ctx.menu, ctx.bartender)

    finally:
        cleanup()


@cli.command(name='test')
@click.pass_context
def test(ctx: click.Context):
    ctx = ctx.obj
    ''':type: Context'''

    print('testing scales. Put an empty glass on them and press Enter')
    input()
    ctx.bartender.make_drink([])
    print('Now lift the glass')
    ctx.bartender.serve() or print('Waiting for a glass lift has timed out')

    print('testing compressor')
    ctx.bartender.compressor.open()
    sleep(.3)
    ctx.bartender.compressor.close()
    sleep(.5)

    print('testing valves')
    for component, valve in ctx.bar.items():
        print('Testing', component.name)
        valve.open()
        sleep(.3)
        valve.close()
        sleep(.3)


__name__ == '__main__' and cli()
