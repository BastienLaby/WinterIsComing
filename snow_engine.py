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
        self.size = [100, 40]
        self.height = 25
        self.height_variation = 5
        self.rate = 4
        self.min_particle_speed = 0.05
        self.max_particle_speed = 0.2
        self.gl_list = GL.glGenLists(1)
        GL.glNewList(self.gl_list, GL.GL_COMPILE)
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

    def generate_particles(self):
        for i in range(self.rate):
            xyz = [random(), self.height + random() * self.height_variation, random()]
            xyz[0] = xyz[0] * self.size[1] - self.size[1] / 2.0
            xyz[2] = xyz[2] * self.size[0] - self.size[0] / 2.0
            rgb = [random(), random(), random()]
            size = random() * 0.6
            speed = min(self.max_particle_speed, max(self.min_particle_speed, random()))
            p = SnowParticle(xyz, rgb, size, speed)
            self.particles.append(p)

    def draw_snow(self):
        for p in self.particles:
            GL.glPushMatrix()
            GL.glTranslatef(p.xyz[0], p.xyz[1], p.xyz[2])
            GL.glRotatef(90, 0, 1, 0)
            GL.glScalef(p.size, p.size, 1.0)
            GL.glColor4f(p.rgb[0], p.rgb[1], p.rgb[2], p.size)
            GL.glCallList(self.gl_list)
            GL.glPopMatrix()

    def update(self):
        for p in self.particles:
            p.xyz[1] -= p.speed
            if p.xyz[1] < 0.0:
                self.particles.remove(p)
