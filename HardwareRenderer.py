#!/usr/bin/env python
# -*- coding: utf-8 -*-

# OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.raw import GL
from OpenGL.constants import GLuint
from OpenGL.raw import *

# Context & Window
import pygame

# Tools
import sys, random, time, os
from random import *
from math import *
import numpy as np
import numpy.linalg as LA
from ctypes import *
from time import *

# Personnal modules
from transformations import *
from OBJLoader import *
from GLProgram import *
import GLTools
from GLTexture import *
import UsefulFunctions as UF



class Scene():

    """
    A class which render the different passes of a .obj file, depending on the Maya parameters.
    """

    def __init__(self):

        # --------------------------------------------------------------------------------------------------------------------
        # Window/Scene initialisation
        # --------------------------------------------------------------------------------------------------------------------

        # Global variables declaration
        global width, height, screen

        # Viewport dimensions
        width = 1280
        height = 720 
        self.viewport = (width , height)

        # Window Initialisation
        screen = pygame.display.set_mode(self.viewport, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)

        # Pygame & GL Initialisation
        pygame.init()

        # Window porameters
        self.title   = "CFE GPU RENDER"
        self.clock   = pygame.time.Clock()
        self.key     = pygame.key.get_pressed()
        pygame.key.set_repeat(3, 40)
        
        # --------------------------------------------------------------------------------------------------------------------
        # Load GL Programs
        # --------------------------------------------------------------------------------------------------------------------

        self.computeShaders()
        
        # --------------------------------------------------------------------------------------------------------------------
        # Load Geometry
        # --------------------------------------------------------------------------------------------------------------------

        print('Loading geometry...')
        self.obj = self.loadOBJ("C:/Users/Bastien/Documents/work/WinterIsComing/assets/bedroom/bedroom.obj")  

        # --------------------------------------------------------------------------------------------------------------------
        # SSAO Management
        # --------------------------------------------------------------------------------------------------------------------

        self.SSAO_Power      = 11
        self.SSAO_NoiseLevel = 0
        self.SSAO_DistValue  = 27
        self.SSAO_Radius     = 0.7
        self.SSAO_NumSamples = 48
        self.SSAO_FOV        = 25

        # --------------------------------------------------------------------------------------------------------------------
        # Multisampled Texture Management
        # --------------------------------------------------------------------------------------------------------------------

        nbSample = 32

        self.DiffuseTextureMS = TextureMS(nbSample, GL_RGBA8, width, height)
        self.NormalTextureMS = TextureMS(nbSample, GL_RGBA8, width, height)
        self.DepthTextureMS = TextureMS(nbSample, GL_DEPTH_COMPONENT24, width, height)
        self.DepthColorTextureMS = TextureMS(nbSample, GL_RGBA8, width, height)
        self.SSAOTextureMS = TextureMS(nbSample, GL_RGBA8, width, height)
        self.LightTextureMS = TextureMS(nbSample, GL_RGBA8, width, height)
        self.IDTextureMS = TextureMS(nbSample, GL_RGBA8, width, height)
        self.NoiseTextureMS = TextureMS(nbSample, GL_RGBA8, width, height)

        # --------------------------------------------------------------------------------------------------------------------
        # Basic Texture Management
        # --------------------------------------------------------------------------------------------------------------------

        self.DiffuseTexture     = Texture(GL_RGBA8, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.NormalTexture      = Texture(GL_RGBA8, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.DepthTexture       = Texture(GL_DEPTH_COMPONENT24, width, height, GL_DEPTH_COMPONENT, GL_FLOAT)
        self.DepthTexture2      = Texture(GL_DEPTH_COMPONENT24, width, height, GL_DEPTH_COMPONENT, GL_FLOAT)
        self.DepthColorTexture  = Texture(GL_RGBA8, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
        
        self.SSAOTexture        = Texture(GL_RGBA8, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.HorizontalBlurTexture       = Texture(GL_RGBA8, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.VerticalBlurTexture       = Texture(GL_RGBA8, width, height, GL_RGBA, GL_UNSIGNED_BYTE)

        self.RotationTexture    = Texture(GL_RGBA, self.SSAO_NoiseLevel, self.SSAO_NoiseLevel, GL_RGBA, GL_FLOAT, UF.generateNoiseTexture(self.SSAO_NoiseLevel))
        self.LightTexture       = Texture(GL_RGBA, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.IDTexture          = Texture(GL_RGBA, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
        self.NoiseTexture       = Texture(GL_RGBA, width, height, GL_RGBA, GL_UNSIGNED_BYTE)


        ssaoRandomTextureData = pygame.image.load(os.path.join("C:/Users/Bastien/Documents/work/cfe_gpuRender/randomTexture.jpg"))
        ix, iy = ssaoRandomTextureData.get_rect().size
        self.RandomTexture    = Texture(GL_RGBA, ix, iy, GL_RGBA, GL_UNSIGNED_BYTE, pygame.image.tostring(ssaoRandomTextureData, 'RGBA', 1))

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
####################################################################################################################################################

    def loadOBJ(self, objFilename):

        obj = OBJ(objFilename)

        if(obj == None):
            print('Problem when loading %s. End of program' % objFilename)
            self.running = False

        return obj

####################################################################################################################################################
####################################################################################################################################################

    def computeShaders(self):

        pathToShaders = "C:/Users/Bastien/Documents/work/cfe_gpuRender/shaders/"

        self.diffuseProgram = GLProgram(pathToShaders + "diffuseVS.glsl", pathToShaders + "diffuseFS.glsl")
        self.normalProgram = GLProgram(pathToShaders + "normalVS.glsl", pathToShaders + "normalFS.glsl")
        self.phongProgram = GLProgram(pathToShaders + "phongVS.glsl", pathToShaders + "phongFS.glsl")
        self.depthProgram = GLProgram(pathToShaders + "depthVS.glsl", pathToShaders + "depthFS.glsl")
        self.idProgram = GLProgram(pathToShaders + "idVS.glsl", pathToShaders + "idFS.glsl")
        self.ssaoProgram = GLProgram(pathToShaders + "ssaoVS.glsl", pathToShaders + "ssaoFS.glsl")
        self.verticalBlurProgram = GLProgram(pathToShaders + "blurVS.glsl", pathToShaders + "verticalBlurFS.glsl")
        self.horizontalBlurProgram = GLProgram(pathToShaders + "blurVS.glsl", pathToShaders + "horizontalBlurFS.glsl")
        self.noiseProgram = GLProgram(pathToShaders + "perlinnoiseVS.glsl", pathToShaders + "perlinnoiseFS.glsl")
        self.dirlightProgram = GLProgram(pathToShaders + "lightVS.glsl", pathToShaders + "dirlightFS.glsl")
        self.ambientlightProgram = GLProgram(pathToShaders + "lightVS.glsl", pathToShaders + "ambientlightFS.glsl")
        self.alphaProgram = GLProgram(pathToShaders + "alphaVS.glsl", pathToShaders + "alphaFS.glsl")     

        GLTools.checkGLErrors()

####################################################################################################################################################
####################################################################################################################################################

    def renderFrame(self, passName):

        # --------------------------------------------------------------------------------------------------------------------
        # Update the camera parameters, Projection and Lookat matrix
        # --------------------------------------------------------------------------------------------------------------------

        fov = 45.0
        aspect = 1.77
        znear = 0.1
        zfar = 1000.0

        ProjectionMatrix = UF.getPerspectiveMatrix(fov, aspect, znear, zfar)
        ProjectionMatrixInverse = LA.inv(ProjectionMatrix)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(fov, aspect, znear, zfar)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0, 15, -15,
            0, 0, 0,
            0, 1, 0) 
        
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

        elif (passName == "AmbientOcclusionPass"):

            self.renderSSAO()

        elif(passName == "NoisePass"):

            self.renderDisplace()


        pygame.display.flip()

        GLTools.checkGLErrors()
        
####################################################################################################################################################
####################################################################################################################################################

    def renderscene(self):

        glCallList(self.obj.gl_list)

####################################################################################################################################################
####################################################################################################################################################

    def handleEvents(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                exit()

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
                if event.key == pygame.K_6:
                    self.displayedPass = "AmbientOcclusionPass"
                if event.key == pygame.K_7:
                    self.displayedPass = "NoisePass"

                if event.key == pygame.K_p:
                    self.SSAO_Power += 1
                if event.key == pygame.K_o:
                    self.SSAO_Power = max(1, self.SSAO_Power-1)

                if event.key == pygame.K_s:
                    self.SSAO_NumSamples += 10
                if event.key == pygame.K_a:

                    self.SSAO_NumSamples = max(10, self.SSAO_NumSamples-10)

                if event.key == pygame.K_r:
                    self.SSAO_Radius += 0.1
                if event.key == pygame.K_e:
                    self.SSAO_Radius = max(0.1, self.SSAO_Radius-0.1)

                if event.key == pygame.K_h:
                    self.SSAO_DistValue += 1
                if event.key == pygame.K_g:
                    self.SSAO_DistValue = max(1, self.SSAO_DistValue-1)    


####################################################################################################################################################
####################################################################################################################################################
     
    def gameLoop(self):

        self.clock = pygame.time.Clock()

        while self.running == True:

            self.clock.tick(30)

            self.handleEvents()

            # VIEW MODE

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
        glViewport(0, 0, width, height)
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
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST)
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_DEPTH_BUFFER_BIT, GL_NEAREST)

        # Draw

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBO)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_BACK)            
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

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
        glViewport(0, 0, width, height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Render

        glUseProgram(self.normalProgram.id)            
        self.renderscene()

        # Blit

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBOMultisampled)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.FBO)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_COLOR_ATTACHMENT0)            
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

        # Draw

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBO)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_BACK)            
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

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

        glViewport(0, 0, width, height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_ONE, GL_ONE)

        # Render

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.NormalTexture.id)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.DepthTexture.id)

        # for lightType in self.lights:

        #     if (lightType == "directionalLight"):

        #         glUseProgram(self.dirlightProgram.id)

        #         # Send parameters common to all the lights
        #         glUniform1i(glGetUniformLocation(self.dirlightProgram.id, "Normal"), 0)

        #         # Send specifics parameters for each light
        #         for dlight in self.lights[lightType]:

        #             if(dlight['name'].__contains__("light_direct_shade")):

        #                 dlightDirection = dlight['direction']
        #                 dlightColor = dlight['rgb']
        #                 dlightIntensity = dlight['brightness']

        #                 loc = glGetUniformLocation(self.dirlightProgram.id, "LightDirection")
        #                 glUniform3f(loc, dlightDirection[0], dlightDirection[1], dlightDirection[2])

        #                 loc = glGetUniformLocation(self.dirlightProgram.id, "LightIntensity")
        #                 glUniform1f(loc, dlightIntensity)

        #                 glBegin(GL_QUADS)
        #                 glVertex2f(0.0, 0.0)
        #                 glVertex2f(1.0, 0.0)
        #                 glVertex2f(1.0, 1.0)
        #                 glVertex2f(0.0, 1.0)
        #                 glEnd()
        
        # Blit

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBOMultisampled)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.FBO)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_COLOR_ATTACHMENT0)            
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

        # Draw

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBO)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_BACK)            
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

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
        glViewport(0, 0, width, height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Render

        glUseProgram(self.depthProgram.id)
        self.renderscene()

        # Blit

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBOMultisampled)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.FBO)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_COLOR_ATTACHMENT0)            
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

        # Draw

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBO)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_BACK)            
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

    def renderSSAO(self):

        # --------------------------------------------------------------------------------------------------------------------
        # Render the SSAO texture using Normal and Depth
        # --------------------------------------------------------------------------------------------------------------------

        # Specify buffers attachements

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.SSAOTexture.id, 0)

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBOMultisampled)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.SSAOTextureMS.id, 0)
        glDrawBuffer(GL_COLOR_ATTACHMENT0)

        # Clean

        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Render

        glUseProgram(self.ssaoProgram.id)

        glUniform1i(glGetUniformLocation(self.ssaoProgram.id, "uNormalTexture"), 0)
        glUniform1i(glGetUniformLocation(self.ssaoProgram.id, "uDepthTexture"), 1)
        glUniform1i(glGetUniformLocation(self.ssaoProgram.id, "uRandomTexture"), 2)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.NormalTexture.id)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.DepthTexture.id)
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self.RandomTexture.id)

        ProjectionMatrix = UF.getProjectionMatrix(self.SSAO_FOV)
        ProjectionBiasMatrixInverse = LA.inv(ProjectionMatrix) 
        glUniformMatrix4fv(glGetUniformLocation(self.ssaoProgram.id, "uInverseProjection"), 1, GL_TRUE, ProjectionBiasMatrixInverse.astype(np.float32))
        glUniformMatrix4fv(glGetUniformLocation(self.ssaoProgram.id, "uProjection"), 1, GL_TRUE, ProjectionMatrix.astype(np.float32))

        glUniform3fv(glGetUniformLocation(self.ssaoProgram.id, "SSAO_Samples"), self.SSAO_NumSamples, UF.genSSAOSamples(self.SSAO_Radius, self.SSAO_NumSamples))    
        glUniform1f(glGetUniformLocation(self.ssaoProgram.id, "SSAO_Power"), self.SSAO_Power)
        glUniform1f(glGetUniformLocation(self.ssaoProgram.id, "SSAO_Dist"), self.SSAO_DistValue)
        glUniform1f(glGetUniformLocation(self.ssaoProgram.id, "SSAO_Radius"), self.SSAO_Radius)
        glUniform1i(glGetUniformLocation(self.ssaoProgram.id, "SSAO_SampleCount"), self.SSAO_NumSamples)
        
        glUniform2f(glGetUniformLocation(self.ssaoProgram.id, "sxy"), width/3.0, height/3.0)
        

        glBegin(GL_QUADS)
        glVertex2f(0.0, 0.0)
        glVertex2f(1.0, 0.0)
        glVertex2f(1.0, 1.0)
        glVertex2f(0.0, 1.0)
        glEnd()
        
        # Blit

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBOMultisampled)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.FBO)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_COLOR_ATTACHMENT0)            
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

        glBindTexture(GL_TEXTURE_2D, 0)
        glUseProgram(0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        # --------------------------------------------------------------------------------------------------------------------
        # Horizontal Blur
        # --------------------------------------------------------------------------------------------------------------------

        # glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        # glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.HorizontalBlurTexture.id, 0)

        # glUseProgram(self.horizontalBlurProgram.id)
        # glUniform1i(glGetUniformLocation(self.horizontalBlurProgram.id, "Texture"), 0)
        # glUniform1f(glGetUniformLocation(self.horizontalBlurProgram.id, "sx"), 1 / float(width))

        # glActiveTexture(GL_TEXTURE0)
        # glBindTexture(GL_TEXTURE_2D, self.SSAOTexture.id)

        # glDisable(GL_DEPTH_TEST)
        # glClear(GL_COLOR_BUFFER_BIT)

        # glBegin(GL_QUADS)
        # glVertex2f(0.0, 0.0)
        # glVertex2f(1.0, 0.0)
        # glVertex2f(1.0, 1.0)
        # glVertex2f(0.0, 1.0)
        # glEnd()


        # --------------------------------------------------------------------------------------------------------------------
        # Vertical Blur
        # --------------------------------------------------------------------------------------------------------------------

        # glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        # glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.VerticalBlurTexture.id, 0)

        # glUseProgram(self.verticalBlurProgram.id)
        # glUniform1i(glGetUniformLocation(self.verticalBlurProgram.id, "Texture"), 0)
        # glUniform1f(glGetUniformLocation(self.verticalBlurProgram.id, "sy"), 1 / float(height))

        # glActiveTexture(GL_TEXTURE0)
        # glBindTexture(GL_TEXTURE_2D, self.HorizontalBlurTexture.id)

        # glClear(GL_COLOR_BUFFER_BIT)

        # glBegin(GL_QUADS)
        # glVertex2f(0.0, 0.0)
        # glVertex2f(1.0, 0.0)
        # glVertex2f(1.0, 1.0)
        # glVertex2f(0.0, 1.0)
        # glEnd()

        # Draw

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBO)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_BACK)            
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

    def renderDisplace(self):

        # Specify buffers attachementsC:\Users\Bastien\Documents\work\WinterIsComing\assets\bedroom

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.NoiseTexture.id, 0)
        GLTools.checkFBO()

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBOMultisampled)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.NoiseTextureMS.id, 0)
        glDrawBuffer(GL_COLOR_ATTACHMENT0)
        GLTools.checkFBO()
        
        # Clean

        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Render

        glUseProgram(self.noiseProgram.id)
        glBegin(GL_QUADS)
        glVertex2f(0.0, 0.0)
        glVertex2f(1.0, 0.0)
        glVertex2f(1.0, 1.0)
        glVertex2f(0.0, 1.0)
        glEnd()

        # Blit

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBOMultisampled)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.FBO)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_COLOR_ATTACHMENT0)            
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

        # Draw

        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.FBO)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glReadBuffer(GL_COLOR_ATTACHMENT0)            
        glDrawBuffer(GL_BACK)            
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

####################################################################################################################################################
####################################################################################################################################################

scene = Scene()