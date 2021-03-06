import sys
import logging
from time import sleep

import yaml
import click
import attr

from mixorama.factory import create_bartender, create_bar, create_menu, create_shelf, create_usage_manager
from mixorama.recipes import Recipe
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
    usage_manager = attr.ib()
    ''':type: mixorama.usage_manager.UsageManager'''
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
    menu = create_menu(bar, cfg.get('menu'))

    # Usage Manager simply hooks
    usage_manager = create_usage_manager(bartender, cfg.get('usage'))

    ctx.obj = Context(cfg, shelf, bar, bartender, usage_manager, menu)


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
            gui_config(ctx.cfg.get('kivy', {}))
            if is_gui_available():
                gui_run(ctx.menu, ctx.bartender, ctx.usage_manager)
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

    print('Testing scales')

    print('Prepare a 100g weight and press enter') or input()
    ctx.bartender.scales.reset()
    ctx.bartender.scales.\
        wait_for_weight(100, on_progress=lambda d, s:
        print('scales: {}/{}'.format(d, s)))

    print('Put an empty glass on them and press Enter') or input()
    ctx.bartender.make_drink(recipe=Recipe('mixorama test'))
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

    ctx.bartender.compressor.close()


@cli.command(name='whatswhat')
@click.pass_context
def whatswhat(ctx: click.Context):
    ctx = ctx.obj
    ''':type: Context'''

    print('!! Make sure the air is disconnected from bottles !!')
    if not input('Press Y to start').upper().startswith('Y'):
        return

    valves = sorted(ctx.bar.items(), key=lambda i: i[1].channel)
    try:
        while True:
            for component, valve in valves:
                print("Testing %s on pin %d" % (component.name, valve.channel))
                input("Press any key to start")
                valve.open()
                ctx.bartender.compressor.open()
                input("Press any key to stop")
                ctx.bartender.compressor.close()
                sleep(.5)
                valve.close()
    except KeyboardInterrupt:
        pass


@cli.command('scales')
@click.pass_context
def scales(ctx: click.Context):
    ctx = ctx.obj
    ''':type: Context'''

    impl = ctx.bartender.scales.scales

    impl.reset()
    while True:
        print(impl.get_raw_data(1))


__name__ == '__main__' and cli()
