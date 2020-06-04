# name=Novation Impulse 25/49/61
# url=https://forum.image-line.com/viewtopic.php?f=1994&t=229878
# Author: Praash
# https://github.com/praashie/fl-novation-impulse


# Tweak these options to your liking.

# Change pages without Shift, hold Shift to change encoder/fader modes
INVERT_PAGE_SHIFT = True

ENCODER_SCALE = 1 / 200.0

ENCODER_FINETUNE = False
ENCODER_FINETUNE_THRESHOLD = 1 # Maximum speed to use fine tuning with
ENCODER_SCALE_FINE = 1 / 400.0
FREE_ENCODER_CC_START = 20

# minimum delay between LCD updates
LCD_THROTTLE = 0.1

LCD_TEST = False
DEBUG = False # causes lag!

import arrangement
import channels
import device
import midi
import time
import transport
import ui

from flatmate import flags as Flags
from flatmate import snippets
from flatmate.control import MIDIControl
from flatmate.hooker import *
from flatmate.lcd import MidiLCD
from flatmate.midi import setEventMidiChannel
from flatmate.mixer import MixerController

import controls
from modes import EncoderMode, FaderMode, ImpulseModeSwitcher

import rec

h = bytes.fromhex

SYSEX_HEADER = h("F0 00 20 29 67")
IMPULSE_INIT = h("06 01 01 01")
IMPULSE_DEINIT = h("06 00 00 00")

class ImpulseBase:
    def __init__(self):
        for control in controls.controls:
            control.verbose = DEBUG
            control.throttling = True

        for t in controls.transport:
            t.set_callback(self.onTransport)

        for e in controls.encoders:
            e.set_callback(self.onEncoder)

        for f in controls.faders:
            f.set_callback(self.onFader)

        for b in controls.trackButtons:
            if b.index == 8: # Master
                b.set_callback(self.onMasterButton)
            else:
                b.set_callback(self.onTrackButton)

        for p in controls.clipPads:
            p.set_callback(self.onClipPad)

        self.encoderSwitcher = ImpulseModeSwitcher(
                modes=(EncoderMode.Free, EncoderMode.Mixer, EncoderMode.MixerPlugin),
                invert=INVERT_PAGE_SHIFT)
        self.encoderSwitcher.set(EncoderMode.Free)
        self.encoderSwitcher.onModeChangeCallback = self.onSwitcherModeChange

        self.faderSwitcher = ImpulseModeSwitcher(
                modes=(FaderMode.Mixer, FaderMode.Free),
                invert=INVERT_PAGE_SHIFT)
        self.faderSwitcher.set(FaderMode.Mixer)
        self.faderSwitcher.onModeChangeCallback = self.onSwitcherModeChange
        self.faderSwitcher.onPageChangeCallback = self.onMixerPageChange

        self.lcd_text = MidiLCD(sysex_prefix=SYSEX_HEADER + h('08'),
                width=8, minInterval=LCD_THROTTLE)
        self.lcd_value = MidiLCD(sysex_prefix=SYSEX_HEADER + h('09'),
                width=3, minInterval=LCD_THROTTLE)

        self.timeDisplay = False

        controls.shift.set_callback(self.onModifierButton)
        controls.loop.set_callback(self.onModifierButton)
        controls.preview.set_callback(self.onModifierButton)

        controls.mixerTrackNext.set_callback(self.onMixerTrackButton)
        controls.mixerTrackPrevious.set_callback(self.onMixerTrackButton)

        self.mixer = MixerController(track_width=8)

        self.soloMode = False
        controls.faderMixerMode.onSoloModeCallback = self.onSoloModeButton

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

    def lcdText(self, text, resetTimeDisplay=True, **kwargs):
        if resetTimeDisplay:
            self.timeDisplay = False

        self.lcd_text.write(text, **kwargs)

    def lcdValueText(self, value):
        self.lcd_value.write(value, align='>')

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
            if not controls.shift.value:
                transport.continuousMovePos(5, control.value * 2)
            elif control.value:
                ui.next()
        elif control is controls.rewind:
            if not controls.shift.value:
                transport.continuousMovePos(-5, control.value * 2)
            elif control.value:
                ui.previous()
        else:
            return
        event.handled = True

    def onSwitcherModeChange(self, mode, event):
        self.lcdText(mode.displayName)
        event.handled = True

    def onEncoder(self, encoder, event):
        if self.encoderSwitcher.mode == EncoderMode.Mixer:
            track = self.mixer.tracks[encoder.index]
            if controls.shift.value:
                targetEvent = track.stereoSeparation
            else:
                targetEvent = track.pan

            if self.tryControllingTargetEvent(targetEvent, fl_event=event):
                if ENCODER_FINETUNE and abs(encoder.value) <= ENCODER_FINETUNE_THRESHOLD:
                    scale = ENCODER_SCALE_FINE
                else:
                    scale = ENCODER_SCALE
                targetEvent.setIncrement(encoder.value * scale)

        elif self.encoderSwitcher.mode == EncoderMode.Free:

            # Holding Shift gives alternate controls!
            cc_offset = controls.shift.value * len(controls.encoders)
            event.data1 = FREE_ENCODER_CC_START + encoder.ccNumber + cc_offset
            event.inEv = encoder.value
            event.outEv = encoder.value
            event.isIncrement = True

            virtualControl = MIDIControl(channel=encoder.channel, ccNumber=event.data1)
            targetEvent = virtualControl.getLinkedRECEvent()

            if not targetEvent or self.tryControllingTargetEvent(targetEvent):
                device.processMIDICC(event)

        if targetEvent is not None:
            self.displayEventFeedback(targetEvent, encoder)

        event.handled = True

    def onFader(self, fader, event):
        if self.faderSwitcher.mode == FaderMode.Mixer:
            fader_float = fader.value / 127.0
            if fader.index == 8: # Master
                target_event = rec.MainVol
            else:
                target_event = self.mixer.tracks[fader.index].volume

            if self.tryControllingTargetEvent(target_event, fl_event=event):
                target_event.setValue(fader.value / 127.0, max=1.25)
            self.displayEventFeedback(target_event, fader, max=1.25)

        event.handled = True

    def tryControllingTargetEvent(self, targetEvent, fl_event=None):
        if fl_event and not (fl_event.pmeFlags & Flags.PME.System_Safe):
            return False
        if controls.preview.value:
            targetEvent.touch()
            return False
        elif controls.loop.value:
            targetEvent.resetValue()
            return False
        else:
            return True

    def onModifierButton(self, control, event):
        event.handled = True

    def onMixerPageChange(self, control, event):
        if control == controls.mixerBankNext:
            self.mixer.bankUp()
            self.mixer.selectBank(focus=self.mixer.track_width)
        elif control == controls.mixerBankPrevious:
            self.mixer.bankDown()
            self.mixer.selectBank()

            self.lcdValueText(self.mixer.bank_start)

        self.lcdText(self.mixer.tracks[0].getName())

        event.handled = True

    def onTrackButton(self, control, event):
        event.handled = True
        track = self.mixer.tracks[control.index]

        if control.value == 0:
            return
        elif controls.shift.value:
            track.select(single=True)
            self.selectMixerTrackChannel(track.index)
        elif self.soloMode:
            track.solo(flags=midi.fxSoloModeWithSourceTracks + midi.fxSoloModeWithDestTracks)
        else:
            track.mute()

        self.refreshTrackLed(control.index, track)
        self.lcdText(track.getName())
        self.lcdValueText(track.index)

        event.handled = True

    def onMasterButton(self, control, event):
        transport.globalTransport(midi.FPT_Metronome, control.value)

    def onSoloModeButton(self, control, event):
        self.soloMode = not bool(control.value)
        event.handled = True

    def onMixerTrackButton(self, control, event):
        if control == controls.mixerTrackNext:
            self.mixer.trackUp()
            self.mixer.selectBank(focus=self.mixer.track_width)
        elif control == controls.mixerTrackPrevious:
            self.mixer.trackDown()
            self.mixer.selectBank()

    def displayEventFeedback(self, recEvent, controller=None, min=0.0, max=1.0):
        context, sep, parameter = recEvent.getSplitName()

        parameter = parameter[:3]
        text_parts = (context, '-', parameter, ':', recEvent.getValueString())
        self.lcd_text.writeParts(text_parts)

        if controller is not None:
            percentage = int(recEvent.getFloat(min=min, max=max) * 100.0)
            controller.sendFeedback(percentage)

    def OnIdle(self):
        self.refreshTrackLeds()
        self.refreshPads()

    def OnRefresh(self, flags):
        if flags & (Flags.HW_Dirty.LEDs):
            self.refreshTrackLeds()

    def refreshTrackLeds(self):
        for i, track in enumerate(self.mixer.tracks):
            self.refreshTrackLed(i, track)

    def refreshPads(self):
        for pad in controls.clipPads:
            if controls.shift.value and pad.index == 4:
                pad.setColor(green=2, flash=False)
            else:
                pad.setColor(red=0, green=0, flash=False)

    def refreshTrackLed(self, index, track):
        if self.soloMode:
            value = (track.getPeaks() > 0.1)
        else:
            value = 1 - track.isMuted()
        controls.trackButtons[index].sendFeedback(value)

    def onClipPad(self, control, event):
        if control.index == 4 and controls.shift.value:
            transport.globalTransport(midi.FPT_TapTempo, control.value)
        event.handled = True

    def OnPitchBend(self, event):
        # Sets the port to 0 too, to preserve universal pitch bending
        event.midiChanEx = event.midiChan

    def selectMixerTrackChannel(self, track_index):
        current_channel = channels.channelNumber()
        channel_count = channels.channelCount()

        for i in range(channel_count):
            # If multiple channels match, select the next matching one
            channel_index = (current_channel + i) % channel_count
            if channels.getTargetFxTrack(channel_index) == track_index:
                channels.selectChannel(channel_index, 1)
                return channel_index


impulse = ImpulseBase()


Hooker.include(impulse)

if DEBUG:
    Hooker.OnControlChange.attach(snippets.EventDumper("OnControlChange"))
    Hooker.include(snippets.refreshDumper)

Hooker.include(snippets.sustainFix)

OnUpdateBeatIndicator = impulse.OnUpdateBeatIndicator

del OnDirtyMixerTrack
