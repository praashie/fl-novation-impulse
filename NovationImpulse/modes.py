# https://github.com/praashie/fl-novation-impulse

import controls

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

class EncoderMode(ControllerMode):
    Free = ControllerMode("FreeCtrl",
            source=controls.encoderPluginMode,
            feedback=controls.encoderPluginMode,
            page=controls.encoderPageUp)

    Mixer = ControllerMode("Mixer",
            source=controls.encoderMixerMode,
            feedback=controls.encoderMixerMode)

    MixerPlugin = ControllerMode("MixerPlug",
            source=controls.encoderMidiMode,
            feedback=controls.encoderMixerMode,
            page=controls.encoderPageDown)

class FaderMode(ControllerMode):
    Mixer = ControllerMode("Mixer",
            source=controls.faderMixerMode,
            feedback=controls.faderMixerMode,
            page=controls.mixerBankNext)
    Free = ControllerMode("FreeCtrl",
            source=controls.faderMidiMode,
            feedback=controls.faderMidiMode,
            page=controls.mixerBankPrevious,
            exitOnPage=True)
