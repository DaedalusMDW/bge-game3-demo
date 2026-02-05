

import mathutils

from game3 import door


class Swing(door.CoreDoor):

	SPRING = "SPRING"
	ANIM = {"OPEN":(0,60), "CLOSE":(60,0)}

class Automatic(door.CoreDoor):

	SPRING = "MOTOR"
	ANIM = {"OPEN":(0,60), "CLOSE":(60,0)}

class Slide(door.CoreDoor):

	ANIM = {"OPEN":(0,120), "CLOSE":(130,250)}

class GarageDoor(Automatic):

	NAME = "Garage Door"
	ANIM = {"OPEN":(0,300), "CLOSE":(300,0)}

class Blast(Automatic):

	NAME = "Blast Door"
	TIME = 60
	ANIM = {"OPEN":(0,240), "CLOSE":(240,0)}

class CargoLift(door.CoreDoor):

	NAME = "Cargo Lift"
	ANIM = {"OPEN":(0,300), "CLOSE":(300,0)}

class Ramp(door.CoreDoor):

	NAME = "Ramp"
	ANIM = {"OPEN":(0,150), "CLOSE":(150,0)}

