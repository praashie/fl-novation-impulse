# name=Novation Impulse 25/49/61
# url=

import fl
import patterns
import mixer
import device
import transport
import arrangement
import general
import playlist
import ui
import channels

import midi
import utils
import time

import flatmate

h = bytes.fromhex

SYSEX_HEADER = h("F0 00 20 29 67")
IMPULSE_INIT = h("06 01 01 01")
IMPULSE_DEINIT = h("06 00 00 00")

class Impulse:
    def __init__(self):
        pass

    def OnInit(self):
        device.midiOutSysex(SYSEX_HEADER + IMPULSE_INIT)

    def OnDeInit(self):
        device.midiOutSysex(SYSEX_HEADER + IMPULSE_DEINIT)

    def OnDirtyMixerTrack(self, SetTrackNum):
        pass

    def OnRefresh(self, Flags):
        pass

    def OnMidiMsg(self, event):
        self.last_event = event

    def OnSendTempMsg(self, Msg, Duration = 1000):
        pass

    def OnUpdateBeatIndicator(self, Value):
        pass

    def OnUpdateMeters(self):
        pass

    def OnIdle(self):
        pass

    def OnWaitingForInput(self):
        pass

impulse = Impulse()

module = globals()
module.update([
    (attr, getattr(impulse, attr)) for attr in dir(impulse)
    if not attr.startswith('__')
])
