

from mathutils import Vector

from bge import logic


def BULLET(cont):
	owner = cont.owner
	rayfrom = owner.worldPosition.copy()
	rayto = rayfrom+owner.getAxisVect([0,1,0])

	obj, pnt, nrm = owner["ROOTOBJ"].rayCast(rayto, rayfrom, owner.localScale[1], "", 1, 1, 0)

	if obj != None and owner["ROOTOBJ"] != obj:
		if "MODIFIERS" in obj:
			obj["MODIFIERS"].append({"HEALTH":-owner["DAMAGE"]})

		if obj.getPhysicsId() != 0:
			obj.applyImpulse(pnt, owner.getAxisVect([0,owner["DAMAGE"],0]), False)

		gfx = owner.scene.addObject("GFX_LaserHit", owner, 0)
		gfx.worldPosition = pnt
		s = owner.localScale[0]
		#if s < 0.5:
		#	s = 0.5
		gfx.localScale = (s,s,s)
		gfx.children[0].color = owner.color
		owner.endObject()

	owner.worldPosition += owner.getAxisVect([0,1,0])*owner.localScale[1]
	if "LINV" in owner:
		owner.worldPosition += owner["LINV"]


def MISSILE(cont):
	owner = cont.owner
	scene = owner.scene

	WV = owner.worldLinearVelocity*(1/60)

	rayfrom = owner.worldPosition-owner.getAxisVect([0,-1,0])+(WV*-0.5)
	rayto = owner.worldPosition+owner.getAxisVect([0,1,0])+(WV*0.5)

	obj, pnt, nrm = owner.rayCast(rayto, rayfrom, 0, "", 1, 0, 0)

	if obj != None and owner["ROOTOBJ"] != obj:
		print("HIT", obj)
		owner["TIME"] = -1

	if owner["TIME"] <= 0:
		bom = scene.addObject("AOE_Bomb", owner, 0)
		bom.localScale = (16, 16, 16)
		bom["DAMAGE"] = owner["DAMAGE"]
		bom["IMPULSE"] = 100
		owner.endObject()

	owner["TIME"] -= 1

	t = owner.get("SMOKE", 0)
	if t == 2:
		owner["SMOKE"] = 0
		sma = scene.addObject("GFX_Batbomb", owner, 0)
		sma.localScale = (1, 1, 1)
		rndx = (logic.getRandomFloat()-0.5)*0.1
		rndy = (logic.getRandomFloat()-0.5)*0.1
		rvec = owner.getAxisVect((rndx,0,rndy))
		sma.worldPosition += rvec
		sma["SCALE"] = 16
		sma["MOVE"] = rvec*0.05
	else:
		owner["SMOKE"] = t+1

	owner.setDamping(0.9,0.7)
	owner.applyForce((0,300,0), True)
	owner.applyForce(-scene.gravity, False)

	if WV.length < 0.01:
		return

	tx = 0
	tz = 0
	if owner.get("TARGET", None) != None:
		obj = owner["TARGET"]
		if obj.invalid == False:
			t = (obj.worldPosition-owner.worldPosition)
			if t.length > 0.1 and owner.getAxisVect([0,1,0]).dot(t.normalized()) > 0:
				tx, ty, tz = owner.worldOrientation.inverted()*t.normalized()

	LV = owner.localLinearVelocity
	v = LV.normalized()
	l = (LV.length*0.05)**2
	x = Vector([-1,tx*-1,0]).normalized()
	z = Vector([0,tz*1,1]).normalized()

	owner.applyTorque([z.dot(v)*l, 0, x.dot(v)*l], True)


def GRENADE(cont):
	owner = cont.owner
	scene = owner.scene
	rayfrom = owner.worldPosition.copy()
	rayto = rayfrom+owner.getAxisVect([0,1,0])
	obj, pnt, nrm = owner.rayCast(rayto, rayfrom, 0.5, "", 1, 0, 0)
	if obj != None and owner["ROOTOBJ"] != obj:
		if "MODIFIERS" in obj:
			obj["MODIFIERS"].append({"HEALTH":-40})
		owner["TIME"] = -1

	if owner["TIME"] <= 0:
		bom = scene.addObject("AOE_Bomb", owner, 0)
		bom.localScale = (3, 3, 3)
		bom["DAMAGE"] = 40
		bom["IMPULSE"] = 4
		owner.endObject()

	owner["TIME"] -= 1
	sma = scene.addObject("GFX_Batbomb", owner, 0)
	sma.localScale = (0.3, 1, 0.3)
	rndx = (logic.getRandomFloat()-0.5)*0.05
	rndy = (logic.getRandomFloat()-0.5)*0.05
	rvec = owner.getAxisVect((rndx,0,rndy))
	sma.worldPosition += rvec
	sma["SCALE"] = 5
	sma["MOVE"] = rvec*0.05
	owner.worldPosition += owner.getAxisVect([0,1,0])*0.5


def BOMB(cont):
	owner = cont.owner
	dmg = owner.get("DAMAGE", 60)
	imp = owner.get("IMPULSE", 3)
	dur = owner.get("TIME", 5)

	if "GFX" not in owner:
		gfx = owner.scene.addObject(owner.get("GFX", "GFX_LaserHit"), owner, 0)
		gfx.localScale = Vector(owner.localScale)*4
		gfx.color = (1,0.8,0,1)
		owner["GFX"] = gfx
		owner["HITLIST"] = []

	for obj in owner.sensors["Collision"].hitObjectList:
		if obj.isSuspendDynamics == False and obj not in owner["HITLIST"]:
			rnd = Vector([logic.getRandomFloat()-0.5, logic.getRandomFloat()-0.5, logic.getRandomFloat()-0.5])
			pnt = obj.worldPosition+(rnd*0.1)
			dst = obj.worldPosition-owner.worldPosition
			fac = (1-(dst.length*(1/owner.localScale.length)))**2
			vec = dst.normalized()*(logic.getRandomFloat()+1)*imp
			obj.applyImpulse(pnt, vec+owner.getAxisVect([0,0,imp*0.2]), False)
			if "MODIFIERS" in obj:
				obj["MODIFIERS"].append({"HEALTH":-dmg*fac})
			owner["HITLIST"].append(obj)

	if dur <= 0:
		owner.endObject()
	owner["TIME"] = dur-1

