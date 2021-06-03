# https://github.com/praashie/fl-novation-impulse

from flatmate.control import MIDIControl, MIDIButton
from flatmate.hooker import Hooker

import _random as random

import device
random_generator = random.Random()

class ImpulseEncoder(MIDIControl):
    def updateValueFromEvent(self, event):
        self.value = event.controlVal - 0x40
        event.inEv = self.value
        event.outEv = self.value
        event.isIncrement = True

class ImpulseSoloMode(MIDIControl):
    _mixermode_callback = None
    onSoloModeCallback = None

    def callback(self, control, event):
        if self.value == self.value_previous:
            self._mixermode_callback(self, event)
        else:
            self.onSoloModeCallback(self, event)

    def set_callback(self, callback):
        self._mixermode_callback = callback

    def setValue(self, value):
        self.value = value
        self.sendFeedback(value)

    def isSoloEnabled(self):
        return self.value == 0

class ImpulsePad(MIDIControl):
    _last_state = 0x7F
    current_color = 0
    flashing = False

    PEAK_COLOR_TABLE = [
        (0, 0), (0, 1),
        (0, 1), (0, 2), (0, 3),
        (1, 3), (2, 3), (3, 3),
        (3, 2), (3, 1), (3, 0)
    ]

    def setColor(self, red=0, green=0, flash=None):
        red = red & 0b11
        green = green & 0b11
        if flash is not None:
            self.flashing = flash

        # Color bits:
        # _BBF_RR
        self.current_color = (green << 4) + red
        self._update()

    def _update(self):
        new_state = self.current_color + self.flashing * 0x08
        if self._last_state == new_state:
            return
        self.sendFeedback(new_state)
        self._last_state = new_state

    def setFlash(self, flash=None):
        if flash is None:
            self.flashing = not self.flashing
        else:
            self.flashing = flash
        self._update()

    def setPeakColor(self, peak_value):
        range_max = (len(self.PEAK_COLOR_TABLE) - 1)

        # Dithering
        peak_value += 0.98 * (random_generator.random() - 0.5) / range_max
        peak_value = max(0.0, min(1.0, peak_value))

        offset = int(peak_value * range_max)
        red, green = self.PEAK_COLOR_TABLE[offset]

        self.setColor(red=red, green=green)

class DoubleClickHoldControl(MIDIButton):
    holding = False

    def updateValueFromEvent(self, event):
        super().updateValueFromEvent(event)

        if self.double_click:
            self.holding = True
        elif self.holding and self.value:
            self.holding = False
        if self.holding:
            self.value = 1
        self.sendFeedback(self.value)

class ProgramChangeDataKnobWrapper:
    def __init__(self, channel):
        self.channel = channel
        self.current_program = None
        self.value = 0
        self.index = 9001
        self.callback = None

        Hooker.include(self)

    def OnProgramChange(self, event):
        if event.midiChan == self.channel:
            if self.current_program is not None:
                self.value = event.progNum - self.current_program
                if self.callback:
                    self.callback(self, event)
            self.current_program = event.progNum
            event.handled = True

    def set_callback(self, func):
        self.callback = func

controls = []

faders = [MIDIControl(channel=0, ccNumber=i, index=i,
    name='Fader_{}'.format(i + 1)) for i in range(9)]

encoders = [ImpulseEncoder(channel=1, ccNumber=i, index=i,
    name='Encoder_{}'.format(i + 1)) for i in range(8)]

dataKnob = ProgramChangeDataKnobWrapper(channel=0)

trackButtons = [MIDIButton(channel=0, ccNumber=i+0x09, index=i,
    name='TrackButton_{}'.format(i), lazy_feedback=True) for i in range(8)]

masterButton = DoubleClickHoldControl(channel=0, ccNumber=0x09 + 8, index=8, name='MasterButton')

clipPads = [ImpulsePad(channel=0, ccNumber=i+0x3C, index=i,
    name='ClipPad_{}'.format(i + 1)) for i in range(8)]

modwheel = MIDIControl(channel=2, ccNumber=0x01, name='ModWheel')

@modwheel.set_callback
def modwheel_fix(wheel, event):
    event.midiChan = 0
    device.processMIDICC(event)
    event.handled = True

controls.extend(faders)
controls.extend(encoders)
controls.extend(trackButtons)
controls.extend(clipPads)

_namespace = globals()

_control_dict = {
        "encoderMidiMode": (1, 0x8),
        "encoderMixerMode": (1, 0x9),
        "encoderPluginMode": (1, 0xA),
        "encoderPageUp": (1, 0xB),
        "encoderPageDown": (1, 0xC),
        "rewind": (0, 0x1B),
        "forward": (0, 0x1C),
        "stop": (0, 0x1D),
        "play": (0, 0x1E),
        "loop": (0, 0x1F),
        "record": (0, 0x20),
        "mixerBankNext": (0, 0x23),
        "mixerBankPrevious": (0, 0x24),
        "mixerTrackNext": (0, 0x25),
        "mixerTrackPrevious": (0, 0x26),
        "faderMidiMode": (0, 0x21),
        "shift": (0, 0x27),
        "preview": (0, 0x29)
}

for _name, _arguments in _control_dict.items():
    mc = MIDIControl(*_arguments, name=_name)
    _namespace[_name] = mc
    controls.append(mc)

faderMixerMode = ImpulseSoloMode(0, 0x22, name="faderMixerSoloMode")
faderMixerMode.setValue(1) # Set Mute mode by default

controls.append(faderMixerMode)

transport = [
    rewind,
    forward,
    stop,
    play,
    loop,
    record,
    masterButton
]
