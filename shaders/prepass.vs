#version 120

uniform sampler2D tex;

void main() {
    gl_TexCoord[0] = gl_TextureMatrix[0] * gl_MultiTexCoord0;
    gl_FrontColor = gl_Color;
    gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;
}