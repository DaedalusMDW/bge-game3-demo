
## CAR OBJECTS ##


from game3 import vehicle


class ATV(vehicle.CoreCar):

	NAME = "ShowStealer ATV"
	INPUT_SMOOTH = 0.15

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
	CAR_BAIL = 360

	CAR_STEER = 0.5

	SEATS = {
		"Seat_1": {"NAME":"Driver", "DOOR":"Root", "CAMERA":(0, 0, 0.6), "VISIBLE":"FULL", "ACTION":"SeatRide", "SPAWN":[-1,0,0.3]} }

	def ST_Startup(self):
		self.env_dim = None
		self.active_post.append(self.PS_Ambient)

	def applyContainerProps(self, cls):
		super().applyContainerProps(cls)
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


class Buggy(vehicle.CoreCar):

	NAME = "All-Terrain Buggy"
	INPUT_SMOOTH = 0.1

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

	def ST_Startup(self):
		self.env_dim = None
		self.active_post.append(self.PS_Ambient)

	def applyContainerProps(self, cls):
		super().applyContainerProps(cls)
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

