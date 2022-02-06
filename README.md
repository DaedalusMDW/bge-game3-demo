# bge-game3-demo
A set of classes and code built around the bge-game3-core to demonstrate the most prominent features.

## Quick tips:
- keybinds are fully customizable but the common defaults are
  - WSAD to move, C/SPACE to jump/crouch
  - V toggle third person
  - R to toggle camera orbit/follow
  - X activate weapons
  - middle mouse to interact
  - F is a generic mode toggle
    - the player will float around for travel assist, shift for boost
    - aircraft toggle landing gear
  - alt-` will drop all attachments, alt-number will drop specific attachment
  - alt-pageup will snap you to the ground if you fall through
  - alt-backspace is a "break glass in emergency" if you get stuck (may cause bugs)
- use ESC to open pause menu, f12 for screenshot
- you can back out to launcher/menu and resume at any time
- use the SAVE and LOAD buttons to save the session to a file (do this when a bug occures and include with issue)

## How to build:
- unzip the packaged game3 release "bge_game3_core-xxxxxx" to a folder called `game3`.  this folder should only contain py files and a blend.
- go the the current upload site and "Download All".
  - https://drive.google.com/drive/folders/13nl_B-knwAJ2afuhTZqTfIXukIc1dGxZ?usp=sharing
  - extract the zip and paste the `CONTENT`, `MAPS`, `TEXTURES` into the project folder
- download the bin exe to run the demo without the need of blender upbge 0.2.0.
  - https://drive.google.com/file/d/1Kvwysta-Fcy0yc3VGIf0c5PJL7AZYHwF/view?usp=sharing
  - extract the zip and paste the `bin64` in the project folder.
- run the LaunchDemo.cmd to play.
