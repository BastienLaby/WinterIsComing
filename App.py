'''
    - Created with Sublime Text 2.
    - User: song.chen
    - Date: 2014-12-17
    - Time: 10:49:40
    - Contact: song.chen@qunar.com
'''
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from math import cos, sin
import time

from OpenGL.GL import *
from OpenGL.GLU import *
import OpenGL.GLUT as glut

import pygame

from GLSLProgram import GLSLProgram
from GLTexture import Texture, TextureMS
import Camera
import Mesh
import SnowEngine
from Tools import glCheckError, glCheckFbo

def draw_quad():
    glBegin(GL_QUADS)
    glVertex2f(0.0, 0.0)
    glVertex2f(1.0, 0.0)
    glVertex2f(1.0, 1.0)
    glVertex2f(0.0, 1.0)
    glEnd()

class Viewport():

    """
    A class which render the different passes of a .obj file, depending on the Maya parameters.
    """

    def __init__(self):

        screen = pygame.display.set_mode((1280, 720), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.width, self.height = screen.get_size()

        pygame.init()

        print "OpenGL Informations : "
        print "\t" + "Vendor : " + glGetString(GL_VENDOR)
        print "\t" + "Renderer : " + glGetString(GL_RENDERER)
        print "\t" + "Version : " + glGetString(GL_VERSION)
        print "\t" + "GLSL : " + glGetString(GL_SHADING_LANGUAGE_VERSION)

        self.clock   = pygame.time.Clock()
        self.key     = pygame.key.get_pressed()
        pygame.key.set_repeat(3, 40)

        self.camera = Camera.Camera()
        self.camera.up = [0, 1, 0]
        self.camera.eye = [-13, 7, -10]
        self.camera.target = [0, 0, -10]
        
        self.computeShaders()

        print('Load geometry...')

        self.obj = Mesh.Mesh()
        self.obj.loadFromObj("E:/Bastien/WinterIsComing/assets/bedroom/bedroom.obj")
        # self.obj.loadFromObj("C:/Users/Bastien/Documents/work/AngeloChristmas/scenes/bedroom/bedroom.obj")
        self.obj.generateGLLists()

        # self.ground = Mesh.Mesh()
        # self.ground.loadFromObj("E:/Bastien/AngeloChristmas/scenes/bedroom/ground.obj")
        # self.ground.generateGLLists()

        self.loadTextures()
        self.loadFbos()
        

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        self.se = SnowEngine.SnowEngine()
        self.se.setSize([60, 30])
        self.se.setRate(25)
        self.se.setHeight(10)

    def loadTextures(self):
        nbSample = 8
        self.texs = {}
        self.texs["color_ms"] = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.texs["illum_ms"] = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.texs["id_ms"] = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.texs["shadowmap_ms"] = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.texs["depth_ms"] = TextureMS(nbSample, GL_DEPTH_COMPONENT24, self.width, self.height)
        self.texs["color"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["illum"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["id"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["shadowmap"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["depth"] = Texture(GL_DEPTH_COMPONENT24, self.width, self.height, GL_DEPTH_COMPONENT, GL_FLOAT)

    def loadFbos(self):
        self.FBOMultisampled = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBOMultisampled)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.texs["color_ms"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, GL_TEXTURE_2D_MULTISAMPLE, self.texs["illum_ms"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT2, GL_TEXTURE_2D_MULTISAMPLE, self.texs["id_ms"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT3, GL_TEXTURE_2D_MULTISAMPLE, self.texs["shadowmap_ms"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D_MULTISAMPLE, self.texs["depth_ms"].id, 0)
        glCheckFbo()

        self.FBO = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texs["color"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, GL_TEXTURE_2D, self.texs["illum"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT2, GL_TEXTURE_2D, self.texs["id"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT3, GL_TEXTURE_2D, self.texs["shadowmap"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.texs["depth"].id, 0)
        glCheckFbo()

    def computeShaders(self):
        pathToShaders = "E:/Bastien/WinterIsComing/shaders/"
        # pathToShaders = "C:/Users/Bastien/Documents/work/WinterIsComing/shaders/"
        self.programs = {}
        self.programs["prepass"] = GLSLProgram(pathToShaders + "prepass.vs", pathToShaders + "prepass.fs")
        self.programs["blit"] = GLSLProgram(pathToShaders + "blit.vs", pathToShaders + "blit.fs")
        glCheckError()

    def handleEvents(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                exit()

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.dict['size']
                print'reload'
                self.loadTextures()
                self.loadFbos()

            elif event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_SPACE:
                    self.computeShaders()

                if event.key == pygame.K_1:
                    self.displayedPass = "ColorPass"

            elif event.type == pygame.MOUSEMOTION:
                dx = event.pos[0] - self.width/2
                dy = event.pos[1] - self.height/2
                self.camera.target = [0, -dy * 0.01, -10 + dx * 0.01]


    def startRendering(self):

        self.running = True

        while self.running:

            self.clock.tick(30)
            self.handleEvents()

            

            fov = 60
            aspect = float(self.width) / float(self.height)
            znear = 0.1
            zfar = 1000.0

            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(fov, aspect, znear, zfar)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            gluLookAt(self.camera.eye[0], self.camera.eye[1], self.camera.eye[2],
                self.camera.target[0], self.camera.target[1], self.camera.target[2],
                self.camera.up[0], self.camera.up[1], self.camera.up[2]) 

            
            self.se.generateParticle()

            self.render()

            self.se.updateParticles()

            pygame.display.flip()

    def render(self):

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBOMultisampled)

        glDrawBuffers(4, (GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1, GL_COLOR_ATTACHMENT2, GL_COLOR_ATTACHMENT3))

        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glUseProgram(self.programs["prepass"].id)
        textureLocation = glGetUniformLocation(self.programs["prepass"].id, "uColorTexture")
        cameraPositionLocation = glGetUniformLocation(self.programs["prepass"].id, "uCameraPosition")
        glUniform1i(textureLocation, 0);
        glUniform3f(cameraPositionLocation, self.camera.eye[0], self.camera.eye[1], self.camera.eye[2]);

        glActiveTexture(GL_TEXTURE0)

        self.obj.draw()
        self.se.drawSnow()

        # Transfer from Multisampled FBO to classic FBO

        self.transferTexture(self.FBOMultisampled, self.FBO, GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT0, colorTexture=True)
        self.transferTexture(self.FBOMultisampled, self.FBO, GL_COLOR_ATTACHMENT1, GL_COLOR_ATTACHMENT1, colorTexture=True)
        self.transferTexture(self.FBOMultisampled, self.FBO, GL_COLOR_ATTACHMENT2, GL_COLOR_ATTACHMENT2, colorTexture=True)
        self.transferTexture(self.FBOMultisampled, self.FBO, GL_COLOR_ATTACHMENT3, GL_COLOR_ATTACHMENT3, colorTexture=True)
        self.transferTexture(self.FBOMultisampled, self.FBO, None, None, colorTexture=False)

        # Blit the result

        self.blitToScreen(0, 0, self.width, self.height, self.texs["color"].id)
        self.blitToScreen(0, 0, self.width/4, self.height/4, self.texs["illum"].id)
        self.blitToScreen(self.width/4, 0, self.width/4, self.height/4, self.texs["id"].id)
        self.blitToScreen(2*self.width/4, 0, self.width/4, self.height/4, self.texs["shadowmap"].id)

    def transferTexture(self, srcFbo, dstFbo, srcBuffer, dstBuffer, colorTexture=True):
        glBindFramebuffer(GL_READ_FRAMEBUFFER, srcFbo)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, dstFbo)
        if colorTexture:
            glReadBuffer(srcBuffer)
            glDrawBuffer(dstBuffer)
            glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_LINEAR)
        else:
            glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_DEPTH_BUFFER_BIT, GL_NEAREST);

    def blitToScreen(self, xPos, yPos, width, height, textureID):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(xPos, yPos, width, height)
        glUseProgram(self.programs["blit"].id)
        u = glGetUniformLocation(self.programs["blit"].id, "uTexture")
        glUniform1i(u, 0)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, textureID)
        glDisable(GL_DEPTH_TEST)
        draw_quad()
        glEnable(GL_DEPTH_TEST)
        glBindTexture(GL_TEXTURE_2D, 0)
        glUseProgram(0)


####################################################################################################################################################



viewport = Viewport()
viewport.startRendering()