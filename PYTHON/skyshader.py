############################################################################
#
#    The BlenderWAR's Custom: This is a designed Sky HDRI Script !!!
#    
#     This is an advanced script that plays completely has an HDRI Sky Texture
#     packed inside the desired code below! (Or atleast Fakes an HDRI successfully)
#     The Script was originally Written by @Martins Upitis on B.A
#
#
#     Edited by Fred/K.S - this is a combination of past scripts put up
#     to create a new version that functions better in the Blender Game Engine !!!
#
#     Free to use in any project as a test experiment and do not use as a final script!
#
#########################################################################


VertexShader = """

attribute vec4 Tangent;
varying vec4 fragPos;
varying vec3 wT, wB, wN; //tangent binormal normal
varying vec3 wPos, pos, viewPos;
uniform mat4 ModelMatrix;
uniform vec3 cameraPos;
varying float luminance;

mat3 m3( mat4 m )
{
	mat3 result;
	
	result[0][0] = m[0][0]; 
	result[0][1] = m[0][1]; 
	result[0][2] = m[0][2]; 

	result[1][0] = m[1][0]; 
	result[1][1] = m[1][1]; 
	result[1][2] = m[1][2]; 
	
	result[2][0] = m[2][0]; 
	result[2][1] = m[2][1]; 
	result[2][2] = m[2][2]; 
	
	return result;
}

void main() 
{
	wPos = vec3(ModelMatrix * gl_Vertex);
	//pos = vec3(gl_Vertex);

	wT = m3(ModelMatrix)*Tangent.xyz;
	wB = m3(ModelMatrix)*cross(gl_Normal, Tangent.xyz);
	wN = m3(ModelMatrix)*gl_Normal;

	//fragPos = ftransform();
	viewPos = wPos - cameraPos.xyz;
	luminance = 1.0-exp(-gl_Color.r);
	gl_Position = ftransform();
}

"""


FragmentShader = """

uniform sampler2D skySampler;

varying vec4 fragPos; //fragment coordinates
varying vec3 wT, wB, wN; //tangent binormal normal
varying vec3 wPos, pos, viewPos;
uniform vec3 cameraPos;
uniform float bias, lumamount, contrast;
varying float luminance;
uniform vec3 sunVec;

vec3 sunDirection = normalize(sunVec);

uniform float turbidity, reileigh;

float reileighCoefficient = reileigh;
const float mieCoefficient = 0.1;
const float mieDirectionalG = 0.7;

vec3 tangentSpace(vec3 v)
{
	vec3 vec;
	vec.xy=v.xy;
	vec.z=sqrt(1.0-dot(vec.xy,vec.xy));;
	vec.xyz= normalize(vec.x*wT+vec.y*wB+vec.z*wN);
	return vec;
}

// constants for atmospheric scattering
const float e  = 2.71828182;
const float pi = 3.14159265;

const float n = 1.0003;   // refractive index of air
const float N = 2.545E25; // number of molecules per unit volume for air at 288.15K and 1013mb (sea level -45 celsius)
const float pn = 0.035;   // depolatization factor for standard air

// wavelength of used primaries, according to preetham
const vec3 lambda = vec3(680E-9, 550E-9, 450E-9);

// mie stuff
// K coefficient for the primaries
const vec3 K = vec3(0.686, 0.678, 0.666);
const float v = 4.0;

// optical length at zenith for molecules
const float rayleighZenithLength = 8.4E3;
const float mieZenithLength = 1.25E3;
const vec3 up = vec3(0.0, 0.0, 1.0);

const float EE = 1000.0;
const float sunAngularDiameterCos = 0.99;

// earth shadow hack
const float cutoffAngle = pi/1.95;
const float steepness = 1.5;


vec3 totalRayleigh(vec3 lambda)
{
	return (8.0 * pow(pi, 3.0) * pow(pow(n, 2.0) - 1.0, 2.0) * (6.0 + 3.0 * pn)) / (3.0 * N * pow(lambda, vec3(4.0)) * (6.0 - 7.0 * pn));
}

float rayleighPhase(float cosTheta)
{
	//return (3.0 / (16.0*pi)) * (1.0 + pow(cosTheta, 2.0));
	//return (1.0 / (3.0*pi)) * (1.0 + pow(cosTheta, 2.0));
	return (3.0 / 4.0) * (1.0 + pow(cosTheta, 2.0));
}

vec3 totalMie(vec3 lambda, vec3 K, float T)
{
	float c = (0.2 * T ) * 10E-18;
	return 0.434 * c * pi * pow((2.0 * pi) / lambda, vec3(v - 2.0)) * K;
}

float hgPhase(float cosTheta, float g)
{
	return (1.0 / (4.0*pi)) * ((1.0 - pow(g, 2.0)) / pow(1.0 - 2.0*g*cosTheta + pow(g, 2.0), 1.5));
}

float sunIntensity(float zenithAngleCos)
{
	return EE * max(0.0, 1.0 - exp(-((cutoffAngle - acos(zenithAngleCos))/steepness)));
}

float logLuminance(vec3 c)
{
	return log(c.r * 0.2126 + c.g * 0.7152 + c.b * 0.0722);
}


float A = 0.15;
float B = 0.50;
float C = 0.10;
float D = 0.20;
float E = 0.02;
float F = 0.30;
float W = 1000.0;

vec3 Uncharted2Tonemap(vec3 x)
{
	return ((x*(A*x+C*B)+D*E)/(x*(A*x+B)+D*F))-E/F;
}

// HSV ADD
vec3 rgb2hsv(vec3 c)
{
	vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
	vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
	vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

	float d = q.x - min(q.w, q.y);
	float e = 1.0e-10;
	return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}
// HSV ADD

void main() 
{
	float sunE = sunIntensity(dot(sunDirection, up));

	// extinction (absorbtion + out scattering)
	// rayleigh coefficients
	vec3 betaR = totalRayleigh(lambda) * reileighCoefficient;

	// mie coefficients
	vec3 betaM = totalMie(lambda, K, turbidity) * mieCoefficient;

	// optical length
	// cutoff angle at 90 to avoid singularity in next formula.
	float zenithAngle = acos(max(0.0, dot(up, normalize(wPos - cameraPos))));
	float sR = rayleighZenithLength / (cos(zenithAngle) + 0.15 * pow(93.885 - ((zenithAngle * 180.0) / pi), -1.253));
	float sM = mieZenithLength / (cos(zenithAngle) + 0.15 * pow(93.885 - ((zenithAngle * 180.0) / pi), -1.253));


	// combined extinction factor
	vec3 Fex = exp(-(betaR * sR + betaM * sM));

	// in scattering
	float cosTheta = dot(normalize(wPos - cameraPos), sunDirection);

	float rPhase = rayleighPhase(cosTheta*0.5+0.5);
	vec3 betaRTheta = betaR * rPhase;

	float mPhase = hgPhase(cosTheta, mieDirectionalG);
	vec3 betaMTheta = betaM * mPhase;

        
	vec3 Lin =            pow(sunE*((betaRTheta+betaMTheta)/(betaR+betaM))*(1.0 - Fex),vec3(1.3));
	Lin *= mix(vec3(1.0), pow(sunE*((betaRTheta+betaMTheta)/(betaR+betaM))*Fex,vec3(1.0/2.0)), clamp(pow(1.0-dot(up,sunDirection),5.0), 0.0, 1.0));

	//nightsky
	vec3 direction = normalize(wPos - cameraPos);

	float theta = acos(direction.y);               // elevation --> y-axis, [-pi/2, pi/2]
	float phi = atan(direction.z, direction.x);    // azimuth --> x-axis [-pi/2, pi/2]

	vec2 uv = vec2(phi, theta) / vec2(2.0*pi, pi) + vec2(0.5, 0.0);

	//vec3 L0 = texture2D(skySampler, uv).rgb+0.1 * Fex;
	vec3 L0 = vec3(0.1) * Fex;

	// composition + solar disc
	//if (cosTheta > sunAngularDiameterCos)
	//if (normalize(wPos - cameraPos).z>0.0)
	//	L0 += sunE * 1000.0 * Fex;


	vec3 whiteScale = 1.0/Uncharted2Tonemap(vec3(W));

	vec3 texColor = (Lin+L0);
	texColor *= 0.01;

	float ExposureBias = 1.0;

	vec3 curr = Uncharted2Tonemap(ExposureBias*texColor);
	vec3 color = curr*whiteScale;

	vec3 retColor = pow(color,vec3(1.0/1.2));
	gl_FragColor.rgb = vec3(retColor.r,retColor.g,retColor.b);

	gl_FragColor.a = 1.0; //rgb2hsv(retColor).b; //HSV Alpha
}
"""


from math import degrees, radians

from mathutils import *

from bge import logic as g
from bge import render as r
from bge import events as e

from game3 import base


def RUN(cont):
	owner = cont.owner
	scene = owner.scene
	child = owner.childrenRecursive

	sun =   child["xENV.Sun"]
	halo =  child["xENV.Halo"]
	pitch = child["xENV.Angle"]
	yaw =   child["xENV.Rotate"]
	env =   child["xENV.Hemi.0"]
	amb =   child["xENV.Hemi.180"]

	refVec = Vector((0,0,1))
	sunVec = sun.worldOrientation*refVec

	# DATA
	group = owner.groupObject
	if group == None:
		group = owner

	angle = [group.get("Y", 30), group.get("Z", 30)]
	key = group.get("WORLD", None)

	if key != None:
		if "SUNDIAL" not in base.WORLD:
			base.WORLD["SUNDIAL"] = {}
		if key not in base.WORLD["SUNDIAL"]:
			base.WORLD["SUNDIAL"][key] = angle
			print("TIMEBUREAU: WORLD", key)
		angle = base.WORLD["SUNDIAL"][key]

	elif base.LEVEL != None:
		if "SUNDIAL" not in base.LEVEL:
			base.LEVEL["SUNDIAL"] = angle
			print("TIMEBUREAU: LOCAL")
		angle = base.LEVEL["SUNDIAL"]

	# ANGLE
	kbe = g.keyboard.events

	angle[0] += ((kbe[e.PAD2]==2) - (kbe[e.PAD8]==2))*0.25
	angle[1] += ((kbe[e.PAD4]==2) - (kbe[e.PAD6]==2))*0.5

	if angle[0] < 0:
		angle[0] = 0
	if angle[0] > 90:
		angle[0] = 90
	if angle[1] >= 360:
		angle[1] -= 360
	if angle[1] < 0:
		angle[1] += 360

	dot = refVec.dot(sunVec)
	dot *= int(dot>=0)
	fac = ((1-dot)**3)
	dot = 1-fac

	# SUN
	pitch.localOrientation = Euler((0,radians(angle[0]),0)).to_matrix()
	yaw.localOrientation = Euler((0,0,radians(angle[1]))).to_matrix()

	sunStart = Vector((1.00, 0.94, 0.85))
	sunEnd =   Vector((1.00, 0.36, 0.00))
	sun.color = sunStart.lerp(sunEnd, fac)
	sun.energy = 0.0+(dot*1.3)

	# HEMI
	env.localOrientation = Euler((0,radians(angle[0]/2),0)).to_matrix()
	env.energy = 0.3+(dot*0.4)
	amb.energy = 0.2+(dot*0.2)

	# HALO
	halo.worldScale = Vector((1000, 1000, 1000))*(5-(3*dot))
	halo.color = (dot, dot, dot, 1)

	# FOLLOW
	Z = group.get("TRACK", "")

	parent = scene.active_camera.parent

	if parent == None:
		parent = scene.active_camera

	if "X" in Z or Z == "A":
		owner.worldPosition[0] = parent.worldPosition[0]

	if "Y" in Z or Z == "A":
		owner.worldPosition[1] = parent.worldPosition[1]

	if "Z" in Z or Z == "A":
		owner.worldPosition[2] = parent.worldPosition[2]

	# SHADER
	mesh = owner.meshes[0]
	for mat in mesh.materials:
		shader = mat.getShader()
		if shader != None:
			if not shader.isValid():
				shader.setSource(VertexShader, FragmentShader, 1)
			shader.setAttrib(g.SHD_TANGENT)
			shader.setUniformDef('ModelMatrix', g.MODELMATRIX)
			shader.setUniformDef('cameraPos', g.CAM_POS)
			shader.setUniform3f('sunVec', sunVec[0],sunVec[1],sunVec[2])
			shader.setUniform1f('turbidity', 1.5)
			shader.setUniform1f('reileigh', 2.0)

	# DEBUG
	group["Y"] = angle[0]
	group["Z"] = angle[1]
	group.addDebugProperty("Y", True)
	group.addDebugProperty("Z", True)

