import os

from OpenGL import GL
import pygame


class Mesh(object):
    def __init__(self):
        self.materials = {}
        self.glList = 0

    def loadFromObj(self, filename):

        f = None
        try:
            f = open(filename, "r")
        except IOError:
            raise Exception("Cannot open %s" % filename)

        self.rootPath = "/".join(filename.split("/")[:-1]) + "/"
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []

        materialName = None

        for line in f:

            if line.startswith("#"):
                continue

            values = line.split()

            if not values:
                continue

            if values[0] == "v":
                self.vertices.append(list(map(float, values[1:4])))

            elif values[0] == "vn":
                self.normals.append(list(map(float, values[1:4])))

            elif values[0] == "vt":
                self.texcoords.append(list(map(float, values[1:3])))

            elif values[0] in ("usemtl", "usemat"):
                materialName = values[1]

            elif values[0] == "mtllib":
                self.loadMaterialFile(values[1])

            elif values[0] == "f":
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split("/")
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, materialName))
        return

    def loadMaterialFile(self, filename):

        f = None
        try:
            f = open(self.rootPath + filename, "r")
        except IOError:
            print(
                "The program cannot load %s.\nEnd of program."
                % str(self.rootPath + filename)
            )
            return None

        currentMTLName = ""

        for line in f:

            if line.startswith("#"):
                continue

            values = line.split()

            if not values:
                continue

            if values[0] == "newmtl":
                currentMTLName = values[1]
                if currentMTLName not in self.materials:
                    self.materials[currentMTLName] = {}
                else:
                    continue

            elif values[0] == "map_Kd":

                if values[1] == "-s":
                    self.scaleX, self.scaleY = values[2], values[3]
                    textureFile = self.rootPath + values[4]
                else:
                    textureFile = self.rootPath + values[1]

                data = pygame.image.load(os.path.join("", textureFile))
                image = pygame.image.tostring(data, "RGBA", 1)
                w, h = data.get_rect().size

                # Generate GL Texture
                self.materials[currentMTLName]["textureID"] = GL.glGenTextures(1)
                GL.glBindTexture(
                    GL.GL_TEXTURE_2D, self.materials[currentMTLName]["textureID"]
                )
                GL.glTexParameteri(
                    GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR
                )
                GL.glTexParameteri(
                    GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
                )
                GL.glTexImage2D(
                    GL.GL_TEXTURE_2D,
                    0,
                    GL.GL_RGBA,
                    w,
                    h,
                    0,
                    GL.GL_RGBA,
                    GL.GL_UNSIGNED_BYTE,
                    image,
                )

            else:
                self.materials[currentMTLName][values[0]] = list(map(float, values[1:]))

    def generateGLLists(self):

        GL.glDeleteLists(self.glList, 1)
        self.glList = GL.glGenLists(1)
        GL.glNewList(self.glList, GL.GL_COMPILE)

        for face in self.faces:
            vertices, normals, texture_coords, materialName = face
            if materialName in self.materials:
                currentMaterial = self.materials[materialName]
                if "textureID" in currentMaterial:
                    GL.glActiveTexture(GL.GL_TEXTURE0)
                    GL.glBindTexture(GL.GL_TEXTURE_2D, currentMaterial["textureID"])
                else:
                    rgb = currentMaterial["Kd"]
                    if rgb:
                        GL.glColor3f(rgb[0], rgb[1], rgb[2])
            else:
                GL.glColor3f(1.0, 1.0, 1.0)

            GL.glBegin(GL.GL_POLYGON)
            for i in range(len(vertices)):
                if normals[i] > 0:
                    normal = self.normals[normals[i] - 1]
                    GL.glNormal3f(normal[0], normal[1], normal[2])
                if texture_coords[i] > 0:
                    tex = self.texcoords[texture_coords[i] - 1]
                    if "SET1:lambert105SG" in materialName:
                        GL.glTexCoord2f(0.5 * tex[0], 0.5 * tex[1])
                    else:
                        GL.glTexCoord2f(tex[0], tex[1])
                else:
                    GL.glTexCoord2f(1.0, 1.0)
                vertex = self.vertices[vertices[i] - 1]
                GL.glVertex3f(vertex[0], vertex[1], vertex[2])
            GL.glEnd()

        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glEndList()

    def draw(self):
        GL.glCallList(self.glList)
