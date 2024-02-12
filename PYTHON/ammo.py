

from mathutils import Vector

from bge import logic


def BULLET(cont):
	owner = cont.owner

	if owner["ROOTOBJ"].invalid == True:
		owner["ROOTOBJ"] = owner

	fwd = owner.getAxisVect([0,1,0])
	h = owner.get("HEALTH", 100)
	l = owner.get("LINV", Vector((0,0,0)))

	if owner.get("CTS", None) == True:
		owner.worldPosition += fwd*owner.localScale[1]
		owner.worldPosition += l
	else:
		owner["CTS"] = True

	rayfrom = owner.worldPosition-(fwd*0.1)
	rayto = rayfrom+fwd

	rco = owner
	if h == 100:
		rco = owner["ROOTOBJ"]

	obj, pnt, nrm = rco.rayCast(rayto, rayfrom, owner.localScale[1]+0.1, "", 1, 0, 0)

	if obj != None:
		gfx = owner.scene.addObject("GFX_LaserHit", owner, 0)
		gfx.worldPosition = pnt
		s = owner.localScale[0]
		if s < 1:
			s = 1
		gfx.localScale = (s,s,s)
		gfx.children[0].color = owner.color

		cls = obj.get("Class", None)

		v = obj.get("SHIELD", 0)
		dmg = owner["DAMAGE"]

		if h >= 0:
			s = dmg
			dmg -= v
			if dmg <= 0:
				dmg = 0
				rv = fwd.reflect(nrm)
				rv = obj.get("BLOCK", rv)
				owner.alignAxisToVect(rv, 1, 1.0)
				owner.worldPosition = pnt+(nrm*0.1)
				owner["DAMAGE"] *= 0.75
				owner["HEALTH"] = h-50
			else:
				s -= dmg
				owner["HEALTH"] = -1

			if cls != None:
				cls.sendEvent("MODIFIERS", HEALTH=-dmg, POS=list(pnt), VEC=list(fwd), IMPULSE=dmg/4)

		if dmg > 0:
			if obj.getPhysicsId() != 0:
				obj.applyImpulse(pnt, owner.getAxisVect([0,dmg/4,0]), False)
			if cls != None:
				cls.sendEvent("IMPULSE")

		if owner["HEALTH"] < 0:
			owner.endObject()

	#else:
	#	owner.worldPosition += fwd*owner.localScale[1]
	#	owner.worldPosition += l


def MISSILE(cont):
	owner = cont.owner
	scene = owner.scene

	if owner["ROOTOBJ"].invalid == True:
		owner["ROOTOBJ"] = owner

	m = owner.get("MODIFIERS", [])
	for i in m:
		if i.get("HEALTH", 0) < 0:
			owner["TIME"] = -1
	owner["MODIFIERS"] = []

	WV = owner.worldLinearVelocity*(1/60)

	rayfrom = owner.worldPosition-WV #owner.getAxisVect([0,-1,0])+(WV*-0.5)
	rayto = owner.worldPosition+WV #owner.getAxisVect([0,1,0])+(WV*0.5)

	obj, pnt, nrm = owner.rayCast(rayto, rayfrom, 0, "", 1, 0, 0)

	if obj != None and owner["ROOTOBJ"] != obj:
		print("HIT", obj)
		owner["TIME"] = -1

	if owner["TIME"] <= 0:
		bom = scene.addObject("AOE_Bomb", owner, 0)
		s = owner.get("RADIUS", 16)
		bom.localScale = (s, s, s)
		bom.color = (1,0.8,0,1)
		bom["DAMAGE"] = owner.get("DAMAGE", 200.0)
		bom["IMPULSE"] = owner.get("IMPULSE", 100.0)
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
		sma["SCALE"] = owner.get("SCALE", 16)
		sma["MOVE"] = rvec*0.05
	elif t >= 0:
		owner["SMOKE"] = t+1

	owner.setDamping(0.9,0.7)
	owner.applyForce((0,300,0), True)
	owner.applyForce(-scene.gravity, False)

	if WV.length < 0.1:
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

	if owner["ROOTOBJ"].invalid == True:
		owner["ROOTOBJ"] = owner

	rayfrom = owner.worldPosition.copy()
	rayto = rayfrom+owner.getAxisVect([0,1,0])

	obj, pnt, nrm = owner.rayCast(rayto, rayfrom, 0.5, "", 1, 0, 0)

	if obj != None and owner["ROOTOBJ"] != obj:
		cls = obj.get("Class", None)
		if cls != None:
			cls.sendEvent("MODIFIERS", HEALTH=-40, IMPULSE=1)
			cls.sendEvent("IMPULSE")
		owner["TIME"] = -1

	if owner["TIME"] <= 0:
		bom = scene.addObject("AOE_Bomb", owner, 0)
		bom.localScale = (3, 3, 3)
		bom.color = (1,0.8,0,1)
		bom["DAMAGE"] = 40.0
		bom["IMPULSE"] = 8.0
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
	dmg = owner.get("DAMAGE", 60.0)
	imp = owner.get("IMPULSE", 3.0)
	dur = owner.get("TIME", 5)

	if "GFX" not in owner:
		gfx = owner.scene.addObject(owner.get("GFX", "GFX_LaserHit"), owner, 0)
		gfx.localScale = Vector(owner.localScale)*4
		gfx.children[0].color = owner.color
		owner["GFX"] = gfx
		owner["HITLIST"] = []

	for obj in owner.sensors["Collision"].hitObjectList:
		if obj not in owner["HITLIST"]:
			rnd = Vector([logic.getRandomFloat()-0.5, logic.getRandomFloat()-0.5, logic.getRandomFloat()-0.5])
			pnt = obj.worldPosition+(rnd*0.1)
			dst = obj.worldPosition-owner.worldPosition
			fac = (1-(dst.length*(1/owner.localScale.length)))**2
			vec = dst.normalized()*(logic.getRandomFloat()+1)*imp*fac
			if obj.mass > 0.01 and obj.isSuspendDynamics == False:
				obj.applyImpulse(pnt, vec, False)
			cls = obj.get("Class", None)
			if cls != None:
				cls.sendEvent("MODIFIERS", HEALTH=-dmg*fac, POS=list(owner.worldPosition), VEC=list(vec) , IMPULSE=vec.length)
				cls.sendEvent("IMPULSE")
			owner["HITLIST"].append(obj)

	if dur <= 0:
		owner.endObject()
	owner["TIME"] = dur-1

