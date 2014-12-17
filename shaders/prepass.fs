#version 120

varying vec3 fs_in_normal;
varying vec3 fs_in_pos; // View Space
varying vec2 fs_in_texcoord;
varying vec4 fs_in_color;

uniform sampler2D uColorTexture;
uniform vec3 uCameraPosition;

uniform mat4 shadowmapVPmatrix;

vec3 dLightDirection = vec3(-0.5, -0.5, -0.5);
vec3 dLightDiffuseColor = vec3(1.0, 1.0, 1.0);
vec3 dLightSpecularColor = vec3(0.0, 0.0, 1.0);
float dLightIntensity = 1.0;

float flight()
{
	return dot(fs_in_normal, -dLightDirection);
}

vec3 vlight()
{
	float l = flight();
	return vec3(l);
}

void main() {

    vec4 color = texture2D(uColorTexture, fs_in_texcoord);
    if(color.xyz == vec3(0.0, 0.0, 0.0))
    {
        color = vec4(1.0) - 0.2 * fs_in_color;
        color.a = 1.0;
    }

    gl_FragData[0] = color;
    gl_FragData[1] = vec4(fs_in_normal, 1.0);
    gl_FragData[2] = vec4(fs_in_pos, 1.0);
    gl_FragData[3] = vec4(vlight(), 1.0);
}