from OpenGL import GL


class GLSLProgram:
    def __init__(self, vertexShaderFile, fragmentShaderFile):

        self.id = GL.glCreateProgram()
        vs = 0
        fs = 0

        # Load Vertex Shader
        try:
            with open(vertexShaderFile, "r") as f:
                vs = self.create_and_compile_shader(GL.GL_VERTEX_SHADER, f.read())
            GL.glAttachShader(self.id, vs)
        except IOError as e:
            print("Fail to load %s" % vertexShaderFile)
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
            return

        # Load Fragment Shader
        try:
            with open(fragmentShaderFile, "r") as f:
                fs = self.create_and_compile_shader(GL.GL_FRAGMENT_SHADER, f.read())
            GL.glAttachShader(self.id, fs)
        except IOError as e:
            print("Fail to load %s" % str(fragmentShaderFile))
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
            return

        GL.glLinkProgram(self.id)
        GL.glDeleteShader(vs)
        GL.glDeleteShader(fs)

        # Check for program error
        status = GL.glGetProgramiv(self.id, GL.GL_LINK_STATUS)
        if GL.glGetProgramiv(self.id, GL.GL_INFO_LOG_LENGTH) > 1:
            print("Error in linking shaders (status = %s) : %s" % (str(status), GL.glGetProgramInfoLog(self.id)))
            return

        print("Shaders successfully loaded")

    def create_and_compile_shader(self, shaderType, source):

        shader = GL.glCreateShader(shaderType)
        GL.glShaderSource(shader, source)
        GL.glCompileShader(shader)

        # Check for shader error
        status = GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS)
        loglength = GL.glGetShaderiv(shader, GL.GL_INFO_LOG_LENGTH)
        if loglength > 1:
            print(
                "Error in compiling %s (Status = %s): %s"
                % (str(shaderType), str(status), GL.glGetShaderInfoLog(shader))
            )
            return

        return shader
