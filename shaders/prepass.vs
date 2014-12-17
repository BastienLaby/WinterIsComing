#version 120

varying vec3 fs_in_normal;
varying vec3 fs_in_pos; // View Space
varying vec2 fs_in_texcoord;
varying vec4 fs_in_color;

void main() {

	fs_in_normal = gl_NormalMatrix * gl_Normal;
	fs_in_pos = (gl_ModelViewMatrix * gl_Vertex).xyz;
    fs_in_texcoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).st;
    fs_in_color = gl_Color;
    gl_Position = gl_ProjectionMatrix * vec4(fs_in_pos, 1.0);
}