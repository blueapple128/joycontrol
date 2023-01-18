import inspect
import logging
import shlex

from aioconsole import ainput

from joycontrol.controller_state import button_push, ControllerState
from joycontrol.transport import NotConnectedError

logger = logging.getLogger(__name__)

import os
os.system('xhost local:root')
from pynput import keyboard

def _print_doc(string):
    """
    Attempts to remove common white space at the start of the lines in a doc string
    to unify the output of doc strings with different indention levels.

    Keeps whitespace lines intact.

    :param fun: function to print the doc string of
    """
    lines = string.split('\n')
    if lines:
        prefix_i = 0
        for i, line_0 in enumerate(lines):
            # find non empty start lines
            if line_0.strip():
                # traverse line and stop if character mismatch with other non empty lines
                for prefix_i, c in enumerate(line_0):
                    if not c.isspace():
                        break
                    if any(lines[j].strip() and (prefix_i >= len(lines[j]) or c != lines[j][prefix_i])
                           for j in range(i+1, len(lines))):
                        break
                break

        for line in lines:
            print(line[prefix_i:] if line.strip() else line)


class CLI:
    def __init__(self):
        self.commands = {}

    def add_command(self, name, command):
        if name in self.commands:
            raise ValueError(f'Command {name} already registered.')
        self.commands[name] = command

    async def cmd_help(self):
        print('Commands:')
        for name, fun in inspect.getmembers(self):
            if name.startswith('cmd_') and fun.__doc__:
                _print_doc(fun.__doc__)

        for name, fun in self.commands.items():
            if fun.__doc__:
                _print_doc(fun.__doc__)

        print('Commands can be chained using "&&"')
        print('Type "exit" to close.')

    async def run(self):
        while True:
            user_input = await ainput(prompt='cmd >> ')
            if not user_input:
                continue

            for command in user_input.split('&&'):
                cmd, *args = shlex.split(command)

                if cmd == 'exit':
                    return

                if hasattr(self, f'cmd_{cmd}'):
                    try:
                        result = await getattr(self, f'cmd_{cmd}')(*args)
                        if result:
                            print(result)
                    except Exception as e:
                        print(e)
                elif cmd in self.commands:
                    try:
                        result = await self.commands[cmd](*args)
                        if result:
                            print(result)
                    except Exception as e:
                        print(e)
                else:
                    print('command', cmd, 'not found, call help for help.')

    @staticmethod
    def deprecated(message):
        async def dep_printer(*args, **kwargs):
            print(message)

        return dep_printer


class ControllerCLI(CLI):
    def __init__(self, controller_state: ControllerState):
        super().__init__()
        self.controller_state = controller_state

    async def cmd_help(self):
        print('Button commands:')
        print(', '.join(self.controller_state.button_state.get_available_buttons()))
        print()
        await super().cmd_help()

    @staticmethod
    def _set_stick(stick, direction, value):
        if direction == 'center':
            stick.set_center()
        elif direction == 'up':
            stick.set_up()
        elif direction == 'down':
            stick.set_down()
        elif direction == 'left':
            stick.set_left()
        elif direction == 'right':
            stick.set_right()
        elif direction in ('h', 'horizontal'):
            if value is None:
                raise ValueError(f'Missing value')
            try:
                val = int(value)
            except ValueError:
                raise ValueError(f'Unexpected stick value "{value}"')
            stick.set_h(val)
        elif direction in ('v', 'vertical'):
            if value is None:
                raise ValueError(f'Missing value')
            try:
                val = int(value)
            except ValueError:
                raise ValueError(f'Unexpected stick value "{value}"')
            stick.set_v(val)
        else:
            raise ValueError(f'Unexpected argument "{direction}"')

        return f'{stick.__class__.__name__} was set to ({stick.get_h()}, {stick.get_v()}).'

    async def cmd_stick(self, side, direction, value=None):
        """
        stick - Command to set stick positions.
        :param side: 'l', 'left' for left control stick; 'r', 'right' for right control stick
        :param direction: 'center', 'up', 'down', 'left', 'right';
                          'h', 'horizontal' or 'v', 'vertical' to set the value directly to the "value" argument
        :param value: horizontal or vertical value
        """
        if side in ('l', 'left'):
            stick = self.controller_state.l_stick_state
            return ControllerCLI._set_stick(stick, direction, value)
        elif side in ('r', 'right'):
            stick = self.controller_state.r_stick_state
            return ControllerCLI._set_stick(stick, direction, value)
        else:
            raise ValueError('Value of side must be "l", "left" or "r", "right"')

    async def run(self, is_tui):
        mapping = {
            keyboard.KeyCode(char='S') : 'left',
            keyboard.KeyCode(char='D') : 'down',
            keyboard.KeyCode(char='E') : 'up',
            keyboard.KeyCode(char='F') : 'right',
            keyboard.KeyCode(char='s') : 'stick l left',
            keyboard.KeyCode(char='d') : 'stick l down',
            keyboard.KeyCode(char='e') : 'stick l up',
            keyboard.KeyCode(char='f') : 'stick l right',
            keyboard.KeyCode(char='j') : 'b',
            keyboard.KeyCode(char='k') : 'y',
            keyboard.KeyCode(char='i') : 'x',
            keyboard.KeyCode(char='l') : 'a',
            keyboard.KeyCode(char='J') : 'stick r left',
            keyboard.KeyCode(char='K') : 'stick r down',
            keyboard.KeyCode(char='I') : 'stick r up',
            keyboard.KeyCode(char='L') : 'stick r right',
            keyboard.Key.enter         : 'plus',
            keyboard.Key.backspace     : 'minus',
            keyboard.KeyCode(char='w') : 'zl',
            keyboard.KeyCode(char='r') : 'l',
            keyboard.KeyCode(char='u') : 'r',
            keyboard.KeyCode(char='o') : 'zr',
            keyboard.KeyCode(char='g') : 'l_stick',
            keyboard.KeyCode(char='h') : 'r_stick',
            keyboard.Key.tab           : 'home',
            keyboard.KeyCode(char='\\'): 'capture',
            keyboard.KeyCode(char='6') : 'special camera',
            keyboard.KeyCode(char='p') : 'mash',
            keyboard.KeyCode(char='x') : 'special dpad',
        }
        currently_held = []
        sticks = {'l': {'h': 2048, 'v': 2048}, 'r': {'h': 2048, 'v': 2048}}
        special = {'camera': False, 'dpad': False}
        if is_tui:
            with keyboard.Events() as events:
                for event in events:
                    if event.__class__ == keyboard.Events.Press:
                        if event.key not in currently_held:
                            currently_held.append(event.key)
                            if event.key in mapping:
                                command = mapping[event.key]
                            else:
                                continue
                            if command.startswith('stick '):
                                _, side, direction = command.split()
                                if special['camera'] and side == 'r':
                                    continue
                                horiz_or_vert = 'h' if direction in ['left', 'right'] else 'v'
                                sticks[side][horiz_or_vert] += (1792 if direction in ['up', 'right'] else -1792)
                                print(await self.cmd_stick(side, horiz_or_vert, sticks[side][horiz_or_vert]))
                                await self.controller_state.send()
                            elif command == 'mash':
                                await self.commands['mash']('a', 1)
                            elif command.startswith('special '):
                                _, subcommand = command.split()
                                special[subcommand] = not special[subcommand]
                                now_on = special[subcommand]
                                print(f'{subcommand} turned {"on" if now_on else "off"}')
                                if subcommand == 'camera':
                                    if now_on:
                                        await self.cmd_stick('r', 'up')
                                    else:
                                        await self.cmd_stick('r', 'center')
                                elif subcommand == 'dpad':
                                    if now_on:
                                        mapping.update({
                                            keyboard.KeyCode(char='s') : 'left',
                                            keyboard.KeyCode(char='d') : 'down',
                                            keyboard.KeyCode(char='e') : 'up',
                                            keyboard.KeyCode(char='f') : 'right',
                                            keyboard.KeyCode(char='S') : 'stick l left',
                                            keyboard.KeyCode(char='D') : 'stick l down',
                                            keyboard.KeyCode(char='E') : 'stick l up',
                                            keyboard.KeyCode(char='F') : 'stick l right',
                                        })
                                    else:
                                        mapping.update({
                                            keyboard.KeyCode(char='S') : 'left',
                                            keyboard.KeyCode(char='D') : 'down',
                                            keyboard.KeyCode(char='E') : 'up',
                                            keyboard.KeyCode(char='F') : 'right',
                                            keyboard.KeyCode(char='s') : 'stick l left',
                                            keyboard.KeyCode(char='d') : 'stick l down',
                                            keyboard.KeyCode(char='e') : 'stick l up',
                                            keyboard.KeyCode(char='f') : 'stick l right',
                                        })
                                else:
                                    assert False
                            else:
                                await self.commands['hold'](command)
                    elif event.__class__ == keyboard.Events.Release:
                        if event.key in currently_held:
                            currently_held.remove(event.key)
                            if event.key in mapping:
                                command = mapping[event.key]
                            else:
                                continue
                            if command.startswith('stick '):
                                _, side, direction = command.split()
                                if special['camera'] and side == 'r':
                                    continue
                                horiz_or_vert = 'h' if direction in ['left', 'right'] else 'v'
                                sticks[side][horiz_or_vert] += (-1792 if direction in ['up', 'right'] else 1792)
                                print(await self.cmd_stick(side, horiz_or_vert, sticks[side][horiz_or_vert]))
                                await self.controller_state.send()
                            elif command == 'mash' or command.startswith('special '):
                                pass
                            else:
                                await self.commands['release'](command)
                    else:
                        print(f'Error! Received unexpected event {event}')
        else:
            while True:
                user_input = await ainput(prompt='cmd >> ')
                if not user_input:
                    continue

                buttons_to_push = []

                for command in user_input.split('&&'):
                    cmd, *args = shlex.split(command)

                    if cmd == 'exit':
                        return

                    available_buttons = self.controller_state.button_state.get_available_buttons()

                    if hasattr(self, f'cmd_{cmd}'):
                        try:
                            result = await getattr(self, f'cmd_{cmd}')(*args)
                            if result:
                                print(result)
                        except Exception as e:
                            print(e)
                    elif cmd in self.commands:
                        try:
                            result = await self.commands[cmd](*args)
                            if result:
                                print(result)
                        except Exception as e:
                            print(e)
                    elif cmd in available_buttons:
                        buttons_to_push.append(cmd)
                    else:
                        print('command', cmd, 'not found, call help for help.')

                if buttons_to_push:
                    await button_push(self.controller_state, *buttons_to_push)
                else:
                    try:
                        await self.controller_state.send()
                    except NotConnectedError:
                        logger.info('Connection was lost.')
                        return
