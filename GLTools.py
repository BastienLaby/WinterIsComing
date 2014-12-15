from OpenGL.GL import *

def checkFBO():

    status = glCheckFramebufferStatus(GL_FRAMEBUFFER)

    if(status == GL_FRAMEBUFFER_UNDEFINED):
        print('GL_FRAMEBUFFER_UNDEFINED')
    elif(status == GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT):
        print('GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT')
    elif(status == GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT):
        print('GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT')
    elif(status == GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER):
        print('GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER')
    elif(status == GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER):
        print('GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER')
    elif(status == GL_FRAMEBUFFER_UNSUPPORTED):
        print('GL_FRAMEBUFFER_UNSUPPORTED')
    elif(status == GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE):
        print('GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE')
    elif(status == GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS):
        print('GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS')
    elif(status == 0):
        print('An error occurs')

def checkGLErrors():
    if(glGetError() != GL_NO_ERROR):
        print('Error OpenGL : ' + str(glGetError()))