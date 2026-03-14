
## CAR OBJECTS ##


from game3 import vehicle, keymap


class AmbientCar(vehicle.CoreCar):

	AMBIENT_CHILD = False

	def ST_Startup(self):
		self.env_dim = None
		self.active_post.append(self.PS_Ambient)

	def applyContainerProps(self, cls):
		super().applyContainerProps(cls)
		if self.AMBIENT_CHILD == True:
			cls.env_dim = list(self.objects["Mesh"].color)

	def PS_Ambient(self):
		if self.env_dim == None:
			cls = self.getParent()
			amb = 0
			if cls != None:
				amb = cls.dict.get("DIM", amb)
			self.env_dim = (amb+1, amb+1, amb+1, 1.0)

		self.objects["Mesh"].color = self.env_dim

		for w in self.wheelobj:
			obj = self.wheelobj[w]
			obj.children[0].color = self.env_dim

		self.env_dim = None
		self.container_props = None


class Mercedes(AmbientCar):

	NAME = "Raptor's Mercedes"
	PLAYERACTION = "SeatLow"

	WH_MESH = "Wheel.Mercedes"
	WH_RADIUS = 0.3

	WH_FRONT = 1.275
	WH_REAR = -1.24
	WH_WIDTH = 0.75
	WH_HEIGHT = 0.3
	VEH_LENGTH = 0.15

	VEH_ROLL = 0
	VEH_SPRING = 50
	VEH_DAMPING = 2
	VEH_COMPRESS = 4

	VEH_FRICTION = 1

	CAR_POWER = 80
	CAR_SPEED = 40
	CAR_DRIVE = "FRONT"
	CAR_BRAKE = 1.0
	CAR_HANDBRAKE = 1
	CAR_REVERSE = 0.5

	CAR_STEER = 0.5

	CAM_MIN = 1
	SEATS = {
		"Seat_1": {"NAME":"Driver",    "DOOR":"Door_1", "CAMERA":(-0.39,-0.55, 0.3), "ACTION":"SeatLow",  "SPAWN":[-1.5,-0.5, 0.3], "STATE":"DRIVER"},
		"Seat_2": {"NAME":"Passenger", "DOOR":"Door_2", "CAMERA":( 0.39,-0.55, 0.3), "ACTION":"SeatLowP", "SPAWN":[ 1.5,-0.5, 0.3], "STATE":"PASSIVE"} }


class Corvette(AmbientCar):

	NAME = "Hugo's Corvette"

	WH_MESH = "Wheel.Corvette"
	WH_RADIUS = 0.33

	WH_FRONT = 1.275
	WH_REAR = -1.35
	WH_WIDTH = 0.75
	WH_HEIGHT = 0.35
	VEH_LENGTH = 0.08

	VEH_ROLL = 0
	VEH_SPRING = 60
	VEH_DAMPING = 5

	VEH_FRICTION = 1.5

	CAR_POWER = 80
	CAR_SPEED = 40
	CAR_DRIVE = "REAR"
	CAR_BRAKE = 0.8
	CAR_HANDBRAKE = 1
	CAR_REVERSE = 0.5

	CAR_STEER = 0.5

	CAM_MIN = 1
	SEATS = {
		"Seat_1": {"NAME":"Driver",    "DOOR":"Door_1", "CAMERA":(-0.39,-0.45, 0.35), "ACTION":"SeatLow",  "SPAWN":[-1.5,-0.5, 0.3], "STATE":"DRIVER"},
		"Seat_2": {"NAME":"Passenger", "DOOR":"Door_2", "CAMERA":( 0.39,-0.45, 0.35), "ACTION":"SeatLowP", "SPAWN":[ 1.5,-0.5, 0.3], "STATE":"PASSIVE"} }


class Lamborghini(AmbientCar):

	NAME = "Lamborghini"

	WH_MESH = "Wheel.Lamborghini"
	WH_RADIUS = 0.33

	WH_FRONT = 1.275
	WH_REAR = -1.48
	WH_WIDTH = 0.87
	WH_HEIGHT = 0.33
	VEH_LENGTH = 0.05

	VEH_ROLL = 0
	VEH_SPRING = 80
	VEH_DAMPING = 3

	VEH_FRICTION = 2

	CAR_POWER = 100
	CAR_SPEED = 60
	CAR_DRIVE = "REAR"
	CAR_BRAKE = 1.0
	CAR_HANDBRAKE = 1.0
	CAR_REVERSE = 0.5

	CAR_STEER = 0.5

	CAM_MIN = 1.5
	SEATS = {
		"Seat_1": {"NAME":"Driver",    "DOOR":"Door_1", "CAMERA":(-0.4, 0, 0.325), "ACTION":"SeatLow",  "SPAWN":[-1.5,-0.5, 0.3], "STATE":"DRIVER"},
		"Seat_2": {"NAME":"Passenger", "DOOR":"Door_2", "CAMERA":( 0.4, 0, 0.325), "ACTION":"SeatLowP", "SPAWN":[ 1.5,-0.5, 0.3], "STATE":"PASSIVE"} }


class Van(AmbientCar):

	NAME = "RayBase Transport Van"

	WH_MESH = "Wheel.Van"
	WH_RADIUS = 0.4

	WH_FRONT = 1.87
	WH_REAR = -1.70
	WH_WIDTH = 0.8
	WH_HEIGHT = 0.65
	VEH_LENGTH = 0.17

	VEH_ROLL = 0
	VEH_SPRING = 70
	VEH_DAMPING = 7
	#VEH_COMPRESS = 4

	VEH_FRICTION = 0.7

	CAR_POWER = 50
	CAR_SPEED = 100
	CAR_DRIVE = "REAR"
	CAR_BRAKE = 1
	CAR_HANDBRAKE = 1
	CAR_REVERSE = 0.7

	CAR_STEER = 0.5

	CAM_MIN = 2
	SEATS = {
		"Seat_1": {"NAME":"Driver",    "DOOR":"Door_1", "CAMERA":(-0.56, 0.95, 0.675), "ACTION":"SeatTall",  "SPAWN":[-1.5,1,-0.2], "STATE":"DRIVER"},
		"Seat_2": {"NAME":"Passenger", "DOOR":"Door_2", "CAMERA":( 0.56, 0.95, 0.675), "ACTION":"SeatTallP", "SPAWN":[ 1.5,1,-0.2], "STATE":"PASSIVE"} }


class Silverado(AmbientCar):

	NAME = "The Scientist's Truck"

	WH_MESH = "Wheel.Silverado"
	WH_RADIUS = 0.38

	WH_FRONT = 2.13
	WH_REAR = -1.78
	WH_WIDTH = 0.85
	WH_HEIGHT = 0.3
	VEH_LENGTH = 0.4

	VEH_ROLL = 0
	VEH_SPRING = 150
	VEH_DAMPING = 20

	VEH_FRICTION = 2

	CAR_POWER = 70
	CAR_SPEED = 25
	CAR_DRIVE = "FOUR"
	CAR_BRAKE = 1
	CAR_HANDBRAKE = 2
	CAR_REVERSE = 0.5

	CAR_STEER = 0.5

	CAM_MIN = 1.5
	SEATS = {
		"Seat_1": {"NAME":"Driver",    "DOOR":"Door_1", "CAMERA":(-0.4, 0.7, 0.45), "ACTION":"SeatTall",  "SPAWN":[-1.5, 1, 0], "STATE":"DRIVER"},
		"Seat_2": {"NAME":"Passenger", "DOOR":"Door_2", "CAMERA":( 0.4, 0.7, 0.45), "ACTION":"SeatTallP", "SPAWN":[ 1.5, 1, 0], "STATE":"PASSIVE"},
		"Seat_3": {"NAME":"Passenger", "DOOR":"Door_3", "CAMERA":(10.4,-0.3, 0.45), "ACTION":"SeatTallP", "SPAWN":[-1.5, 0, 0], "STATE":"PASSIVE"},
		"Seat_4": {"NAME":"Passenger", "DOOR":"Door_4", "CAMERA":( 0.4,-0.3, 0.45), "ACTION":"SeatTallP", "SPAWN":[ 1.5, 0, 0], "STATE":"PASSIVE"} }


class ATV(AmbientCar):

	NAME = "ShowStealer ATV"
	INPUT_SMOOTH = 0.15

	AMBIENT_CHILD = True

	CAM_MIN = 1.5

	WH_MESH = "Wheel.ATV"
	WH_RADIUS = 0.3

	WH_FRONT = 0.75
	WH_REAR = -0.75
	WH_WIDTH = 0.55
	WH_HEIGHT = 0.0
	VEH_LENGTH = 0.5

	VEH_ROLL = 0
	VEH_SPRING = 30
	VEH_DAMPING = 4

	VEH_FRICTION = 1

	CAR_POWER = 10
	CAR_SPEED = 40
	CAR_BRAKE = 0.1
	CAR_HANDBRAKE = 0.1
	CAR_REVERSE = 1.0
	CAR_DRIVE = "REAR"
	CAR_AIR = (2,2,1)
	CAR_ALIGN = True
	CAR_BAIL = 90

	CAR_STEER = 0.5

	SEATS = {
		"Seat_1": {"NAME":"Driver", "DOOR":"Root", "CAMERA":(0, 0, 0.6), "VISIBLE":"FULL", "ACTION":"SeatRide", "SPAWN":[-1,0,0.3]} }


class Buggy(AmbientCar):

	NAME = "All-Terrain Buggy"
	INPUT_SMOOTH = 0.1

	AMBIENT_CHILD = True

	WH_MESH = "Wheel.Buggy"
	WH_COLOR = None
	WH_RADIUS = 0.35

	WH_FRONT = 1.5
	WH_REAR = -1.5
	WH_WIDTH = 1.1
	WH_HEIGHT = 0.2
	VEH_LENGTH = 0.4

	VEH_ROLL = 0
	VEH_SPRING = 20
	VEH_DAMPING = 3
	VEH_COMPRESS = 3

	VEH_FRICTION = 4

	CAR_POWER = 20
	CAR_SPEED = 100
	CAR_BRAKE = 0.5
	CAR_HANDBRAKE = 0.2
	CAR_REVERSE = 0.5
	CAR_DRIVE = "FOUR"
	CAR_ALIGN = True

	CAR_STEER = 0.5

	SEATS = {
		"Seat_1": {"NAME":"Driver",    "DOOR":"Root",   "CAMERA":( 0.0,-0.0, 0.6), "ACTION":"SeatTall",  "SPAWN":[-1.5, 1, 0.3], "STATE":"DRIVER"},
		"Seat_2": {"NAME":"Passenger", "DOOR":"Door_2", "CAMERA":( 0.6,-0.3, 0.6), "ACTION":"SeatTallP", "SPAWN":[ 1.5, 0, 0.3], "STATE":"PASSIVE"},
		"Seat_3": {"NAME":"Passenger", "DOOR":"Door_3", "CAMERA":(-0.6,-0.3, 0.6), "ACTION":"SeatTallP", "SPAWN":[-1.5, 0, 0.3], "STATE":"PASSIVE"}
	}

