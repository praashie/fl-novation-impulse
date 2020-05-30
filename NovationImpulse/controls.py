# https://github.com/praashie/fl-novation-impulse

from flatmate.control import MIDIControl

class ImpulseEncoder(MIDIControl):
    def updateValueFromEvent(self, event):
        self.value = event.controlVal - 0x40

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

controls = []

faders = [MIDIControl(channel=0, ccNumber=i, index=i,
    name='Fader_{}'.format(i + 1)) for i in range(9)]

encoders = [ImpulseEncoder(channel=1, ccNumber=i, index=i,
    name='Encoder_{}'.format(i + 1)) for i in range(8)]

trackButtons = [MIDIControl(channel=0, ccNumber=i+0x09, index=i,
    name='TrackButton_{}'.format(i)) for i in range(9)]

clipPads = [ImpulsePad(channel=0, ccNumber=i+0x3C, index=i,
    name='ClipPad_{}'.format(i + 1)) for i in range(8)]

modwheel = MIDIControl(channel=2, ccNumber=0x01, name='ModWheel')

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

transport = [_namespace[name] for name in ("rewind", "forward", "stop", "play", "loop", "record")]
