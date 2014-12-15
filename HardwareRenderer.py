#!/usr/bin/env python
# -*- coding: utf-8 -*-

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.constants import GLuint
from OpenGL.raw import *

import pygame

import sys
from math import *
from ctypes import *

from OBJLoader import *
from GLProgram import *
import GLTools
from GLTexture import *
import UsefulFunctions as UF
import Camera


class Scene():

    """
    A class which render the different passes of a .obj file, depending on the Maya parameters.
    """

    def __init__(self):

        # --------------------------------------------------------------------------------------------------------------------
        # Window/Scene initialisation
        # --------------------------------------------------------------------------------------------------------------------


        # Window Initialisation
        screen = pygame.display.set_mode((1280, 720), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.width, self.height = screen.get_size()

        # Pygame & GL Initialisation
        pygame.init()

        print "OpenGL Informations : "
        print "\t" + "Vendor : " + glGetString(GL_VENDOR)
        print "\t" + "Renderer : " + glGetString(GL_RENDERER)
        print "\t" + "Version : " + glGetString(GL_VERSION)
        print "\t" + "GLSL : " + glGetString(GL_SHADING_LANGUAGE_VERSION)

        # Window porameters
        self.clock   = pygame.time.Clock()
        self.key     = pygame.key.get_pressed()
        pygame.key.set_repeat(3, 40)

        self.camera = Camera.Camera()
        self.camera.eye = [-20, 10.0, -13.0]
        self.camera.target = [0, 0, -13.0]
        self.camera.up = [0, 1, 0]
        
        # --------------------------------------------------------------------------------------------------------------------
        # Load GL Programs
        # --------------------------------------------------------------------------------------------------------------------

        self.computeShaders()
        
        # --------------------------------------------------------------------------------------------------------------------
        # Load Geometry
        # --------------------------------------------------------------------------------------------------------------------

        print('Load geometry...')
        self.obj = self.loadOBJ("E:/Bastien/AngeloChristmas/scenes/bedroom/bedroom.obj")
        self.ground = self.loadOBJ("E:/Bastien/AngeloChristmas/scenes/bedroom/ground.obj")

        self.loadTextures()

        # --------------------------------------------------------------------------------------------------------------------
        # FBO Management
        # --------------------------------------------------------------------------------------------------------------------
        
        self.FBOMultisampled = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBOMultisampled)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.DiffuseTextureMS.id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D_MULTISAMPLE, self.DepthTextureMS.id, 0)
        GLTools.checkFBO()
        GLTools.checkGLErrors()

        self.FBO = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.DiffuseTexture.id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.DepthTexture.id, 0)

        GLTools.checkFBO()
        GLTools.checkGLErrors()

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
        # --------------------------------------------------------------------------------------------------------------------
        # Start Loop
        # --------------------------------------------------------------------------------------------------------------------

        self.displayedPass = "ColorPass"

        self.running = True
        self.gameLoop()

####################################################################################################################################################

    def loadTextures(self):

        # --------------------------------------------------------------------------------------------------------------------
        # Multisampled Texture Management
        # --------------------------------------------------------------------------------------------------------------------

        nbSample = 32

        self.DiffuseTextureMS = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.NormalTextureMS = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.DepthTextureMS = TextureMS(nbSample, GL_DEPTH_COMPONENT24, self.width, self.height)
        self.DepthColorTextureMS = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.LightTextureMS = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.IDTextureMS = TextureMS(nbSample, GL_RGBA8, self.width, self.height)
        self.NoiseTextureMS = TextureMS(nbSample, GL_RGBA8, self.width, self.height)

        # --------------------------------------------------------------------------------------------------------------------
        # Basic Texture Management
        # --------------------------------------------------------------------------------------------------------------------

        self.DiffuseTexture     = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.NormalTexture      = Texture(GL_RGBA8, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.DepthTexture       = Texture(GL_DEPTH_COMPONENT24, self.width, self.height, GL_DEPTH_COMPONENT, GL_FLOAT)
        self.LightTexture       = Texture(GL_RGBA, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.IDTexture          = Texture(GL_RGBA, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)

####################################################################################################################################################


    def loadOBJ(self, objFilename):

        obj = OBJ(objFilename)

        if(obj == None):
            print('Problem when loading %s. End of program' % objFilename)
            self.running = False

        return obj

####################################################################################################################################################

    def computeShaders(self):

        pathToShaders = "E:/Bastien/WinterIsComing/shaders/"

        self.diffuseProgram = GLProgram(pathToShaders + "diffuseVS.glsl", pathToShaders + "diffuseFS.glsl")
        self.normalProgram = GLProgram(pathToShaders + "normalVS.glsl", pathToShaders + "normalFS.glsl")
        self.phongProgram = GLProgram(pathToShaders + "phongVS.glsl", pathToShaders + "phongFS.glsl")
        self.depthProgram = GLProgram(pathToShaders + "depthVS.glsl", pathToShaders + "depthFS.glsl")
        self.idProgram = GLProgram(pathToShaders + "idVS.glsl", pathToShaders + "idFS.glsl")
        self.dirlightProgram = GLProgram(pathToShaders + "lightVS.glsl", pathToShaders + "dirlightFS.glsl") 

        GLTools.checkGLErrors()

####################################################################################################################################################

    def renderFrame(self, passName):

        print("render")

        # --------------------------------------------------------------------------------------------------------------------
        # Update the camera parameters, Projection and Lookat matrix
        # --------------------------------------------------------------------------------------------------------------------

        fov = 40
        aspect = float(self.width) / float(self.height)
        znear = 0.1
        zfar = 1000.0

        ProjectionMatrix = UF.getPerspectiveMatrix(fov, aspect, znear, zfar)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(fov, aspect, znear, zfar)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.camera.eye[0], self.camera.eye[1], self.camera.eye[2],
            self.camera.target[0], self.camera.target[1], self.camera.target[2],
            self.camera.up[0], self.camera.up[1], self.camera.up[2]) 
        
        # --------------------------------------------------------------------------------------------------------------------
        # Rendering
        # --------------------------------------------------------------------------------------------------------------------       

        if (passName == "ColorPass"):
            self.renderDiffuse()

        elif (passName == "NormalPass"):
            self.renderNormals()

        elif (passName == "LightPass"):
            self.renderLight()

        elif (passName == "DepthPass"):
            self.renderDepth()

        pygame.display.flip()

        GLTools.checkGLErrors()
        
####################################################################################################################################################
####################################################################################################################################################

    def renderscene(self):
        glCallList(self.obj.gl_list)
        glCallList(self.ground.gl_list)

####################################################################################################################################################
####################################################################################################################################################

    def handleEvents(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                exit()

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.dict['size']
                self.loadTextures()

            # Keyboard events
            elif event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_SPACE:
                    self.computeShaders()

                if event.key == pygame.K_1:
                    self.displayedPass = "ColorPass"
                if event.key == pygame.K_2:
                    self.displayedPass = "NormalPass"
                if event.key == pygame.K_3:
                    self.displayedPass = "LightPass"
                if event.key == pygame.K_4:
                    self.displayedPass = "DepthPass"
                if event.key == pygame.K_5:
                    self.displayedPass = "IDPass"
                if event.key == pygame.K_7:
                    self.displayedPass = "NoisePass"


####################################################################################################################################################
####################################################################################################################################################
     
    def gameLoop(self):

        self.clock = pygame.time.Clock()

        while self.running == True:

            self.clock.tick(30)

            self.handleEvents()

            self.renderFrame(self.displayedPass)

####################################################################################################################################################
####################################################################################################################################################

    def renderDiffuse(self):

        # Specify buffers attachements

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.DiffuseTexture.id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.DepthTexture.id, 0)
        GLTools.checkFBO()

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBOMultisampled)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.DiffuseTextureMS.id, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D_MULTISAMPLE, self.DepthTextureMS.id, 0)
        glDrawBuffer(GL_COLOR_ATTACHMENT0)
        GLTools.checkFBO()

        # Clean

        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Render

        glUseProgram(self.diffuseProgram.id)
        glUniform1i(glGetUniformLocation(self.diffuseProgram.id, "tex"), 0)
        glCallList(self.obj.gl_list)

        # Blit

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBOMultisampled)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.FBO)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_COLOR_ATTACHMENT0)            
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_DEPTH_BUFFER_BIT, GL_NEAREST)

        # Draw

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBO)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_BACK)            
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

    def renderNormals(self):

        # Specify buffers attachements

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.NormalTexture.id, 0)
        GLTools.checkFBO()

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBOMultisampled)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.NormalTextureMS.id, 0)
        glDrawBuffer(GL_COLOR_ATTACHMENT0)
        GLTools.checkFBO()

        # Clean

        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Render

        glUseProgram(self.normalProgram.id)            
        self.renderscene()

        # Blit

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBOMultisampled)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.FBO)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_COLOR_ATTACHMENT0)            
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

        # Draw

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBO)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_BACK)            
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

    def renderLight(self):

        # Specify buffers attachements

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.LightTexture.id, 0)
        GLTools.checkFBO()

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBOMultisampled)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.LightTextureMS.id, 0)
        glDrawBuffer(GL_COLOR_ATTACHMENT0)
        GLTools.checkFBO()

        # Clean

        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_ONE, GL_ONE)

        # Render

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.NormalTexture.id)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.DepthTexture.id)
        
        # Blit

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBOMultisampled)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.FBO)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_COLOR_ATTACHMENT0)            
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

        # Draw

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBO)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_BACK)            
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

        glDisable(GL_BLEND)

    def renderDepth(self):

        # Specify buffers attachements

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.DepthColorTexture.id, 0)
        GLTools.checkFBO()

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBOMultisampled)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.DepthColorTextureMS.id, 0)
        glDrawBuffer(GL_COLOR_ATTACHMENT0)
        GLTools.checkFBO()
        
        # Clean

        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Render

        glUseProgram(self.depthProgram.id)
        self.renderscene()

        # Blit

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBOMultisampled)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.FBO)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_COLOR_ATTACHMENT0)            
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

        # Draw

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBO)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_BACK)            
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

####################################################################################################################################################
####################################################################################################################################################

scene = Scene()