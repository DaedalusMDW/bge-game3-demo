# bge-game3-demo
A set of classes and code built around the bge-game3-core to demonstrate the most prominent features.

## Whats demonstrated?
There is a continually expanding collection of example content to provide a variety of examples for use of game3's feature set, also constantly expanding and evolving.  With that said, the purpose of this is a collection of examples assembled into a playable environment.  UX and UI are the minimum effective solution and i advise visiting the keybinds utility to make the experience smoother.
### Maps
- Lighthouse
  - a model of the portland head lighthouse in maine by IamKraZ
- Tahiti
  - use the numpad to change the time of day
- SGC
  - a really big landscape to showcase origin shifting to keep floating point accuracy withing 3 figures of loss
  - a fun place to take a jet for a test flight
- Planets
  - just when you thought space was the final frontier... the full power of container streaming on display
  - points of interest and detail will continue to be added to planets as models are made
- TreeLods
  - more than the name implies, this is the first map that has gameplay elements
  - not everything has to use game3, this shows how different logic can be combined with game3
  - and of course, an object scattering script to dynamically spawn trees around the player
  - navmesh with obstacles
- LavaPits
  - by completion, level one of what im hoping will evolve into its own game.  to be used as a feedback on mechanics.
- TileCity
  - a simpler demo of container streaming
### Assets
- Zephyr Ship
  - this project was originally called the "Zephyr Demo" showcasing container streaming and persistance data being passed across game world data
  - containers now have slots that children can be attached to on display as the shuttle docking
- Vehicles
  - jets, atvs, cars, etc
- Player characters
  - you can change character in the characters menu.  green highlight is the active player, select again to reset to default.
- Attachments/Usables
  - guns, jetpacks, hats and things

## Quick tips:
- Keybinds are fully customizable but the common defaults are
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
- Use ESC to open pause menu, f12 for screenshot
- You can back out to launcher/menu and resume at any time
- Use the SAVE and LOAD buttons to save the session to a file (do this when a bug occures and include with issue)

## How to build:
- Unzip the packaged game3 release "bge_game3_core-xxxxxx" to a folder called `game3`
  - generally "extract here" and renaming the folder (bge_game3_core-master or similar) it creates should do
  - this folder should only contain py files and a blend
- Go the the current upload site and "Download All"
  - https://drive.google.com/drive/folders/13nl_B-knwAJ2afuhTZqTfIXukIc1dGxZ?usp=sharing
  - extract the zip and paste the `CONTENT`, `MAPS`, `TEXTURES` into the project folder
- Download the bin exe to run the demo without the need of upbge 0.2.0 (based on blender 2.78.5)
  - https://drive.google.com/file/d/1Kvwysta-Fcy0yc3VGIf0c5PJL7AZYHwF/view?usp=sharing
  - extract the zip and paste the `bin64` in the project folder
- Run the LaunchDemo.cmd to play
