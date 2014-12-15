#version 120

uniform float LightIntensity;

void main(void)
{
	gl_FragColor = vec4(LightIntensity, LightIntensity, LightIntensity, 1);
}


