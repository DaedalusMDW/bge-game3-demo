
from game3 import config, input, keymap

# while i dont recommend using lights in libs...
# blends with lights should be at the top, since lights only affect all loaded after.

config.LIBRARIES = [
	"CommonAssets",
	"DemoContent",
	"Zephyr1",
	"StarWars",
	"Stargate",
]

config.LIBLOAD_TYPE = "NORMAL"
config.SCREENSHOT_PATH = "SCREENSHOTS"
config.LIBRARY_PATH = "CONTENT"
config.MAPS_PATH = "MAPS"

config.CAMERA_CLIP = [0.1, 100000]
config.MOUSE_BUFFER = True	# False to remove mouse input processing
config.FPS_CAP = 60		# Set 0 for uncapped, -1 for use-framerate capped.
#config.FONT_SCALE = 0.3	# Scale font texture, screen width (as 16/9) divided by 6400.

config.DEFAULT_PLAYER = "Actor"

# add a spacebar skip keybind
keymap.SYSTEM["UI_SKIP"] = input.KeyBase("999.Z", "SPACEKEY", "UI Skip", JOYBUTTON=keymap.joy_msb[0])

print("\n\t...game init...\n")
