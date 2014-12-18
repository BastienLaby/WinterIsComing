import os

from OpenGL.GL import *
from OpenGL.arrays import vbo

import pygame

import numpy as np

from ctypes import c_float

class Mesh:

    def __init__(self):
        self.materials = {}
        self.glList = 0

    def loadFromObj(self, filename):

        f = None
        try:
            f = open(filename, "r")
        except IOError:
            raise OBJFrameLoadingError('Cannot open %s' % filename)

        self.rootPath = "/".join(filename.split("/")[:-1]) + "/"

        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        
        materialName = None

        for line in f:
            
            if line.startswith('#'):
                continue

            values = line.split()

            if not values:
                continue

            if values[0] == 'v':
                self.vertices.append(map(float, values[1:4]))

            elif values[0] == 'vn':
                self.normals.append(map(float, values[1:4]))

            elif values[0] == 'vt':
                self.texcoords.append(map(float, values[1:3]))

            elif values[0] in ('usemtl', 'usemat'):
                materialName = values[1]

            elif values[0] == 'mtllib':
                self.loadMaterialFile(values[1])                

            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, materialName))
        return

    def loadMaterialFile(self, filename):

        f = None
        try:
            f = open(self.rootPath + filename, "r")
        except IOError:
            print('The program cannot load %s.\nEnd of program.' % str(self.rootPath + filename))
            return None 

        currentMTLName = ""

        for line in f:

            if line.startswith('#'):
                continue

            values = line.split()

            if not values:
                continue

            if values[0] == 'newmtl':
                currentMTLName = values[1]
                if(not currentMTLName in self.materials):
                    self.materials[currentMTLName] = {}
                else:
                    continue

            elif values[0] == 'map_Kd':
          
                self.hasToScale = False
                scaleX, scaleY = 1, 1
                if(values[1] == '-s'):
                    hasToScale = True
                    self.scaleX, self.scaleY = values[2], values[3]
                    textureFile = self.rootPath + values[4]
                else:
                    textureFile = self.rootPath + values[1]

                data = pygame.image.load(os.path.join("", textureFile))
                image = pygame.image.tostring(data, 'RGBA', 1)
                w, h = data.get_rect().size
                
                # Generate GL Texture
                self.materials[currentMTLName]['textureID'] = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, self.materials[currentMTLName]['textureID'])
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)

            else:
                self.materials[currentMTLName][values[0]] = map(float, values[1:])

    def generateGLLists(self):

        glDeleteLists(self.glList, 1)
        self.glList = glGenLists(1)
        glNewList(self.glList, GL_COMPILE)

        for face in self.faces:
            vertices, normals, texture_coords, materialName = face
            if materialName in self.materials:
                currentMaterial = self.materials[materialName]
                if 'textureID' in currentMaterial:
                    glActiveTexture(GL_TEXTURE0)
                    glBindTexture(GL_TEXTURE_2D, currentMaterial['textureID'])
                else:
                    rgb = currentMaterial['Kd']
                    if rgb:
                        glColor3f(rgb[0], rgb[1], rgb[2])
            else:
                glColor3f(1.0, 1.0, 1.0)
            
            glBegin(GL_POLYGON)
            for i in range(len(vertices)):
                if normals[i] > 0:
                    normal = self.normals[normals[i] - 1]
                    glNormal3f(normal[0], normal[1], normal[2])
                if texture_coords[i] > 0:
                    tex = self.texcoords[texture_coords[i] - 1]
                    if "SET1:lambert105SG" in materialName:
                        glTexCoord2f(0.5*tex[0], 0.5*tex[1])
                    else:
                        glTexCoord2f(tex[0], tex[1])
                else:
                    glTexCoord2f(1.0, 1.0)
                vertex = self.vertices[vertices[i] - 1]
                glVertex3f(vertex[0], vertex[1], vertex[2])
            glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glEndList()

    def draw(self):
        glCallList(self.glList)