# https://github.com/praashie/fl-novation-impulse

import controls

class ControllerModeSwitch:
    def __init__(self, modes, source, feedback, page=None, exitOnPage=False):
        self.modes = modes
        self.current_mode_index = 0

        self.sourceControl = source
        self.feedbackControl = feedback
        self.pageSourceControl = page

        self.callback = None
        self.pageCallback = None
        self.exitOnPage = exitOnPage

        self.sourceControl.set_callback(self.onControl)
        if self.pageSourceControl:
            self.pageSourceControl.set_callback(self.onControl)

        for m in modes:
            m.modeController = self

    def feedback(self):
        self.feedbackControl.sendFeedback(self.feedbackControl.value)

    def onControl(self, control, event):
        if control == self.sourceControl:
            self.callback(self, control, event)
        elif control == self.pageSourceControl:
            self.pageCallback(self, control, event)

    def cycleModes(self, reset=False):
        if reset:
            self.current_mode_index = 0
        else:
            self.current_mode_index = (self.current_mode_index + 1) % len(self.modes)

    def getMode(self):
        return self.modes[self.current_mode_index]

class ControllerMode:
    def __init__(self, displayName):
        self.displayName = displayName
        self.modeController = None

    def feedback(self):
        self.modeController.feedback()

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

    def onModeButton(self, modeController, control, event):
        self.previous = self.mode

        modeController.cycleModes()
        self.mode = modeController.getMode()
        if callable(self.onModeChangeCallback):
            control = modeController.sourceControl
            self.onModeChangeCallback(self.mode, event)
        self.set(modeController.getMode())

    def onPageChange(self, mode, control, event):
        if self.mode.modeController.exitOnPage:
            return self.onModeButton(mode, control, event)

        if callable(self.onPageChangeCallback):
            control = mode.pageSourceControl
            self.onPageChangeCallback(control, event)
        self.set(self.mode)

    def set(self, mode):
        self.mode = mode
        mode.feedback()

class EncoderMode:
    Free = ControllerMode("FreeCtrl")
    Mixer = ControllerMode("Mixer")
    MixerPlugin = ControllerMode("MixerPlugin")
    Jogs = ControllerMode("FL Jogs")

    PluginButton = ControllerModeSwitch(
            modes=(Free, MixerPlugin),
            source=controls.encoderPluginMode,
            feedback=controls.encoderPluginMode,
            page=controls.encoderPageUp)

    MixerButton = ControllerModeSwitch(
            modes=(Mixer,),
            source=controls.encoderMixerMode,
            feedback=controls.encoderMixerMode)

    MidiButton = ControllerModeSwitch(
            (Jogs,),
            source=controls.encoderMidiMode,
            feedback=controls.encoderMixerMode,
            page=controls.encoderPageDown)

    Switchers = (PluginButton, MixerButton, MidiButton)

class FaderMode:
    Mixer = ControllerMode("Mixer")
    Free = ControllerMode("FreeCtrl")

    MixerButton = ControllerModeSwitch(
            modes=(Mixer,),
            source=controls.faderMixerMode,
            feedback=controls.faderMixerMode,
            page=controls.mixerBankNext)

    MidiButton = ControllerModeSwitch(
            modes=(Free,),
            source=controls.faderMidiMode,
            feedback=controls.faderMidiMode,
            page=controls.mixerBankPrevious,
            exitOnPage=True)

    Switchers = (MixerButton, MidiButton)

