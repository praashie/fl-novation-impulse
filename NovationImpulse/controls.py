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

class ControllerMode:
    def __init__(self, displayName, source, feedback, page=None, exitOnPage=False):
        self.displayName = displayName
        self.sourceControl = source
        self.feedbackControl = feedback
        self.pageSourceControl = page

        self.callback = None
        self.pageCallback = None
        self.exitOnPage = exitOnPage

        self.sourceControl.set_callback(self.onControl)
        if self.pageSourceControl:
            self.pageSourceControl.set_callback(self.onControl)

    def feedback(self):
        self.feedbackControl.sendFeedback(self.feedbackControl.value)

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
            control = mode.sourceControl
            self.onModeChangeCallback(mode, event)
        self.set(mode)

    def onPageChange(self, mode, control, event):
        if self.mode.exitOnPage:
            return self.onModeButton(mode, control, event)

        if callable(self.onPageChangeCallback):
            control = mode.pageSourceControl
            self.onPageChangeCallback(control, event)
        self.set(self.mode)

    def set(self, mode):
        self.mode = mode
        mode.feedback()

controls = []

faders = [MIDIControl(channel=0, ccNumber=i, index=i,
    name='Fader_{}'.format(i + 1)) for i in range(9)]

encoders = [ImpulseEncoder(channel=1, ccNumber=i, index=i,
    name='Encoder_{}'.format(i + 1)) for i in range(8)]

trackButtons = [MIDIControl(channel=0, ccNumber=i+0x09, index=i,
    name='TrackButton_{}'.format(i)) for i in range(9)]

modwheel = MIDIControl(channel=2, ccNumber=0x01, name='ModWheel')

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
