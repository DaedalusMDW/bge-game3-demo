
from game3 import config

config.LIBRARIES = [
	"CommonAssets",
	"Zephyr"
]

config.LIBLOAD_TYPE = "NORMAL"
config.SCREENSHOT_PATH = "SCREENSHOTS"
config.LIBRARY_PATH = "CONTENT"
config.MAPS_PATH = "MAPS"

config.CAMERA_CLIP = [0.1, 100000]
config.MOUSE_BUFFER = True   #False to remove mouse input processing

config.DEFAULT_PLAYER = "Actor"

print("\n\t...game init...\n")
