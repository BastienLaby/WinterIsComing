from OpenGL import GL


def draw_quad():
    GL.glBegin(GL.GL_QUADS)
    GL.glVertex2f(0.0, 0.0)
    GL.glVertex2f(1.0, 0.0)
    GL.glVertex2f(1.0, 1.0)
    GL.glVertex2f(0.0, 1.0)
    GL.glEnd()
