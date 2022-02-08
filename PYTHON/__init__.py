
from game3 import config, input, keymap

# while i dont recommend using lights in libs...
# blends with lights should be at the top, since lights only affect all loaded after.

config.LIBRARIES = [
	"Zephyr",
	"StarWars",
	"CommonAssets"	# Pro-Tip: put blends that are integral at the bottom,
			#          that way you can comment "addons" without needing
			#          to bother with the comma at the end :)
]

config.LIBLOAD_TYPE = "NORMAL"
config.SCREENSHOT_PATH = "SCREENSHOTS"
config.LIBRARY_PATH = "CONTENT"
config.MAPS_PATH = "MAPS"

config.CAMERA_CLIP = [0.1, 100000]
config.MOUSE_BUFFER = True   #False to remove mouse input processing
config.FPS_CAP = 60 #set 0 for uncapped, -1 for use-framerate capped.

config.DEFAULT_PLAYER = "Actor"

# add a spacebar skip keybind
keymap.SYSTEM["UI_SKIP"] = input.KeyBase("999.Z", "SPACEKEY", "UI Skip", JOYBUTTON=keymap.joy_msb[0])

print("\n\t...game init...\n")
