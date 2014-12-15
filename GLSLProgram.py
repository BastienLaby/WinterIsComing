from OpenGL.GL import *

class GLSLProgram():

    def __init__(self, vertexShaderFile, fragmentShaderFile):

        self.id = glCreateProgram()
        vs = 0
        fs = 0

        # Load Vertex Shader
        try:
            f = open(vertexShaderFile, 'r')
            vs = self.createAndCompileShader(GL_VERTEX_SHADER, f.read())
            glAttachShader(self.id, vs)
        except IOError as e:
            print('Fail to load ' + str(vertexShaderFile))
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
            return

        # Load Fragment Shader
        try:
            f = open(fragmentShaderFile, 'r')
            fs = self.createAndCompileShader(GL_FRAGMENT_SHADER, f.read())
            glAttachShader(self.id, fs)
        except IOError as e:
            print('Fail to load ' + str(vertexShaderFile))
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
            return

        glLinkProgram(self.id)
        glDeleteShader(vs)
        glDeleteShader(fs)

        # Check for program error
        status = glGetProgramiv(self.id, GL_LINK_STATUS)
        loglength = glGetProgramiv(self.id, GL_INFO_LOG_LENGTH)
        if(loglength > 1):
            print("Error in linking shaders (status = %s) : %s" % (str(status), glGetProgramInfoLog(self.id)))
            return

    def createAndCompileShader(self, shaderType, source):
        
        shader = glCreateShader(shaderType)
        glShaderSource(shader, source)
        glCompileShader(shader)

        # Check for shader error
        status = glGetShaderiv(shader, GL_COMPILE_STATUS)
        loglength = glGetShaderiv(shader, GL_INFO_LOG_LENGTH)
        if(loglength > 1):
            print("Error in compiling %s (Status = %s): %s" % (str(shaderType), str(status), glGetShaderInfoLog(shader)))
            return

        return shader