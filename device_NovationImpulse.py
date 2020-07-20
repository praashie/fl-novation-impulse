# name=Novation Impulse 25/49/61
# url=https://forum.image-line.com/viewtopic.php?f=1994&t=229878
# Author: Praash
# https://github.com/praashie/fl-novation-impulse


# Tweak these options to your liking.

# Change pages without Shift, hold Shift to change encoder/fader modes
INVERT_PAGE_SHIFT = True

# How quickly the Master button must be double-tapped to lock
MASTER_LOCK_TIMEOUT = 0.3

ENCODER_SCALE = 1 / 200.0

ENCODER_FINETUNE = False
ENCODER_FINETUNE_THRESHOLD = 1 # Maximum speed to use fine tuning with
ENCODER_SCALE_FINE = 1 / 400.0

FREE_ENCODER_CC_START = 20
FREE_ENCODER_PAGES = 4

# minimum delay between LCD updates
LCD_THROTTLE = 0.1

LCD_TEST = False
DEBUG = False # causes lag!

import arrangement
import channels
import device
import general
import midi
import mixer
import patterns
import time
import transport
import ui

from flatmate.alakazam import Alakazam

from flatmate import flags
from flatmate import snippets
from flatmate.control import MIDIControl
from flatmate.hooker import *
from flatmate.lcd import MidiLCD, MidiLCDParts
from flatmate.midi import setEventMidiChannel
from flatmate.mixer import MixerController, MixerTrack


import controls
from modes import EncoderMode, FaderMode, ImpulseModeSwitcher

import fpt
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
            b.set_callback(self.onTrackButton)

        for p in controls.clipPads:
            p.set_callback(self.onClipPad)

        controls.dataKnob.set_callback(self.handleJog)

        self.encoderSwitcher = ImpulseModeSwitcher(
                modes=EncoderMode.Switchers,
                invert=INVERT_PAGE_SHIFT)
        self.encoderSwitcher.onModeChangeCallback = self.onSwitcherModeChange
        self.encoderSwitcher.onPageChangeCallback = self.onEncoderPageChange
        self.encoderSwitcher.page = 0

        self.faderSwitcher = ImpulseModeSwitcher(
                modes=FaderMode.Switchers,
                invert=INVERT_PAGE_SHIFT)
        self.faderSwitcher.onModeChangeCallback = self.onSwitcherModeChange
        self.faderSwitcher.onPageChangeCallback = self.onMixerPageChange

        self.lcd_text = MidiLCDParts(sysex_prefix=SYSEX_HEADER + h('08'),
                width=8, minInterval=LCD_THROTTLE)
        self.lcd_value = MidiLCD(sysex_prefix=SYSEX_HEADER + h('09'),
                width=3, minInterval=LCD_THROTTLE)

        self.timeDisplay = False

        controls.shift.set_callback(self.onModifierButton)
        controls.loop.set_callback(self.onModifierButton)
        controls.preview.set_callback(self.onModifierButton)
        controls.masterButton.set_callback(self.onModifierButton)
        controls.masterButton.timeout = MASTER_LOCK_TIMEOUT

        controls.mixerTrackNext.set_callback(self.onMixerTrackButton)
        controls.mixerTrackPrevious.set_callback(self.onMixerTrackButton)

        self.mixer = MixerController(track_width=8)

        self.soloMode = False
        controls.faderMixerMode.onSoloModeCallback = self.onSoloModeButton

    def OnInit(self):
        if device.isAssigned():
            self.sysex(IMPULSE_INIT)
            self.encoderSwitcher.set(EncoderMode.Mixer)
            self.faderSwitcher.set(FaderMode.Mixer)
            self.lcdText(ui.getProgTitle())

    def OnDeInit(self):
        if device.isAssigned():
            self.sysex(IMPULSE_DEINIT)

    def OnUpdateBeatIndicator(self, value):
        controls.masterButton.sendFeedback(value)
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

    def onTransport(self, control, event):
        result = fpt.handleTransport(control, event)
        if result:
            if control == controls.play:
                self.timeDisplay = True
            elif control == controls.stop:
                self.timeDisplay = False
            else:
                self.lcdText(result)
        elif control in (controls.forward, controls.rewind):
            direction = (1 if control is controls.forward else -1)
            if controls.shift.value and control.value: # Fixed steps. Hacky. Please fix the API.
                ppb = general.getRecPPB()
                move_ticks = direction * ppb

                song_length_ticks = transport.getSongLength(midi.SONGLENGTH_ABSTICKS)
                current_pos_ticks = transport.getSongPos() * song_length_ticks

                next_pos_ticks = current_pos_ticks + move_ticks
                next_pos_ticks = round(next_pos_ticks / ppb) * ppb
                # Hacky snap
                transport.setSongPos(next_pos_ticks / (song_length_ticks or 1))
            else:
                transport.continuousMovePos(5 * direction, control.value * 2)

        event.handled = True

    def onSwitcherModeChange(self, mode, event):
        self.lcdText(mode.displayName)
        event.handled = True

    encoderJogs = {
        False: {
            0: ("Jog", "Jog"),
            1: ("HZoomJog", "HZoom"),
            9001: ("Jog", "Jog")
        },
        True: {
            0: ("Jog2", "Jog2"),
            1: ("VZoomJog", "VZoom"),
            9001: ("MoveJog", "Move")
        }
    }

    def onEncoder(self, encoder, event):
        targetEvent = None
        if controls.masterButton.value or self.encoderSwitcher.mode == EncoderMode.Jogs:
            self.handleJog(encoder, event)
        elif self.encoderSwitcher.mode == EncoderMode.Mixer:
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
            setEventMidiChannel(event, self.encoderSwitcher.page)

            virtualControl = MIDIControl(channel=self.encoderSwitcher.page, ccNumber=event.data1)
            targetEvent = virtualControl.getLinkedRECEvent()

            if not targetEvent or self.tryControllingTargetEvent(targetEvent):
                device.processMIDICC(event)

        if targetEvent is not None:
            self.displayEventFeedback(targetEvent, encoder)

        event.handled = True

    def handleJog(self, encoder, event):
        display_message = ''
        display_value = None

        i = encoder.index
        jogmap = self.encoderJogs[controls.shift.value]
        if i in jogmap:
            target, display_message = jogmap[i]
            fpt.callFPT(target, encoder.value, event)

            direction = '>' if encoder.value > 0 else '<'
            display_message += ' ' + direction
        elif i == 4:
            selected_track = self.moveSelectedMixerTrack(encoder.value)
            display_message = mixer.getTrackName(selected_track)
            display_value = selected_track
        elif i == 5:
            selected_pattern = (patterns.patternNumber() + encoder.value) % patterns.patternMax()
            patterns.jumpToPattern(selected_pattern)
            display_message = patterns.getPatternName(selected_pattern)
            display_value = selected_pattern
        elif i == 6:
            group_channel_count = channels.channelCount(0)
            current_channel = channels.channelNumber(0)
            selected_group_index = self.cycleChannels(
                current=0,
                count=group_channel_count,
                condition_func=lambda c: channels.getChannelIndex(c) == current_channel
            ) or 0
            selected_index = (selected_group_index + encoder.value) % group_channel_count
            channels.deselectAll()
            channels.selectChannel(selected_index)
            display_message = channels.getChannelName(selected_index)
            display_value = selected_index

        self.lcdText(display_message)
        if display_value:
            self.lcdValueText(display_value)

    def onFader(self, fader, event):
        if self.faderSwitcher.mode == FaderMode.Mixer:
            fader_float = fader.value / 127.0
            if fader.index == 8: # Master
                if controls.masterButton.value:
                    target_event = rec.MainVol
                else:
                    target_event = MixerTrack(mixer.trackNumber()).volume
            else:
                target_event = self.mixer.tracks[fader.index].volume

            if self.tryControllingTargetEvent(target_event, fl_event=event):
                target_event.setValue(fader_float, max=1.25)
            self.displayEventFeedback(target_event, fader, max=1.25)

        event.handled = True

    def tryControllingTargetEvent(self, targetEvent, fl_event=None):
        if fl_event and not (fl_event.pmeFlags & flags.PME.System_Safe):
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
        if control == controls.masterButton:
            if control.value and not control.holding:
                Alakazam.activate()
            else:
                Alakazam.deactivate()

            if control.holding:
                self.lcdText("MstrLock")
        self.onTransport(control, event)

    def onMixerPageChange(self, control, event):
        event.handled = True
        if control == controls.mixerBankNext:
            self.mixer.bankUp()
        elif control == controls.mixerBankPrevious:
            self.mixer.bankDown()

        self.mixer.selectBank()
        self.lcdValueText(self.mixer.bank_start)
        self.lcdText(self.mixer.tracks[0].getName())

    def onEncoderPageChange(self, control, event):
        event.handled = True
        if self.encoderSwitcher.mode == EncoderMode.Free:
            if control == controls.encoderPageUp:
                page_delta = 1
            elif control == controls.encoderPageDown:
                page_delta = -1
            self.encoderSwitcher.page = (self.encoderSwitcher.page + page_delta) % FREE_ENCODER_PAGES

            self.lcdText("Page {}".format(self.encoderSwitcher.page))
            self.lcdValueText(self.encoderSwitcher.page)

    def onTrackButton(self, control, event):
        event.handled = True
        track = self.mixer.tracks[control.index]

        if control.value == 0:
            return
        if controls.masterButton.value:
            if control.index <= midi.widBrowser:
                ui.showWindow(control.index)
                self.lcdText(ui.getFocusedFormCaption())
        else:
            if self.soloMode:
                track.select(single=True)
                self.selectMixerTrackChannel(track.index)
            elif control.double_click:
                track.solo(flags=midi.fxSoloModeWithSourceTracks + midi.fxSoloModeWithDestTracks)
            else:
                track.mute()

            self.refreshTrackLed(control.index, track)
            self.lcdText(track.getName())
            self.lcdValueText(track.index)

    def onMasterButton(self, control, event):
        event.handled = True
        if controls.loop.value:
            transport.globalTransport(midi.FPT_Metronome, control.value)

    def onSoloModeButton(self, control, event):
        self.soloMode = not bool(control.value)
        event.handled = True

    def onMixerTrackButton(self, control, event):
        if control == controls.mixerTrackNext:
            selected_track = self.moveSelectedMixerTrack(1)
        elif control == controls.mixerTrackPrevious:
            selected_track = self.moveSelectedMixerTrack(-1)
        self.lcdText(mixer.getTrackName(selected_track))

    def displayEventFeedback(self, recEvent, controller=None, min=0.0, max=1.0):
        context, sep, parameter = recEvent.getSplitName()

        if context and parameter:
            parameter_full = (context, '-', parameter)
        else:
            parameter_full = (context or parameter,)

        text_parts = parameter_full + (':', recEvent.getValueString())
        self.lcd_text.writeParts(text_parts)

        if controller is not None:
            percentage = int(recEvent.getFloat(min=min, max=max) * 100.0)
            controller.sendFeedback(percentage)

    def OnIdle(self):
        self.refreshTrackLeds()
        self.refreshPads()

    def refreshTrackLeds(self):
        if self.faderSwitcher.mode == FaderMode.Mixer:
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
            self.lcdText("TapTempo")
        event.handled = True

    def OnPitchBend(self, event):
        # Sets the port to 0 too, to preserve universal pitch bending
        event.midiChanEx = event.midiChan

    def selectMixerTrackChannel(self, track_index):
        current = channels.channelNumber()
        count = channels.channelCount()
        return self.cycleChannels(current, count,
                lambda i: channels.getTargetFxTrack(i) == track_index)

    def moveSelectedMixerTrack(self, offset):
        selected_track = (mixer.trackNumber() + offset) % mixer.trackCount()
        mixer.setTrackNumber(selected_track)
        return selected_track

    def cycleChannels(self, current, count, condition_func):
        for i in range(count):
            # If multiple channels match, select the next matching one
            channel_index = (current + i) % count
            if condition_func(channel_index):
                channels.selectChannel(channel_index, 1)
                return channel_index


impulse = ImpulseBase()
Hooker.include(impulse)

if DEBUG:
    Hooker.OnControlChange.attach(snippets.EventDumper("OnControlChange"))
    Hooker.include(snippets.refreshDumper)

# Hooker.include(snippets.sustainFix)
OnUpdateBeatIndicator = impulse.OnUpdateBeatIndicator

del OnDirtyMixerTrack
del OnRefresh
