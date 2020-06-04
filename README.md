# Novation Impulse MIDI script for FL studio 20.7+

This script is under development. 

# Installation

Download and install [FLatmate](https://github.com/praashie/flatmate).

## Using Git or GitHub Desktop:
Clone the repository directly under your user data script folder.

## Manually
[Download](https://github.com/praashie/fl-novation-impulse/releases) the latest release, and extract the zip file under your user data script folder. Make sure to create a new folder.

# Usage

## Generic controls

To reset a parameter to its (guessed) default value, hold `Loop` and tweak.

Hold `Shift` and press `Rewind` and `Fast Forward` to select the next/previous item in the active window, such as FLEX presets.

### Metronome

The button under the Master fader flashes in tempo. Press to toggle the metronome.

### Tap tempo

Press the two buttons under the drum pads simultaneously to activate the "Clip Launching" mode.
When active, holding `Shift` will highlight the bottom left pad (labeled "Tap") in green - tap to set the project tempo.

## Assignable controls

### Encoders

Press `Shift+Plugin` next to the encoders to make them freely assignable.
Holding `Shift` provides a secondary controller, which suits EQ freq/width perfectly.

### Faders

Press `Shift+MIDI` to put the faders in MIDI mode, which will send regular MIDI CC messages depending on the Impulse's settings.

## Mixer

The faders are set to Mixer mode by default.
Switch the encoders to Mixer mode by pressing Plugin and MIDI together.
At the moment, only panning is implemented for the encoders.

Move the faders to control track volume.
The fader ticks do not align well; this will be refined in the future.
To select a different set of 8 mixer tracks, use the Mixer/MIDI buttons (without using Shift; configurable).
Use `Shift` + `Octave` buttons to change the mixer tracks one at a time.
When changing the active tracks, the display will reflect the name of the leftmost track

To reset a value to its default position, hold the Loop button while tweaking the control.

### Mute & Solo

Press the `Mute/Solo` button to toggle the activated mode. When in Solo mode, the buttons will flash according to track peaks.

### Track selection
To highlight a track in the mixer, hold `Shift` and press the corresponding track button. The LCD will display the track name.

## Preview mode

Press `Shift+Control` to activate Preview mode on the Impulse. Tweaking any control will display the name of the corresponding parameter it is currently bound to.

## Planned features

* Clip launching with pads
* More shortcuts for opening/switching windows
* Generic jog control with encoders
