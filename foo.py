from pynput import keyboard

currently_held = []

with keyboard.Events() as events:
    for event in events:
        if event.key == keyboard.Key.esc:
            break
        else:
            if event.__class__ == keyboard.Events.Press:
                if event.key not in currently_held:
                    currently_held.append(event.key)
                    try:
                        print('Received press {}'.format(event.key.char))
                    except:
                        print('Received special press {}'.format(event.key))
            elif event.__class__ == keyboard.Events.Release:
                print('Received release event {}'.format(event))
                if event.key in currently_held:
                    currently_held.remove(event.key)
                else:
                    print("Warning {}".format(event.key))
            else:
                print('Received unexpected event {}'.format(event))
