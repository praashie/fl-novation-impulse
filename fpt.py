import channels
import midi
import mixer
import patterns
import transport
import ui

import controls

def callFPT(name, value, event):
    fptCode = getattr(midi, 'FPT_' + name)
    transport.globalTransport(fptCode, value, event.pmeFlags | midi.PME_FromMIDI)
    return name

def FPTGeneric(fptName, value_scale=1, func=None):
    def _action(control, event):
        result = callFPT(fptName, control.value * value_scale, event)
        if func:
            return func()
        return result
    return _action

def FPTButton(fptName, value=1, force=False):
    def _action(control, event):
        if force or control.value:
            return callFPT(fptName, value, event)
    return _action

def FPTDualButton(fptOn, fptOff, value=1):
    def _action(control, event):
        action = fptOn if control.value else fptOff
        return callFPT(action, value, event)
    return _action

transportMap = { # (shift, loop, master)
    (False, False, False): { # Normal
        controls.stop: FPTButton("Stop"),
        controls.play: FPTButton("Play"),
        controls.record: FPTButton("Record"),
    }, (True, False, False): { # Shift on, Loop off
        controls.loop: FPTDualButton("PunchIn", "PunchOut"),
        controls.record: FPTButton("Overdub")
    }, (False, True, False): { # Shift off, Loop on
        controls.record: FPTButton("LoopRecord"),
        controls.play: FPTButton("Loop"),
    }, (True, True, False): { # Shift + Loop on
        controls.record: FPTButton("StepEdit"),
        controls.loop: FPTDualButton("PunchIn", "PunchOut")
    }, (False, False, True): { # Master
        controls.forward: FPTButton("Next"),
        controls.rewind: FPTButton("Previous"),
        controls.play: FPTButton("Enter"),
        controls.stop: FPTButton("Escape"),
        controls.record: FPTButton("ItemMenu"),
        controls.loop: FPTDualButton("PunchIn", "PunchOut")
    }, (False, True, True): { # Master + Loop
        controls.masterButton: FPTButton("Metronome"),
        controls.record: FPTButton("Menu"),
        controls.loop: FPTDualButton("PunchIn", "PunchOut")
    }, (True, False, True): { # Master + Shift
        controls.loop: FPTDualButton("PunchIn", "PunchOut")
    }, (True, True, True): { # All three
        controls.loop: FPTDualButton("PunchIn", "PunchOut"),
        controls.masterButton: FPTButton("CountDown")
    }, None: { # Default
    }
}

def handleTransport(control, event):
    modifiers = (controls.shift.value, controls.loop.value, controls.masterButton.value)
    t_map = transportMap.get(modifiers, ())
    if control in t_map:
        return t_map[control](control, event)
    elif control in transportMap[None]:
        return transportMap[None][control](control, event)
