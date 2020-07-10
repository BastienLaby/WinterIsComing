from random import random
from math import pi, cos, sin

from OpenGL import GL


class SnowParticle:
    def __init__(self, xyz, rgb, size, speed):
        self.xyz = xyz
        self.rgb = rgb
        self.size = size
        self.speed = speed


class SnowEngine:
    def __init__(self):
        self.particles = []
        self.size = [50, 50]
        self.height = 50
        self.heightVeriation = 5
        self.rate = 5
        self.minimumParticleSpeed = 0.05
        self.maximumParticleSpeed = 0.2
        self.spList = GL.glGenLists(1)
        GL.glNewList(self.spList, GL.GL_COMPILE)
        GL.glBegin(GL.GL_TRIANGLE_FAN)
        for i in range(20):
            theta = i * 2.0 * pi / 20.0
            x = cos(theta)
            y = sin(theta)
            GL.glVertex3f(x, y, 0.0)
        GL.glEnd()
        GL.glEndList()

    def enable(self):
        self.enable = True

    def disable(self):
        self.enable = False

    def generateParticle(self):
        for i in range(self.rate):
            xyz = [random(), self.height + random() * self.heightVeriation, random()]
            xyz[0] = xyz[0] * self.size[1] - self.size[1] / 2.0
            xyz[2] = xyz[2] * self.size[0] - self.size[0] / 2.0
            rgb = [random(), random(), random()]
            size = random() * 0.6
            speed = min(
                self.maximumParticleSpeed, max(self.minimumParticleSpeed, random())
            )
            p = SnowParticle(xyz, rgb, size, speed)
            self.particles.append(p)

    def drawSnow(self):
        for p in self.particles:
            GL.glPushMatrix()
            GL.glTranslatef(p.xyz[0], p.xyz[1], p.xyz[2])
            GL.glRotatef(90, 0, 1, 0)
            GL.glScalef(p.size, p.size, 1.0)
            GL.glColor4f(p.rgb[0], p.rgb[1], p.rgb[2], p.size)
            GL.glCallList(self.spList)
            GL.glPopMatrix()

    def updateParticles(self):
        for p in self.particles:
            p.xyz[1] -= p.speed
            if p.xyz[1] < 0.0:
                self.particles.remove(p)

    def setSource(self, size, height, heightVariation, rate):
        self.size = size
        self.height = height
        self.heightVariation = heightVariation
        self.rate = rate

    def setSize(self, size):
        self.size = size

    def setHeight(self, height):
        self.height = height

    def setHeightVariation(self, heightVariation):
        self.setHeightVariation = heightVariation

    def setRate(self, rate):
        self.rate = rate
