# Novation Impulse MIDI script for FL studio 20.7+

This script is under development. 

# Installation

Download and install [FLatmate](https://github.com/praashie/flatmate).

## Using Git or GitHub Desktop:
Clone the repository directly under your user data script folder.

## Manually
[Download](https://github.com/praashie/fl-novation-impulse/releases) the latest release, and extract the zip file under your user data script folder. Make sure to create a new folder.

# Usage

## Modifier keys

  * `Shift` - hold for alternate actions
  * `Loop` - Reset values, hold for other alternate actions
  * `Master` - Generic DAW control: double-tap to lock, tap again to unlock

## Generic controls

To reset a parameter to its (guessed) default value, hold `Loop` and tweak.

Hold `Shift` and press `Rewind` and `Fast Forward` to select the next/previous item in the active window, such as FLEX presets.

## DAW controls

### Transport
The transport controls work as usual.

  * `Shift+(FastForward/Rewind)`: move playback position in 1 bar increments.
  * `Loop+Play`: toggle Pattern/Song mode
  * Hold `Shift+Loop` or `Master+Loop`: playlist selection

### Menu/Item selection
#### While holding (or locking) `Master`:
  * `Rewind`: Previous item
  * `Forward`: Next item
  * `Stop`: Escape
  * `Play`: Enter = Accept/Select menu item/open sample folder
  * `Record`: Item menu (+`Shift`: "alternate menu")

  "Alakazam!" Piano keys for menu navigation
  * Under development as a generic framework for all MIDI controllers
  * Regardless of the octave, the piano keys control the following:
    * F: Escape
    * F#: No
    * G: Enter
    * G#: Yes
    * "Arrow keys"
      * A: Left
      * A#: Up
      * B: Down
      * C: Right

### Jog control
#### While holding (or locking `Master`):
  * Tweak encoders:
    * 1: Jog (+`Shift`: Alternate Jog)
    * 2: Horizontal zoom (+`Shift`: Vertical Zoom)
    * 3-4: _unassigned_
    * 5: Mixer track selection
    * 6: Pattern selection
    * 7: Channel selection
    * 8: Window selection

### Window shortcuts
#### While holding (or locking) `Master`:
Track buttons become window shortcuts:
  * 1: Mixer
  * 2: Channel rack
  * 3: Playlist
  * 4: Piano roll
  * 5: Browser

### Recording options
`Loop+Record`: Toggle loop recording
`Shift+Record`: Toggle overdub
`Shift+Loop+Record`: Toggle step editing mode
`Shift+Loop+Master`: Toggle recording countdown

### Metronome
The `Master` button under the Master fader flashes in tempo. Press `Loop+Master` to toggle the metronome.

### Tap tempo
Press the two buttons under the drum pads simultaneously to activate the "Clip Launching" mode.
When active, holding `Shift` will highlight the bottom left pad (labeled "Tap") in green - tap to set the project tempo.

## Assignable controls

### Encoders

Press `Shift+Plugin` next to the encoders to change modes to `FreeCtrl`.
Holding `Shift` provides a secondary controller, which suits EQ freq/width perfectly.
Press `Plugin` and `MIDI` without `Shift` to change between 4 (customizable!) encoder pages.
Each page holds 2x8 assignable controllers, with each page sending on a different MIDI channel.

### Faders

Press `Shift+MIDI` to put the faders in MIDI mode, which will send regular MIDI CC messages depending on the Impulse's settings. Press `Mixer` next to faders to reset.

## Mixer

The faders and encoders are set to Mixer mode by default.

### Volume
Move the faders to control track volume.
The fader ticks do not align well; this will be refined in the future.

### Pan & Stereo separation
Tweak the encoders to tweak panning. Hold `Shift` while tweaking to edit stereo separation.

### Bank navigation
To select a different set of 8 mixer tracks, use the Mixer/MIDI buttons (without using Shift; configurable).
Use `Shift` + `Octave` buttons to change the mixer tracks one at a time.
When changing the active tracks, the display will reflect the name of the leftmost track

### Mute & Solo

Press the `Mute/Solo` button to toggle the activated mode. When in Solo mode, the buttons will flash according to track peaks.

### Track selection
To highlight a track in the mixer, hold `Shift` and press the corresponding track button. The LCD will display the track name. Selecting a track will also cycle through any channels routed to that track, one by one.

## Preview mode

Press `Shift+Control` to activate Preview mode on the Impulse. Tweaking any control will display the name of the corresponding parameter it is currently bound to.

## Planned features

* Clip launching with pads
    
