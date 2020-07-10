import os

from OpenGL import GL, GLU
import numpy as np
import numpy.linalg as npla
import pygame

from gl.glsl_program import GLSLProgram
from gl.texture import Texture, TextureMS
from gl.mesh import Mesh
from gl.check import gl_check_error, gl_check_fbo
from gl.tools import draw_quad
from utils import matrix
from snow_engine import SnowEngine


class Viewport:
    def __init__(self):

        screen = pygame.display.set_mode(
            (1920, 1200), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE | pygame.FULLSCREEN,
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

        self.compute_shaders()

        self.obj = Mesh()
        self.obj.load_from_obj("assets/bedroom/bedroom.obj")
        self.obj.generate_gl_lists()

        self.load_textures()
        self.load_fbos()

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

        self.snow_engine = SnowEngine()

        pygame.mixer.music.load("music/we-three-kings.mp3")
        pygame.mixer.music.play(loops=-1)

    def load_textures(self):
        sample_count = 8
        self.texs = {
            "depth_ms": TextureMS(sample_count, GL.GL_DEPTH_COMPONENT24, self.width, self.height),
            "color_ms": TextureMS(sample_count, GL.GL_RGBA8, self.width, self.height),
            "illum_ms": TextureMS(sample_count, GL.GL_RGBA8, self.width, self.height),
            "id_ms": TextureMS(sample_count, GL.GL_RGBA8, self.width, self.height),
            "normal_ms": TextureMS(sample_count, GL.GL_RGBA8, self.width, self.height),
            "depth": Texture(GL.GL_DEPTH_COMPONENT24, self.width, self.height, GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT),
            "depthblit": Texture(GL.GL_DEPTH_COMPONENT24, self.width, self.height, GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT),
            "depthblit2": Texture(GL.GL_DEPTH_COMPONENT24, self.width, self.height, GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT),
            "color": Texture(GL.GL_RGBA8, self.width, self.height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE),
            "illum": Texture(GL.GL_RGBA8, self.width, self.height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE),
            "id": Texture(GL.GL_RGBA8, self.width, self.height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE),
            "normal": Texture(GL.GL_RGBA8, self.width, self.height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE),
            "compo": Texture(GL.GL_RGBA8, self.width, self.height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE),
            "dof": Texture(GL.GL_RGBA8, self.width, self.height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE),
        }

    def load_fbos(self):

        self.fbo_prepass_ms = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo_prepass_ms)
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D_MULTISAMPLE, self.texs["color_ms"].id, 0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT1, GL.GL_TEXTURE_2D_MULTISAMPLE, self.texs["illum_ms"].id, 0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT2, GL.GL_TEXTURE_2D_MULTISAMPLE, self.texs["id_ms"].id, 0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT3, GL.GL_TEXTURE_2D_MULTISAMPLE, self.texs["normal_ms"].id, 0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_TEXTURE_2D_MULTISAMPLE, self.texs["depth_ms"].id, 0,
        )
        gl_check_fbo()

        self.fbo_prepass = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo_prepass)
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, self.texs["color"].id, 0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT1, GL.GL_TEXTURE_2D, self.texs["illum"].id, 0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT2, GL.GL_TEXTURE_2D, self.texs["id"].id, 0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT3, GL.GL_TEXTURE_2D, self.texs["normal"].id, 0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_TEXTURE_2D, self.texs["depth"].id, 0,
        )
        gl_check_fbo()

        self.fbo_compo = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo_compo)
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, self.texs["compo"].id, 0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_TEXTURE_2D, self.texs["depthblit"].id, 0,
        )
        gl_check_fbo()

        self.fbo_dof = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo_dof)
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, self.texs["dof"].id, 0,
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_TEXTURE_2D, self.texs["depthblit"].id, 0,
        )
        gl_check_fbo()

    def compute_shaders(self):
        pathToShaders = "shaders"
        self.programs = {}
        self.programs["prepass"] = GLSLProgram(
            os.path.join(pathToShaders, "prepass.vs"), os.path.join(pathToShaders, "prepass.fs")
        )
        self.programs["blit"] = GLSLProgram(
            os.path.join(pathToShaders, "blit.vs"), os.path.join(pathToShaders, "blit.fs")
        )
        self.programs["compo"] = GLSLProgram(
            os.path.join(pathToShaders, "compo.vs"), os.path.join(pathToShaders, "compo.fs")
        )
        self.programs["dof"] = GLSLProgram(os.path.join(pathToShaders, "dof.vs"), os.path.join(pathToShaders, "dof.fs"))
        gl_check_error()

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                exit()

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.dict["size"]
                self.load_textures()
                self.load_fbos()

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_SPACE:
                    self.compute_shaders()

            elif event.type == pygame.MOUSEMOTION:
                dx = event.pos[0] - self.width / 2
                dy = event.pos[1] - self.height / 2
                self.camera["target"] = [0, -dy * 0.01, -10 + dx * 0.01]

    def start_loop(self):

        self.running = True
        while self.running:

            self.clock.tick(30)
            self.handle_events()

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

            self.snow_engine.generate_particles()

            self.render()
            self.render_compo()
            self.render_dof()

            self.snow_engine.update()

            pygame.display.flip()

    def render(self):

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo_prepass_ms)
        GL.glDrawBuffers(
            4, (GL.GL_COLOR_ATTACHMENT0, GL.GL_COLOR_ATTACHMENT1, GL.GL_COLOR_ATTACHMENT2, GL.GL_COLOR_ATTACHMENT3),
        )

        GL.glViewport(0, 0, self.width, self.height)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        GL.glUseProgram(self.programs["prepass"].id)
        tex_location = GL.glGetUniformLocation(self.programs["prepass"].id, "uColorTexture")
        cam_pos_location = GL.glGetUniformLocation(self.programs["prepass"].id, "uCameraPosition")
        is_snow_location = GL.glGetUniformLocation(self.programs["prepass"].id, "uIsSnow")

        GL.glUniform1i(tex_location, 0)
        GL.glUniform3f(
            cam_pos_location, self.camera["eye"][0], self.camera["eye"][1], self.camera["eye"][2],
        )

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glUniform1i(is_snow_location, 0)
        self.obj.draw()
        GL.glUniform1i(is_snow_location, 1)
        self.snow_engine.draw_snow()

        # Transfer from Multisampled FBO to classic FBO

        self.transfer_texture(
            self.fbo_prepass_ms, self.fbo_prepass, GL.GL_COLOR_ATTACHMENT0, GL.GL_COLOR_ATTACHMENT0, color_texture=True,
        )
        self.transfer_texture(
            self.fbo_prepass_ms, self.fbo_prepass, GL.GL_COLOR_ATTACHMENT1, GL.GL_COLOR_ATTACHMENT1, color_texture=True,
        )
        self.transfer_texture(
            self.fbo_prepass_ms, self.fbo_prepass, GL.GL_COLOR_ATTACHMENT2, GL.GL_COLOR_ATTACHMENT2, color_texture=True,
        )
        self.transfer_texture(
            self.fbo_prepass_ms, self.fbo_prepass, GL.GL_COLOR_ATTACHMENT3, GL.GL_COLOR_ATTACHMENT3, color_texture=True,
        )
        self.transfer_texture(self.fbo_prepass_ms, self.fbo_prepass, None, None, color_texture=False)

        # Blit the result

        self.blit_to_screen(0, 0, self.width, self.height, self.texs["color"].id)
        self.blit_to_screen(0, 0, self.width / 4, self.height / 4, self.texs["illum"].id)
        self.blit_to_screen(self.width / 4, 0, self.width / 4, self.height / 4, self.texs["id"].id)
        self.blit_to_screen(
            2 * self.width / 4, 0, self.width / 4, self.height / 4, self.texs["normal"].id,
        )

    def render_compo(self):

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo_compo)
        GL.glDrawBuffers(1, (GL.GL_COLOR_ATTACHMENT0))
        GL.glViewport(0, 0, self.width, self.height)
        GL.glClearColor(1.0, 1.0, 1.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glDisable(GL.GL_DEPTH_TEST)

        GL.glUseProgram(self.programs["compo"].id)

        GL.glUniform1i(GL.glGetUniformLocation(self.programs["compo"].id, "uColorTexture"), 0)
        GL.glUniform1i(GL.glGetUniformLocation(self.programs["compo"].id, "uIllumTexture"), 1)
        GL.glUniform1i(GL.glGetUniformLocation(self.programs["compo"].id, "uIDTexture"), 2)

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texs["color"].id)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texs["illum"].id)
        GL.glActiveTexture(GL.GL_TEXTURE2)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texs["id"].id)

        GL.glUniform2f(
            GL.glGetUniformLocation(self.programs["compo"].id, "uScreenResolution"), self.width, self.height,
        )

        draw_quad()

        self.blit_to_screen(0, 0, self.width, self.height, self.texs["compo"].id)

    def render_dof(self):

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo_dof)
        GL.glDrawBuffers(1, (GL.GL_COLOR_ATTACHMENT0))
        GL.glViewport(0, 0, self.width, self.height)
        GL.glClearColor(1.0, 1.0, 1.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glDisable(GL.GL_DEPTH_TEST)

        GL.glUseProgram(self.programs["dof"].id)

        GL.glUniform1i(GL.glGetUniformLocation(self.programs["dof"].id, "uTexture"), 0)
        GL.glUniform1i(GL.glGetUniformLocation(self.programs["dof"].id, "uDepthTexture"), 1)
        proj = matrix.create_perspective_matrix(self.fov, self.aspect, self.znear, self.zfar)
        invProj = npla.inv(proj)
        GL.glUniformMatrix4fv(
            GL.glGetUniformLocation(self.programs["dof"].id, "uInverseProjectionMatrix"),
            1,
            GL.GL_TRUE,
            invProj.astype(np.float32),
        )

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texs["compo"].id)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texs["depth"].id)

        GL.glUniform2i(
            GL.glGetUniformLocation(self.programs["dof"].id, "uScreenResolution"), self.width, self.height,
        )

        draw_quad()

        self.blit_to_screen(0, 0, self.width, self.height, self.texs["dof"].id)

    def transfer_texture(self, src_fbo, dst_fbo, src_buffer, dst_buffer, color_texture=True):
        GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, src_fbo)
        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, dst_fbo)
        if color_texture:
            GL.glReadBuffer(src_buffer)
            GL.glDrawBuffer(dst_buffer)
            GL.glBlitFramebuffer(
                0, 0, self.width, self.height, 0, 0, self.width, self.height, GL.GL_COLOR_BUFFER_BIT, GL.GL_LINEAR,
            )
        else:
            GL.glBlitFramebuffer(
                0, 0, self.width, self.height, 0, 0, self.width, self.height, GL.GL_DEPTH_BUFFER_BIT, GL.GL_NEAREST,
            )

    def blit_to_screen(self, xpos, ypos, width, height, tex_id):
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        GL.glViewport(int(xpos), int(ypos), int(width), int(height))
        GL.glUseProgram(self.programs["blit"].id)
        u = GL.glGetUniformLocation(self.programs["blit"].id, "uTexture")
        GL.glUniform1i(u, 0)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex_id)
        GL.glDisable(GL.GL_DEPTH_TEST)
        draw_quad()
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glUseProgram(0)


viewport = Viewport()
viewport.start_loop()
