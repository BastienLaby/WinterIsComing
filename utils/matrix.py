import math

from .transformations import clip_matrix


def create_perspective_matrix(fov, aspectratio, znear, zfar):
    fov *= math.pi / 180.0  # Degree to radians
    top = math.tan(fov * 0.5) * znear
    bottom = -top
    left = aspectratio * bottom
    right = aspectratio * top
    return clip_matrix(left, right, bottom, top, znear, zfar, perspective=True)
