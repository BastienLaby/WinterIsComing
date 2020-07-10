from OpenGL import GL, GLU
import numpy as np
import numpy.linalg as npla
import pygame

from gl.glsl_program import GLSLProgram
from gl.texture import Texture, TextureMS
from gl.mesh import Mesh
from gl.check import glCheckError, glCheckFbo
from gl.tools import draw_quad
from utils import matrix
from snow_engine import SnowEngine


class Viewport:
    def __init__(self):

        screen = pygame.display.set_mode(
            (1920, 1200),
            pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE | pygame.FULLSCREEN,
        )
        self.width, self.height = screen.get_size()

        pygame.init()

        print("OpenGL Informations : ")
        print("Vendor : %s" % GL.glGetString(GL.GL_VENDOR))
        print("Renderer : %s" % GL.glGetString(GL.GL_RENDERER))
        print("Version : %s" % GL.glGetString(GL.GL_VERSION))
        print("GLSL : %s" % GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION))

        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        pygame.display.flip()

        self.clock = pygame.time.Clock()
        self.key = pygame.key.get_pressed()
        pygame.key.set_repeat(3, 40)

        self.camera = {}
        self.camera["up"] = [0, 1, 0]
        self.camera["eye"] = [-13, 7, -10]
        self.camera["target"] = [0, 0, -10]

        self.computeShaders()

        self.obj = Mesh()
        self.obj.loadFromObj("assets/bedroom/bedroom.obj")
        self.obj.generateGLLists()

        self.loadTextures()
        self.loadFbos()

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

        self.se = SnowEngine()
        self.se.setSize([100, 40])
        self.se.setRate(4)
        self.se.setHeight(25)

        pygame.mixer.music.load("music/we-three-kings.mp3")
        pygame.mixer.music.play(loops=-1)

    def loadTextures(self):

        nbSample = 8
        self.texs = {}

        self.texs["depth_ms"] = TextureMS(
            nbSample, GL.GL_DEPTH_COMPONENT24, self.width, self.height
        )
        self.texs["color_ms"] = TextureMS(
            nbSample, GL.GL_RGBA8, self.width, self.height
        )
        self.texs["illum_ms"] = TextureMS(
            nbSample, GL.GL_RGBA8, self.width, self.height
        )
        self.texs["id_ms"] = TextureMS(nbSample, GL.GL_RGBA8, self.width, self.height)
        self.texs["normal_ms"] = TextureMS(
            nbSample, GL.GL_RGBA8, self.width, self.height
        )

        self.texs["depth"] = Texture(
            GL.GL_DEPTH_COMPONENT24,
            self.width,
            self.height,
            GL.GL_DEPTH_COMPONENT,
            GL.GL_FLOAT,
        )
        self.texs["depthblit"] = Texture(
            GL.GL_DEPTH_COMPONENT24,
            self.width,
            self.height,
            GL.GL_DEPTH_COMPONENT,
            GL.GL_FLOAT,
        )
        self.texs["depthblit2"] = Texture(
            GL.GL_DEPTH_COMPONENT24,
            self.width,
            self.height,
            GL.GL_DEPTH_COMPONENT,
            GL.GL_FLOAT,
        )
        self.texs["color"] = Texture(
            GL.GL_RGBA8, self.width, self.height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE
        )
        self.texs["illum"] = Texture(
            GL.GL_RGBA8, self.width, self.height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE
        )
        self.texs["id"] = Texture(
            GL.GL_RGBA8, self.width, self.height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE
        )
        self.texs["normal"] = Texture(
            GL.GL_RGBA8, self.width, self.height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE
        )
        self.texs["compo"] = Texture(
            GL.GL_RGBA8, self.width, self.height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE
        )
        self.texs["dof"] = Texture(
            GL.GL_RGBA8, self.width, self.height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE
        )

    def loadFbos(self):

        self.fboPrepassMS = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fboPrepassMS)
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT0,
            GL.GL_TEXTURE_2D_MULTISAMPLE,
            self.texs["color_ms"].id,
            0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT1,
            GL.GL_TEXTURE_2D_MULTISAMPLE,
            self.texs["illum_ms"].id,
            0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT2,
            GL.GL_TEXTURE_2D_MULTISAMPLE,
            self.texs["id_ms"].id,
            0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT3,
            GL.GL_TEXTURE_2D_MULTISAMPLE,
            self.texs["normal_ms"].id,
            0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_DEPTH_ATTACHMENT,
            GL.GL_TEXTURE_2D_MULTISAMPLE,
            self.texs["depth_ms"].id,
            0,
        )
        glCheckFbo()

        self.fboPrepass = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fboPrepass)
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT0,
            GL.GL_TEXTURE_2D,
            self.texs["color"].id,
            0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT1,
            GL.GL_TEXTURE_2D,
            self.texs["illum"].id,
            0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT2,
            GL.GL_TEXTURE_2D,
            self.texs["id"].id,
            0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT3,
            GL.GL_TEXTURE_2D,
            self.texs["normal"].id,
            0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_DEPTH_ATTACHMENT,
            GL.GL_TEXTURE_2D,
            self.texs["depth"].id,
            0,
        )
        glCheckFbo()

        self.fboCompo = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fboCompo)
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT0,
            GL.GL_TEXTURE_2D,
            self.texs["compo"].id,
            0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_DEPTH_ATTACHMENT,
            GL.GL_TEXTURE_2D,
            self.texs["depthblit"].id,
            0,
        )
        glCheckFbo()

        self.fboDof = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fboDof)
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT0,
            GL.GL_TEXTURE_2D,
            self.texs["dof"].id,
            0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_DEPTH_ATTACHMENT,
            GL.GL_TEXTURE_2D,
            self.texs["depthblit"].id,
            0,
        )
        glCheckFbo()

    def computeShaders(self):
        pathToShaders = "shaders/"
        self.programs = {}
        self.programs["prepass"] = GLSLProgram(
            pathToShaders + "prepass.vs", pathToShaders + "prepass.fs"
        )
        self.programs["blit"] = GLSLProgram(
            pathToShaders + "blit.vs", pathToShaders + "blit.fs"
        )
        self.programs["compo"] = GLSLProgram(
            pathToShaders + "compo.vs", pathToShaders + "compo.fs"
        )
        self.programs["dof"] = GLSLProgram(
            pathToShaders + "dof.vs", pathToShaders + "dof.fs"
        )
        glCheckError()

    def handleEvents(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                exit()

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.dict["size"]
                self.loadTextures()
                self.loadFbos()

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_SPACE:
                    self.computeShaders()

            elif event.type == pygame.MOUSEMOTION:
                dx = event.pos[0] - self.width / 2
                dy = event.pos[1] - self.height / 2
                self.camera["target"] = [0, -dy * 0.01, -10 + dx * 0.01]

    def startRendering(self):

        self.running = True
        while self.running:

            self.clock.tick(30)
            self.handleEvents()

            self.fov = 60
            self.aspect = float(self.width) / float(self.height)
            self.znear = 0.01
            self.zfar = 1000.0

            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            GLU.gluPerspective(self.fov, self.aspect, self.znear, self.zfar)

            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            GLU.gluLookAt(
                self.camera["eye"][0],
                self.camera["eye"][1],
                self.camera["eye"][2],
                self.camera["target"][0],
                self.camera["target"][1],
                self.camera["target"][2],
                self.camera["up"][0],
                self.camera["up"][1],
                self.camera["up"][2],
            )

            self.se.generateParticle()

            self.render()
            self.renderCompo()
            self.renderDof()

            self.se.updateParticles()

            pygame.display.flip()

    def render(self):

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fboPrepassMS)
        GL.glDrawBuffers(
            4,
            (
                GL.GL_COLOR_ATTACHMENT0,
                GL.GL_COLOR_ATTACHMENT1,
                GL.GL_COLOR_ATTACHMENT2,
                GL.GL_COLOR_ATTACHMENT3,
            ),
        )

        GL.glViewport(0, 0, self.width, self.height)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        GL.glUseProgram(self.programs["prepass"].id)
        textureLocation = GL.glGetUniformLocation(
            self.programs["prepass"].id, "uColorTexture"
        )
        cameraPositionLocation = GL.glGetUniformLocation(
            self.programs["prepass"].id, "uCameraPosition"
        )
        isSnowLocation = GL.glGetUniformLocation(self.programs["prepass"].id, "uIsSnow")

        GL.glUniform1i(textureLocation, 0)
        GL.glUniform3f(
            cameraPositionLocation,
            self.camera["eye"][0],
            self.camera["eye"][1],
            self.camera["eye"][2],
        )

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glUniform1i(isSnowLocation, 0)
        self.obj.draw()
        GL.glUniform1i(isSnowLocation, 1)
        self.se.drawSnow()

        # Transfer from Multisampled FBO to classic FBO

        self.transferTexture(
            self.fboPrepassMS,
            self.fboPrepass,
            GL.GL_COLOR_ATTACHMENT0,
            GL.GL_COLOR_ATTACHMENT0,
            colorTexture=True,
        )
        self.transferTexture(
            self.fboPrepassMS,
            self.fboPrepass,
            GL.GL_COLOR_ATTACHMENT1,
            GL.GL_COLOR_ATTACHMENT1,
            colorTexture=True,
        )
        self.transferTexture(
            self.fboPrepassMS,
            self.fboPrepass,
            GL.GL_COLOR_ATTACHMENT2,
            GL.GL_COLOR_ATTACHMENT2,
            colorTexture=True,
        )
        self.transferTexture(
            self.fboPrepassMS,
            self.fboPrepass,
            GL.GL_COLOR_ATTACHMENT3,
            GL.GL_COLOR_ATTACHMENT3,
            colorTexture=True,
        )
        self.transferTexture(
            self.fboPrepassMS, self.fboPrepass, None, None, colorTexture=False
        )

        # Blit the result

        self.blitToScreen(0, 0, self.width, self.height, self.texs["color"].id)
        self.blitToScreen(0, 0, self.width / 4, self.height / 4, self.texs["illum"].id)
        self.blitToScreen(
            self.width / 4, 0, self.width / 4, self.height / 4, self.texs["id"].id
        )
        self.blitToScreen(
            2 * self.width / 4,
            0,
            self.width / 4,
            self.height / 4,
            self.texs["normal"].id,
        )

    def renderCompo(self):

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fboCompo)
        GL.glDrawBuffers(1, (GL.GL_COLOR_ATTACHMENT0))
        GL.glViewport(0, 0, self.width, self.height)
        GL.glClearColor(1.0, 1.0, 1.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glDisable(GL.GL_DEPTH_TEST)

        GL.glUseProgram(self.programs["compo"].id)

        GL.glUniform1i(
            GL.glGetUniformLocation(self.programs["compo"].id, "uColorTexture"), 0
        )
        GL.glUniform1i(
            GL.glGetUniformLocation(self.programs["compo"].id, "uIllumTexture"), 1
        )
        GL.glUniform1i(
            GL.glGetUniformLocation(self.programs["compo"].id, "uIDTexture"), 2
        )

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texs["color"].id)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texs["illum"].id)
        GL.glActiveTexture(GL.GL_TEXTURE2)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texs["id"].id)

        GL.glUniform2f(
            GL.glGetUniformLocation(self.programs["compo"].id, "uScreenResolution"),
            self.width,
            self.height,
        )

        draw_quad()

        self.blitToScreen(0, 0, self.width, self.height, self.texs["compo"].id)

    def renderDof(self):

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fboDof)
        GL.glDrawBuffers(1, (GL.GL_COLOR_ATTACHMENT0))
        GL.glViewport(0, 0, self.width, self.height)
        GL.glClearColor(1.0, 1.0, 1.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glDisable(GL.GL_DEPTH_TEST)

        GL.glUseProgram(self.programs["dof"].id)

        GL.glUniform1i(GL.glGetUniformLocation(self.programs["dof"].id, "uTexture"), 0)
        GL.glUniform1i(
            GL.glGetUniformLocation(self.programs["dof"].id, "uDepthTexture"), 1
        )
        proj = matrix.create_perspective_matrix(
            self.fov, self.aspect, self.znear, self.zfar
        )
        invProj = npla.inv(proj)
        GL.glUniformMatrix4fv(
            GL.glGetUniformLocation(
                self.programs["dof"].id, "uInverseProjectionMatrix"
            ),
            1,
            GL.GL_TRUE,
            invProj.astype(np.float32),
        )

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texs["compo"].id)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texs["depth"].id)

        GL.glUniform2i(
            GL.glGetUniformLocation(self.programs["dof"].id, "uScreenResolution"),
            self.width,
            self.height,
        )

        draw_quad()

        self.blitToScreen(0, 0, self.width, self.height, self.texs["dof"].id)

    def transferTexture(self, srcFbo, dstFbo, srcBuffer, dstBuffer, colorTexture=True):
        GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, srcFbo)
        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, dstFbo)
        if colorTexture:
            GL.glReadBuffer(srcBuffer)
            GL.glDrawBuffer(dstBuffer)
            GL.glBlitFramebuffer(
                0,
                0,
                self.width,
                self.height,
                0,
                0,
                self.width,
                self.height,
                GL.GL_COLOR_BUFFER_BIT,
                GL.GL_LINEAR,
            )
        else:
            GL.glBlitFramebuffer(
                0,
                0,
                self.width,
                self.height,
                0,
                0,
                self.width,
                self.height,
                GL.GL_DEPTH_BUFFER_BIT,
                GL.GL_NEAREST,
            )

    def blitToScreen(self, xPos, yPos, width, height, textureID):
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        GL.glViewport(int(xPos), int(yPos), int(width), int(height))
        GL.glUseProgram(self.programs["blit"].id)
        u = GL.glGetUniformLocation(self.programs["blit"].id, "uTexture")
        GL.glUniform1i(u, 0)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, textureID)
        GL.glDisable(GL.GL_DEPTH_TEST)
        draw_quad()
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glUseProgram(0)


viewport = Viewport()
viewport.startRendering()
