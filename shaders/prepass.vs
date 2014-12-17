#version 120

varying vec3 fs_in_normal;
varying float fs_in_depth;
varying vec2 fs_in_texcoord;
varying vec4 fs_in_color;

void main() {

	fs_in_normal = gl_Normal;
    fs_in_texcoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).st;
    fs_in_color = gl_Color;

    gl_Position = ftransform();
    gl_Position.z;
    
}