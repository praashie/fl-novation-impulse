# Novation Impulse MIDI script for FL studio 20.7+

This script is under development. 

## Installation
[Download](https://github.com/praashie/fl-novation-impulse/releases) the latest release.
Copy the folder `NovationImpulse` under your user data script folder.
Download and install [FLatmate](https://github.com/praashie/flatmate).

## Usage

### Generic controls
Press `Shift+Plugin` next to the encoders to make them freely assignable.
Holding `Shift` provides a secondary controller, which suits EQ freq/width perfectly.
To reset a parameter to its (guessed) default value, hold `Loop` and tweak.

Hold `Shift` and press `Rewind` and `Fast Forward` to select the next/previous item in the active window, such as FLEX presets.
### Mixer
The faders are set to Mixer mode by default.
Switch the encoders to Mixer mode by pressing Plugin and MIDI together.
At the moment, only panning is implemented for the encoders.

Move the faders to control track volume.
The fader ticks do not align well; this will be refined in the future.
To select a different set of 8 mixer tracks, use the Mixer/MIDI buttons (without using Shift; configurable).
Use `Shift` + `Octave` buttons to change the mixer tracks one at a time.
When changing the active tracks, the display will reflect the name of the leftmost track

To reset a value to its default position, hold the Loop button while tweaking the control.

### Metronome

The button under the Master fader flashes in tempo. Press to toggle the metronome.

### Tap tempo

Press the two buttons under the drum pads simultaneously to activate the "Clip Launching" mode.
When active, hold `Shift` and tap the drum pad that is highlighted in green.



## Planned features

* Clip launching with pads
* More shortcuts for opening/switching windows
* Generic jog control with encoders
