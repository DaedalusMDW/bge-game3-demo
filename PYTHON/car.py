
## CAR OBJECTS ##


from game3 import vehicle


class ATV(vehicle.CoreCar):

	NAME = "ShowStealer ATV"
	INPUT_SMOOTH = 0.2

	CAM_MIN = 1.5

	WH_MESH = "Wheel.ATV"
	WH_RADIUS = 0.3

	WH_FRONT = 0.75
	WH_REAR = -0.75
	WH_WIDTH = 0.45
	WH_HEIGHT = 0.0

	VEH_LENGTH = 0.5

	VEH_ROLL = 0.1
	VEH_SPRING = 65
	VEH_DAMPING = 8
	VEH_FRICTION = 3

	CAR_POWER = 15
	CAR_SPEED = 40
	CAR_BRAKE = 0.1
	CAR_HANDBRAKE = 0.1
	CAR_REVERSE = 1.0
	CAR_STEER = 0.8
	CAR_DRIVE = "REAR"
	CAR_AIR = (2,2,1)
	CAR_ALIGN = True
	CAR_BAIL = 60

	SEATS = {
		"Seat_1": {"NAME":"Driver", "DOOR":"Root", "CAMERA":(0, 0, 0.6), "VISIBLE":"FULL", "ACTION":"SeatRide", "SPAWN":[-1,0,0]} }


class Buggy(vehicle.CoreCar):

	NAME = "All-Terrain Buggy"
	INPUT_SMOOTH = 0.1

	WH_MESH = "Wheel.Buggy"
	WH_RADIUS = 0.35

	WH_FRONT = 1.5
	WH_REAR = -1.5
	WH_WIDTH = 1.1
	WH_HEIGHT = 0.2

	VEH_LENGTH = 0.4

	VEH_ROLL = 0.0
	VEH_SPRING = 20 #30
	VEH_DAMPING = 3 #15
	VEH_FRICTION = 7
	VEH_COMPRESS = 3

	CAR_POWER = 20
	CAR_SPEED = 100
	CAR_BRAKE = 0.5
	CAR_HANDBRAKE = 0.2
	CAR_REVERSE = 0.5
	CAR_STEER = 1.2
	CAR_DRIVE = "FOUR"
	CAR_ALIGN = True
	CAR_BAIL = 120

	SEATS = {
		"Seat_1": {"NAME":"Driver", "DOOR":"Root", "CAMERA":(0, -0.05, 0.6), "VISIBLE":"FULL", "ACTION":"SeatLow", "SPAWN":[-1.5,0,0]} }

