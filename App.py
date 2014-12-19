#!/usr/bin/env python
# -*- coding: utf-8 -*-
#@author Bastien Laby, December 2014

from math import cos, sin
import time

from OpenGL.GL import *
from OpenGL.GLU import *

import numpy as np
import numpy.linalg as npla

import pygame

from GLSLProgram import GLSLProgram
from GLTexture import Texture, TextureMS
import Mesh
import SnowEngine
from Tools import glCheckError, glCheckFbo
import matrix

def draw_quad():
    glBegin(GL_QUADS)
    glVertex2f(0.0, 0.0)
    glVertex2f(1.0, 0.0)
    glVertex2f(1.0, 1.0)
    glVertex2f(0.0, 1.0)
    glEnd()

class Viewport():

    def __init__(self):

        screen = pygame.display.set_mode((1920, 1200), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE | pygame.FULLSCREEN)
        self.width, self.height = screen.get_size()

        pygame.init()

        print "OpenGL Informations : "
        print "\t" + "Vendor : " + glGetString(GL_VENDOR)
        print "\t" + "Renderer : " + glGetString(GL_RENDERER)
        print "\t" + "Version : " + glGetString(GL_VERSION)
        print "\t" + "GLSL : " + glGetString(GL_SHADING_LANGUAGE_VERSION)

        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        pygame.display.flip()

        self.clock = pygame.time.Clock()
        self.key = pygame.key.get_pressed()
        pygame.key.set_repeat(3, 40)

        self.camera = {}
        self.camera["up"] = [0, 1, 0]
        self.camera["eye"] = [-13, 7, -10]
        self.camera["target"] = [0, 0, -10]
        
        self.computeShaders()

        self.obj = Mesh.Mesh()
        self.obj.loadFromObj("assets/bedroom/bedroom.obj")
        self.obj.generateGLLists()

        self.loadTextures()
        self.loadFbos()
        
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        self.se = SnowEngine.SnowEngine()
        self.se.setSize([100, 40])
        self.se.setRate(4)
        self.se.setHeight(25)

        pygame.mixer.music.load("music/we-three-kings.mp3")
        pygame.mixer.music.play(loops=-1)

    def loadTextures(self):

        nbSample = 8
        self.texs = {}

        self.texs["depth_ms"] = TextureMS(nbSample, GL_DEPTH_COMPONENT24, self.width, self.height)
        self.texs["color_ms"] = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.texs["illum_ms"] = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.texs["id_ms"] = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.texs["normal_ms"] = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        
        self.texs["depth"] = Texture(GL_DEPTH_COMPONENT24, self.width, self.height, GL_DEPTH_COMPONENT, GL_FLOAT)
        self.texs["depthblit"] = Texture(GL_DEPTH_COMPONENT24, self.width, self.height, GL_DEPTH_COMPONENT, GL_FLOAT)
        self.texs["depthblit2"] = Texture(GL_DEPTH_COMPONENT24, self.width, self.height, GL_DEPTH_COMPONENT, GL_FLOAT)
        self.texs["color"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["illum"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["id"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["normal"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["compo"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["dof"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)

    def loadFbos(self):

        self.fboPrepassMS = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fboPrepassMS)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.texs["color_ms"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, GL_TEXTURE_2D_MULTISAMPLE, self.texs["illum_ms"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT2, GL_TEXTURE_2D_MULTISAMPLE, self.texs["id_ms"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT3, GL_TEXTURE_2D_MULTISAMPLE, self.texs["normal_ms"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D_MULTISAMPLE, self.texs["depth_ms"].id, 0)
        glCheckFbo()

        self.fboPrepass = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fboPrepass)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texs["color"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, GL_TEXTURE_2D, self.texs["illum"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT2, GL_TEXTURE_2D, self.texs["id"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT3, GL_TEXTURE_2D, self.texs["normal"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.texs["depth"].id, 0)
        glCheckFbo()

        self.fboCompo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fboCompo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texs["compo"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.texs["depthblit"].id, 0)
        glCheckFbo()

        self.fboDof = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fboDof)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texs["dof"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.texs["depthblit"].id, 0)
        glCheckFbo()

    def computeShaders(self):
        pathToShaders = "shaders/"
        self.programs = {}
        self.programs["prepass"] = GLSLProgram(pathToShaders + "prepass.vs", pathToShaders + "prepass.fs")
        self.programs["blit"] = GLSLProgram(pathToShaders + "blit.vs", pathToShaders + "blit.fs")
        self.programs["compo"] = GLSLProgram(pathToShaders + "compo.vs", pathToShaders + "compo.fs")
        self.programs["dof"] = GLSLProgram(pathToShaders + "dof.vs", pathToShaders + "dof.fs")
        glCheckError()

    def handleEvents(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                exit()

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.dict['size']
                self.loadTextures()
                self.loadFbos()

            elif event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_SPACE:
                    self.computeShaders()

            elif event.type == pygame.MOUSEMOTION:
                dx = event.pos[0] - self.width/2
                dy = event.pos[1] - self.height/2
                self.camera["target"] = [0, -dy * 0.01, -10 + dx * 0.01]


    def startRendering(self):

        self.running = True
        i = 0
        while self.running:

            self.clock.tick(30)
            self.handleEvents()

            self.fov = 60
            self.aspect = float(self.width) / float(self.height)
            self.znear = 0.01
            self.zfar = 1000.0

            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(self.fov, self.aspect, self.znear, self.zfar)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            gluLookAt(self.camera["eye"][0], self.camera["eye"][1], self.camera["eye"][2],
                self.camera["target"][0], self.camera["target"][1], self.camera["target"][2],
                self.camera["up"][0], self.camera["up"][1], self.camera["up"][2]) 

            self.se.generateParticle()
            
            self.render()
            self.renderCompo()
            self.renderDof()

            self.se.updateParticles()

            pygame.display.flip()

    def render(self):

        glBindFramebuffer(GL_FRAMEBUFFER, self.fboPrepassMS)
        glDrawBuffers(4, (GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1, GL_COLOR_ATTACHMENT2, GL_COLOR_ATTACHMENT3))

        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glUseProgram(self.programs["prepass"].id)
        textureLocation = glGetUniformLocation(self.programs["prepass"].id, "uColorTexture")
        cameraPositionLocation = glGetUniformLocation(self.programs["prepass"].id, "uCameraPosition")
        isSnowLocation = glGetUniformLocation(self.programs["prepass"].id, "uIsSnow")

        glUniform1i(textureLocation, 0);
        glUniform3f(cameraPositionLocation, self.camera["eye"][0], self.camera["eye"][1], self.camera["eye"][2]);

        glActiveTexture(GL_TEXTURE0)
        glUniform1i(isSnowLocation, 0)
        self.obj.draw()
        glUniform1i(isSnowLocation, 1)
        self.se.drawSnow()

        # Transfer from Multisampled FBO to classic FBO

        self.transferTexture(self.fboPrepassMS, self.fboPrepass, GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT0, colorTexture=True)
        self.transferTexture(self.fboPrepassMS, self.fboPrepass, GL_COLOR_ATTACHMENT1, GL_COLOR_ATTACHMENT1, colorTexture=True)
        self.transferTexture(self.fboPrepassMS, self.fboPrepass, GL_COLOR_ATTACHMENT2, GL_COLOR_ATTACHMENT2, colorTexture=True)
        self.transferTexture(self.fboPrepassMS, self.fboPrepass, GL_COLOR_ATTACHMENT3, GL_COLOR_ATTACHMENT3, colorTexture=True)
        self.transferTexture(self.fboPrepassMS, self.fboPrepass, None, None, colorTexture=False)

        # Blit the result

        self.blitToScreen(0, 0, self.width, self.height, self.texs["color"].id)
        self.blitToScreen(0, 0, self.width/4, self.height/4, self.texs["illum"].id)
        self.blitToScreen(self.width/4, 0, self.width/4, self.height/4, self.texs["id"].id)
        self.blitToScreen(2*self.width/4, 0, self.width/4, self.height/4, self.texs["normal"].id)

    def renderCompo(self):

        glBindFramebuffer(GL_FRAMEBUFFER, self.fboCompo)
        glDrawBuffers(1, (GL_COLOR_ATTACHMENT0))
        glViewport(0, 0, self.width, self.height)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)

        glUseProgram(self.programs["compo"].id)

        glUniform1i(glGetUniformLocation(self.programs["compo"].id, "uColorTexture"), 0)
        glUniform1i(glGetUniformLocation(self.programs["compo"].id, "uIllumTexture"), 1)
        glUniform1i(glGetUniformLocation(self.programs["compo"].id, "uIDTexture"), 2)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texs["color"].id)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.texs["illum"].id)
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self.texs["id"].id)

        glUniform2f(glGetUniformLocation(self.programs["compo"].id, "uScreenResolution"), self.width, self.height)

        draw_quad()

        self.blitToScreen(0, 0, self.width, self.height, self.texs["compo"].id)

    def renderDof(self):

        glBindFramebuffer(GL_FRAMEBUFFER, self.fboDof)
        glDrawBuffers(1, (GL_COLOR_ATTACHMENT0))
        glViewport(0, 0, self.width, self.height)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)

        glUseProgram(self.programs["dof"].id)

        glUniform1i(glGetUniformLocation(self.programs["dof"].id, "uTexture"), 0)
        glUniform1i(glGetUniformLocation(self.programs["dof"].id, "uDepthTexture"), 1)
        proj = matrix.create_perspective_matrix(self.fov, self.aspect, self.znear, self.zfar)
        invProj = npla.inv(proj)
        glUniformMatrix4fv(glGetUniformLocation(self.programs["dof"].id, "uInverseProjectionMatrix"), 1, GL_TRUE, invProj.astype(np.float32))

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texs["compo"].id)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.texs["depth"].id)
        
        glUniform2i(glGetUniformLocation(self.programs["dof"].id, "uScreenResolution"), self.width, self.height)

        draw_quad()

        self.blitToScreen(0, 0, self.width, self.height, self.texs["dof"].id)

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