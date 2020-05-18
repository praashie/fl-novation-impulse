from flatmate.control import MIDIControl

class ImpulseEncoder(MIDIControl):
    def updateValueFromEvent(self, event):
        self.value = event.controlVal - 0x40

class ControllerMode:
    def __init__(self, displayName, source, feedback, page=None):
        self.displayName = displayName
        self.sourceControl = source
        self.feedbackControl = feedback
        self.pageSourceControl = page

        self.callback = None
        self.pageCallback = None

        self.sourceControl.set_callback(self.onControl)
        if self.pageSourceControl:
            self.pageSourceControl.set_callback(self.onControl)

    def feedback(self):
        self.feedbackControl.sendFeedback(0)

    def onControl(self, control, event):
        if control == self.sourceControl:
            self.callback(self, control, event)
        elif control == self.pageSourceControl:
            self.pageCallback(self, control, event)

class ImpulseModeSwitcher:
    def __init__(self, modes, invert=False):
        self.onModeChangeCallback = None
        self.onPageChangeCallback = None
        self.invert = invert

        self.mode = None

        for cmode in modes:
            if self.invert and cmode.pageSourceControl:
                cmode.callback = self.onPageChange
                cmode.pageCallback = self.onModeButton
            else:
                cmode.callback = self.onModeButton
                cmode.pageCallback = self.onPageChange

    def onModeButton(self, mode, control, event):
        self.previous = self.mode
        self.mode = mode
        if callable(self.onModeChangeCallback):
            self.onModeChangeCallback(mode, event)
        self.set(mode)

    def onPageChange(self, mode, control, event):
        if callable(self.onPageChangeCallback):
            self.onPageChangeCallback(control, event)
        self.set(self.mode)

    def set(self, mode):
        self.mode = mode
        mode.feedback()

controls = []

faders = [MIDIControl(channel=0, number=i, name='Fader_{}'.format(i + 1))
        for i in range(9)]

encoders = [ImpulseEncoder(channel=1, number=i, name='Encoder_{}'.format(i + 1))
        for i in range(8)]

trackButtons = [MIDIControl(channel=0, number=i+0x09, name='TrackButton_{}'.format(i))
        for i in range(9)]

controls.extend(faders)
controls.extend(encoders)
controls.extend(trackButtons)

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
        "faderMixerMode": (0, 0x22),
        "shift": (0, 0x27)
}

for _name, _arguments in _control_dict.items():
    mc = MIDIControl(*_arguments, name=_name)
    _namespace[_name] = mc
    controls.append(mc)

transport = [_namespace[name] for name in ("rewind", "forward", "stop", "play", "loop", "record")]
