from OpenGL import GL


class Texture:
    def __init__(
        self, internalFormat, width, height, pixelDataFormat, pixelDataType, data=None
    ):
        self.id = GL.glGenTextures(1)
        self.lod = 0
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.id)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            self.lod,
            internalFormat,
            width,
            height,
            0,
            pixelDataFormat,
            pixelDataType,
            data,
        )
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)


class TextureMS:
    def __init__(self, nbSample, internalFormat, width, height):
        self.id = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D_MULTISAMPLE, self.id)
        GL.glTexImage2DMultisample(
            GL.GL_TEXTURE_2D_MULTISAMPLE,
            nbSample,
            internalFormat,
            width,
            height,
            GL.GL_FALSE,
        )
        GL.glBindTexture(GL.GL_TEXTURE_2D_MULTISAMPLE, 0)
