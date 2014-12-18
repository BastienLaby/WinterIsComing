#version 120

varying vec3 fs_in_normal;
varying float fs_in_depth;
varying vec2 fs_in_texcoord;
varying vec4 fs_in_color;

uniform sampler2D uColorTexture;
uniform vec3 uCameraPosition;
uniform int uIsSnow = 0;

vec3 dLightDirection = vec3(-0.5, -0.7, -0.5);
vec3 dLightDiffuseColor = vec3(1.0, 1.0, 1.0);
vec3 dLightSpecularColor = vec3(0.0, 0.0, 1.0);
float dLightIntensity = 0.6;

float flight()
{
	return dLightIntensity * dot(fs_in_normal, -dLightDirection);
}

vec3 vlight()
{
	float l = flight();
	return vec3(l);
}

void main() {

    // Render Texture 1 : Color
    vec4 color = texture2D(uColorTexture, fs_in_texcoord);
    if(color.xyz == vec3(0.0, 0.0, 0.0))
    {
        color = vec4(1.0) - 0.3 * fs_in_color;
        color.a = 1 - fs_in_color.a;
    }
    else {
        color.a = 1.0;
    }
    gl_FragData[0] = color;

    // Render Texture 2 : R=camera depth, G=shadowmap depth, B=lightFactor
    float r = fs_in_depth;
    float g = 0.0;
    float b = flight();
    gl_FragData[1] = vec4(r, g, b, 1.0);

    // Render Texture 3 : Cache. Snow = red, Other = green
    if(uIsSnow == 1)
    	gl_FragData[2] = vec4(1.0, 0.0, 0.0, 1.0);
    else
    	gl_FragData[2] = vec4(0.0, 1.0, 0.0, 1.0);
    
    // Render Texture 4 : Normal (used for SSAO)
    gl_FragData[3] = vec4(normalize(fs_in_normal) * 0.5 + 0.5, 1.0);
}