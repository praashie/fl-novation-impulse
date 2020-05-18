# name=Novation Impulse 25/49/61
# url=
# Author: Praash

# Tweakable options
DEBUG = False
INVERT_PAGE_SHIFT = True
FREE_ENCODER_CC_START = 20
LCD_TEST = False

import arrangement
import channels
import device
import midi
import time
import transport
import ui

from flatmate.hooker import *
from flatmate import snippets
import controls

h = bytes.fromhex

SYSEX_HEADER = h("F0 00 20 29 67")
IMPULSE_INIT = h("06 01 01 01")
IMPULSE_DEINIT = h("06 00 00 00")

class EncoderMode(controls.ControllerMode):
    pass

EncoderMode.Free = EncoderMode("FreeCtrl",
            source=controls.encoderPluginMode,
            feedback=controls.encoderPluginMode,
            page=controls.encoderPageUp)
EncoderMode.Mixer = EncoderMode("Mixer",
            source=controls.encoderMixerMode,
            feedback=controls.encoderMixerMode)
EncoderMode.MixerPlugin = EncoderMode("MixerPlug",
            source=controls.encoderMidiMode,
            feedback=controls.encoderMixerMode,
            page=controls.encoderPageDown)

class FaderMode(controls.ControllerMode):
    pass

FaderMode.Mixer = FaderMode("Mixer",
            source=controls.faderMixerMode,
            feedback=controls.faderMixerMode,
            page=controls.mixerBankNext)
FaderMode.Free = FaderMode("FreeCtrl",
            source=controls.faderMidiMode,
            feedback=controls.faderMidiMode,
            page=controls.mixerBankPrevious)

class ImpulseBase:
    def __init__(self):
        for control in controls.controls:
            control.verbose = DEBUG
            Hooker.include(control)

        for t in controls.transport:
            t.set_callback(self.onTransport)

        for e in controls.encoders:
            e.set_callback(self.onEncoder)

        self.encoderSwitcher = controls.ImpulseModeSwitcher(
                modes=(EncoderMode.Free, EncoderMode.Mixer, EncoderMode.MixerPlugin),
                invert=INVERT_PAGE_SHIFT)
        self.encoderSwitcher.set(EncoderMode.Free)
        self.encoderSwitcher.onModeChangeCallback = self.onSwitcherModeChange

        self.faderSwitcher = controls.ImpulseModeSwitcher(
                modes=(FaderMode.Mixer, FaderMode.Free),
                invert=INVERT_PAGE_SHIFT)
        self.faderSwitcher.set(FaderMode.Mixer)
        self.faderSwitcher.onModeChangeCallback = self.onSwitcherModeChange

        self.timeDisplay = False

        self.shift = False
        self.loop = False
        controls.shift.set_callback(self.onModifierButton)
        controls.loop.set_callback(self.onModifierButton)

    def OnInit(self):
        if device.isAssigned():
            self.sysex(IMPULSE_INIT)
            self.lcdText(ui.getProgTitle())

    def OnDeInit(self):
        if device.isAssigned():
            self.sysex(IMPULSE_DEINIT)

    def OnUpdateBeatIndicator(self, value):
        controls.trackButtons[8].sendFeedback(value)
        if value > 0 and self.timeDisplay:
            if transport.getLoopMode():
                timeText = arrangement.currentTimeHint(1, arrangement.currentTime(0))
            else:
                timeText = transport.getSongPosHint()
            self.lcdText(timeText, resetTimeDisplay=False)

    def OnNoteOn(self, event):
        if LCD_TEST:
            self.lcdText(''.join(chr(i) for i in range(event.note, event.note + 8)))
            self.lcdValueText(event.note)

    def lcdText(self, text, command=8, resetTimeDisplay=True):
        if resetTimeDisplay:
            self.timeDisplay = False

        self.sysex(bytes((command,)) + text.encode("ascii", errors="ignore"))

    def lcdValueText(self, value):
        self.lcdText('{:>3}'.format(value), command=9)

    def sysex(self, msg):
        device.midiOutSysex(SYSEX_HEADER + msg)

    transportMap = {
            controls.stop: midi.FPT_Stop,
            controls.play: midi.FPT_Play,
            controls.record: midi.FPT_Record
    }

    def onTransport(self, control, event):
        if control in self.transportMap:
            command = self.transportMap[control]
            transport.globalTransport(command, control.value*10, midi.PME_System | midi.PME_System_Safe)
            if control == controls.play:
                self.timeDisplay = True
            elif control == controls.stop:
                self.timeDisplay = False
        elif control is controls.forward:
            if not self.modShift:
                transport.continuousMove(20, control.value and 2 or 0)
            elif control.value:
                ui.next()
        elif control is controls.rewind:
            if not self.modShift:
                transport.continuousMove(-20, control.value and 2 or 0)
            elif control.value:
                ui.previous()

    def onSwitcherModeChange(self, mode, event):
        self.lcdText(mode.displayName)

    def onEncoder(self, encoder, event):
        if self.encoderSwitcher.mode == EncoderMode.Free:
            event.isIncrement = True

            event.data1 = 400 + encoder.number
            event.controlNum = event.data1
            event.midiChan = 0
            event.status = event.status & 0xF0

            event.outEv = encoder.value

            device.processMIDICC(event)

            event.handled = True

    def onModifierButton(self, control, event):
        if control == controls.shift:
            self.modShift = control.value
        elif control == controls.loop:
            self.modLoop = control.value

impulse = ImpulseBase()

Hooker.include(impulse)
# Hooker.include(snippets.sustainFix)

if DEBUG:
    Hooker.OnMidiIn.attach(snippets.EventDumper("OnMidiIn"))
    Hooker.include(snippets.refreshDumper)

OnUpdateBeatIndicator = impulse.OnUpdateBeatIndicator

# Causes tons of lag
del OnDirtyMixerTrack
