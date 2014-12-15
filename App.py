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
import Cube
import SnowEngine
from Tools import glCheckError, glCheckFbo

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
        
        self.computeShaders()

        print('Load geometry...')

        # self.obj = Mesh.Mesh()
        # # self.obj.loadFromObj("E:/Bastien/AngeloChristmas/scenes/bedroom/bedroom.obj")
        # self.obj.loadFromObj("C:/Users/Bastien/Documents/work/AngeloChristmas/scenes/bedroom/bedroom.obj")
        # self.obj.generateGLLists()

        # self.ground = Mesh.Mesh()
        # self.ground.loadFromObj("E:/Bastien/AngeloChristmas/scenes/bedroom/ground.obj")
        # self.ground.generateGLLists()

        self.cube = Cube.Cube()

        self.loadTextures()
        
        self.FBOMultisampled = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBOMultisampled)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.texs["color_ms"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D_MULTISAMPLE, self.texs["depth_ms"].id, 0)
        glCheckFbo()

        self.FBO = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texs["color"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.texs["depth"].id, 0)
        glCheckFbo()

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        self.se = SnowEngine.SnowEngine()
        self.se.setSize([250, 250])
        self.se.setRate(20)
        self.se.setHeight(25)

        self.displayedPass = "ColorPass"

####################################################################################################################################################

    def loadTextures(self):
        nbSample = 8
        self.texs = {}
        self.texs["color_ms"] = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.texs["depth_ms"] = TextureMS(nbSample, GL_DEPTH_COMPONENT24, self.width, self.height)
        self.texs["color"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["depth"] = Texture(GL_DEPTH_COMPONENT24, self.width, self.height, GL_DEPTH_COMPONENT, GL_FLOAT)

####################################################################################################################################################

    def computeShaders(self):
        # pathToShaders = "E:/Bastien/WinterIsComing/shaders/"
        pathToShaders = "C:/Users/Bastien/Documents/work/WinterIsComing/shaders/"
        self.programs = {}
        self.programs["prepass"] = GLSLProgram(pathToShaders + "prepass.vs", pathToShaders + "prepass.fs")
        glCheckError()
        
####################################################################################################################################################

    def renderscene(self):
        # self.obj.draw()
        # self.ground.draw()
        self.cube.draw()
        pass

####################################################################################################################################################

    def handleEvents(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                exit()

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.dict['size']
                self.loadTextures()

            elif event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_SPACE:
                    self.computeShaders()

                if event.key == pygame.K_1:
                    self.displayedPass = "ColorPass"

####################################################################################################################################################
     
    def startRendering(self):

        self.running = True

        while self.running:

            self.clock.tick(30)
            self.handleEvents()

            self.camera.eye = [50 * cos(time.time()), 20, 50 * sin(time.time())]
            self.camera.target = [0, 0, 0]

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

            pygame.display.flip()

####################################################################################################################################################

    def render(self):

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texs["color"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.texs["depth"].id, 0)
        glCheckFbo()

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBOMultisampled)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.texs["color_ms"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D_MULTISAMPLE, self.texs["depth_ms"].id, 0)
        glDrawBuffer(GL_COLOR_ATTACHMENT0)
        glCheckFbo()

        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        projLoc = glGetUniformLocation(self.programs["prepass"].id, "u_projection")
        viewLoc = glGetUniformLocation(self.programs["prepass"].id, "u_view")

        self.renderscene()
        self.se.drawSnow()
        self.se.updateParticles()

        # Blit

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBOMultisampled)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.FBO)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_COLOR_ATTACHMENT0)            
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_DEPTH_BUFFER_BIT, GL_NEAREST)

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBO)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_BACK)            
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

####################################################################################################################################################

viewport = Viewport()
viewport.startRendering()