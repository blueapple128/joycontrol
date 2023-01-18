# joycontrol
Emulate Nintendo Switch Controllers over Bluetooth.

Tested on Ubuntu 19.10, and with Raspberry Pi 3B+ and 4B Raspbian GNU/Linux 10 (buster)

## Features
Emulation of JOYCON_R, JOYCON_L and PRO_CONTROLLER. Able to send:
- button commands
- stick state
- ~~nfc data~~ (removed, see [#80](https://github.com/mart1nro/joycontrol/issues/80))

## Installation
- Install dependencies

Ubuntu: Install the `dbus-python` and `libhidapi-hidraw0` packages
```bash
sudo apt install python3-dbus libhidapi-hidraw0
```

Arch Linux Derivatives: Install the `hidapi` and `bluez-utils-compat`(AUR) packages


- Clone the repository and install the joycontrol package to get missing dependencies (Note: Controller script needs super user rights, so python packages must be installed as root). In the joycontrol folder run:
```bash
sudo pip3 install .
```
<!-- - Consider to disable the bluez "input" plugin, see [#8](https://github.com/mart1nro/joycontrol/issues/8) -->

- Also run:
```
sudo pip3 install hid==1.0.4
```

## Command line interface
- First time:
```bash
sudo python3 run_controller_cli.py PRO_CONTROLLER
```

Then open the "Change Grip/Order" menu of the Switch.

- Second/future times:
```
sudo python3 run_controller_cli.py PRO_CONTROLLER -r '00:00:00:00:00:00'
```

Reconnecting no longer requires opening the "Change Grip/Order" menu. Substitute an actual MAC address; you can find out a paired mac address using the "bluetoothctl" system command, or buried in the terminal output from the first connection. TODO output this accessibly

- After (re)connecting, press `enter` and a `>>>` prompt should appear.

- Use e.g. `a` to press A, `help` to see a list of available commands, and `test_buttons` (from the Home menu) to auto-navigate to the "Test Controller Buttons" menu.

## TUI hack
```
sudo python3 run_controller_cli.py PRO_CONTROLLER tui [-r '00:00:00:00:00:00']
```
Hardcoded controls at https://github.com/blueapple128/joycontrol/blob/master/joycontrol/command_line_interface.py#L166.

## Issues
- Some bluetooth adapters seem to cause disconnects for reasons unknown, try to use an usb adapter instead 
- Incompatibility with Bluetooth "input" plugin requires a bluetooth restart, see [#8](https://github.com/mart1nro/joycontrol/issues/8)
- It seems like the Switch is slower processing incoming messages while in the "Change Grip/Order" menu.
  This causes flooding of packets and makes pairing somewhat inconsistent.
  Not sure yet what exactly a real controller does to prevent that.
  A workaround is to use the reconnect option after a controller was paired once, so that
  opening of the "Change Grip/Order" menu is not required.
- ...

## Thanks
- Special thanks to https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering for reverse engineering of the joycon protocol
- Thanks to the growing number of contributers and users

## Resources

[Nintendo_Switch_Reverse_Engineering](https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering)

[console_pairing_session](https://github.com/timmeh87/switchnotes/blob/master/console_pairing_session)
