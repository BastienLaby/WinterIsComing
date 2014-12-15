from OpenGL.GL import *
from math import *
from random import *
from transformations import *
import numpy as np
import xml.etree.ElementTree as ET
import sys
from ctypes import *


def generateNoiseTexture(Ratio):

    noise_size = 4
    rotationTextureData = []
    for i in range(noise_size**2):
        randpoint = normalized([uniform(-1.0, 1.0),
                                uniform(-1.0, 1.0),
                                0.0])
        rotationTextureData.append(randpoint)

    rotationTextureData = np.array(rotationTextureData, dtype='float32')

    return rotationTextureData

####################################################################################################################################################
####################################################################################################################################################

def genSSAOSamples(radius, numSample):

    samples = [["" for X in range(3)] for Y in range(numSample)]
    randomAngle = math.pi/4

    for i in range(numSample):
        samples[i][0] = math.cos(randomAngle) * (i+1) / numSample * radius   # X
        samples[i][1] = math.sin(randomAngle) * (i+1) / numSample * radius   # Y
        samples[i][2] = (0.5 * samples[i][0] + 0.5 * samples[i][1]) * (i+1) / numSample * radius
        randomAngle += math.pi/2
        
        if(((i + 1) % 4) == 0):
            randomAngle += math.pi/2

    return samples

####################################################################################################################################################
####################################################################################################################################################

def getProjectionMatrix(fov2):

    aspectratio = 1.0
    z_near =  0.01
    z_far =  200.0
    
    fov = fov2 * np.pi/180.0
    
    top = np.tan(fov * 0.5) * z_near
    bottom = -top
    
    left = aspectratio * bottom
    right = aspectratio * top

    return clip_matrix(left, right, bottom, top, z_near, z_far, perspective=True)

####################################################################################################################################################
####################################################################################################################################################

def getPerspectiveMatrix(fov, aspect, near, far):

    f = 1.0 / tan(fov/2.0)

    return numpy.array([[f/(aspect*1.0),    0,        0,                                0],
                       [0,                  f,        0,                                0],
                       [0,                  0,        (far+near)/(1.0*(near-far)),    2*far*near/(1.0*(near-far))],
                       [0,                  0,        -1,                               0]])

####################################################################################################################################################
####################################################################################################################################################

def loadCamerasParameters(path):

    camFile = open(path,'r')

    tree = ET.parse(camFile)
    root = tree.getroot()

    cameras = {}

    for Frame in root:

        currentCamera = {}
        currentFrame = int(float(Frame.attrib['Keyframe']))

        for Attr in Frame:

            if (Attr.attrib.get("view-angle") != None):
                currentCamera["fovy"] = Attr.attrib["view-angle"]

            if (Attr.attrib.get("verticalFieldOfView") != None):
                currentCamera["fovx"] = Attr.attrib["verticalFieldOfView"]

            if (Attr.attrib.get("location") != None):
                currentCamera["location"] = map(float,Attr.attrib["location"].split("  "))

            if (Attr.attrib.get("aim") != None):
                currentCamera["aim"] = map(float,Attr.attrib["aim"].split("  "))

            if (Attr.attrib.get("lookup-vector") != None):
                currentCamera["lookup-vector"] = map(float,Attr.attrib["lookup-vector"].split("  "))

            if (Attr.attrib.get("horizontalFilmAperture") != None):
                currentCamera["horizontalFilmAperture"] = Attr.attrib["horizontalFilmAperture"]

            if (Attr.attrib.get("verticalFilmAperture") != None):
                currentCamera["verticalFilmAperture"] = Attr.attrib["verticalFilmAperture"]

            if (Attr.attrib.get("width") != None):
                currentCamera["width"] = Attr.attrib["width"]

            if (Attr.attrib.get("height") != None):
                currentCamera["height"] = Attr.attrib["height"]

            if (Attr.attrib.get("deviceAspectRatio") != None):
                currentCamera["deviceAspectRatio"] = Attr.attrib["deviceAspectRatio"]

            if (Attr.attrib.get("nearClipPlace") != None):
                currentCamera["nearClipPlace"] = Attr.attrib["nearClipPlace"]

            if (Attr.attrib.get("farClipPlane") != None):
                currentCamera["farClipPlane"] = Attr.attrib["farClipPlane"]
            
        cameras[currentFrame] = currentCamera

    return cameras            

####################################################################################################################################################
####################################################################################################################################################

def loadLightsParameters(path):

    lightsParameters = {}
    
    lightFile = open(path,'r')

    tree = ET.parse(lightFile)
    root = tree.getroot()
    
    for xmlType in root:

        lightType = xmlType.attrib['name']
        lightsParameters[lightType] = []

        if lightType == "ambientLight" :

            for xmlLight in xmlType:

                light = { 
                    "brightness" :    float(xmlLight.attrib['brightness']),
                    "rgb" :           map(float,xmlLight.attrib['rgb'].split(" ")),
                    "name" :          xmlLight.attrib['name']
                }

                lightsParameters[lightType].append(dict(light))

        if lightType == "directionalLight":

            for xmlLight in xmlType:

                light = {
                        "brightness" :  float(xmlLight.attrib['brightness']),
                        "rgb" :         map(float, xmlLight.attrib['rgb'].split(" ")),
                        "direction" :   map(float, xmlLight.attrib['direction'].split(" ")),
                        "name" :        xmlLight.attrib['name']
                        }

                lightsParameters[lightType].append(dict(light))

    return lightsParameters

####################################################################################################################################################
####################################################################################################################################################

def packedList(lights, component):
    packedList = []
    for light in lights:
        if type(light[component]) == list:
            for value in light[component]:
                packedList.append(value)
        else:            
            packedList.append(light[component])
    return packedList      

####################################################################################################################################################
####################################################################################################################################################

def vec(*args):
    return (GLfloat * len(args))(*args)