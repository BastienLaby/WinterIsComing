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

import numpy as np
import numpy.linalg as npla
import pygame

from GLSLProgram import GLSLProgram
from GLTexture import Texture, TextureMS
import Camera
import Mesh
import SnowEngine
from Tools import glCheckError, glCheckFbo
import uf

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

        self.texs["depth_ms"] = TextureMS(nbSample, GL_DEPTH_COMPONENT24, self.width, self.height)
        self.texs["color_ms"] = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.texs["illum_ms"] = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.texs["id_ms"] = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.texs["normal_ms"] = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        
        self.texs["depth"] = Texture(GL_DEPTH_COMPONENT24, self.width, self.height, GL_DEPTH_COMPONENT, GL_FLOAT)
        self.texs["depthblit"] = Texture(GL_DEPTH_COMPONENT24, self.width, self.height, GL_DEPTH_COMPONENT, GL_FLOAT)
        self.texs["color"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["illum"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["id"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["normal"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["ssao"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.texs["rot"] = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)

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

        self.fboSsao = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fboSsao)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texs["ssao"].id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.texs["depthblit"].id, 0)
        glCheckFbo()

    def computeShaders(self):
        pathToShaders = "E:/Bastien/WinterIsComing/shaders/"
        # pathToShaders = "C:/Users/Bastien/Documents/work/WinterIsComing/shaders/"
        self.programs = {}
        self.programs["prepass"] = GLSLProgram(pathToShaders + "prepass.vs", pathToShaders + "prepass.fs")
        self.programs["blit"] = GLSLProgram(pathToShaders + "blit.vs", pathToShaders + "blit.fs")
        self.programs["ssao"] = GLSLProgram(pathToShaders + "ssao.vs", pathToShaders + "ssao.fs")
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

            self.fov = 60
            self.aspect = float(self.width) / float(self.height)
            self.znear = 0.01
            self.zfar = 100.0

            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(self.fov, self.aspect, self.znear, self.zfar)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            gluLookAt(self.camera.eye[0], self.camera.eye[1], self.camera.eye[2],
                self.camera.target[0], self.camera.target[1], self.camera.target[2],
                self.camera.up[0], self.camera.up[1], self.camera.up[2]) 

            self.se.generateParticle()
            self.render()
            self.se.updateParticles()

            self.renderSSAO()

            pygame.display.flip()

    def render(self):

        glBindFramebuffer(GL_FRAMEBUFFER, self.fboPrepassMS)
        glDrawBuffers(4, (GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1, GL_COLOR_ATTACHMENT2, GL_COLOR_ATTACHMENT3))

        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glUseProgram(self.programs["prepass"].id)
        textureLocation = glGetUniformLocation(self.programs["prepass"].id, "uColorTexture")
        cameraPositionLocation = glGetUniformLocation(self.programs["prepass"].id, "uCameraPosition")
        isSnowLocation = glGetUniformLocation(self.programs["prepass"].id, "uIsSnow")

        glUniform1i(textureLocation, 0);
        glUniform3f(cameraPositionLocation, self.camera.eye[0], self.camera.eye[1], self.camera.eye[2]);

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

    def renderSSAO(self):

        glBindFramebuffer(GL_FRAMEBUFFER, self.fboSsao)
        glDrawBuffers(1, (GL_COLOR_ATTACHMENT0))
        glViewport(0, 0, self.width, self.height)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)

        glUseProgram(self.programs["ssao"].id)

        glUseProgram(self.programs["ssao"].id)
        glUniform1i(glGetUniformLocation(self.programs["ssao"].id, "uNormalTexture"), 0)
        glUniform1i(glGetUniformLocation(self.programs["ssao"].id, "uDepthTexture"), 1)
        glUniform1i(glGetUniformLocation(self.programs["ssao"].id, "uRotationTexture"), 2)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texs["normal"].id)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.texs["depth"].id)
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self.texs["rot"].id)

        proj = uf.create_perspective_matrix_improved(self.fov, self.aspect, self.znear, self.zfar)
        invProj = npla.inv(proj)
        glUniformMatrix4fv(glGetUniformLocation(self.programs["ssao"].id, "uInverseProjectionMatrix"), 1, GL_TRUE, invProj.astype(np.float32))

        kernelRadius = 0.2
        sampleCount = 128

        glUniform2fv(glGetUniformLocation(self.programs["ssao"].id, "uSSAOSamples"), sampleCount, uf.generate_ssao_kernel(kernelRadius, sampleCount))
        glUniform2f(glGetUniformLocation(self.programs["ssao"].id, "uSXY"), self.width/3.0, self.height/3.0)
        
        # Render

        glDisable(GL_DEPTH_TEST)
        glClear(GL_COLOR_BUFFER_BIT)

        draw_quad()

        self.blitToScreen(0, self.height/4, 3*self.width/4, self.height, self.texs["ssao"].id)

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