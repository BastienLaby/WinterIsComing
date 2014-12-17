#version 120

varying vec3 Normal;


void main() {
    gl_TexCoord[0] = gl_TextureMatrix[0] * gl_MultiTexCoord0;
    Normal = gl_NormalMatrix * gl_Normal;
    gl_FrontColor = gl_Color;
    gl_Position = ftransform();
}