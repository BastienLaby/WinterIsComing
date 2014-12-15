#version 120

varying vec2 uv;

uniform sampler2D Normal;

uniform vec3 LightDirection;
uniform float LightIntensity;

vec3 computeDirectionnalLight(	vec3 fragNormal,
								vec3 lightDirection,
								float lightIntensity)

{
		// Directionnallight calculation formula
		vec3 n = normalize(fragNormal);
		vec3 l = -normalize(lightDirection);
		float n_dot_l = clamp(dot(n, l), 0, 1.0);
		return vec3(lightIntensity * n_dot_l, lightIntensity * n_dot_l, lightIntensity * n_dot_l);
}

void main(void)
{
	// Recover fragment parameters
	vec3 fragNormal = texture2D(Normal, gl_TexCoord[0].st).xyz;

	// Apply light(s)
	vec3 dirLight = computeDirectionnalLight(fragNormal, LightDirection, LightIntensity);

	// Set the output color
	gl_FragColor = vec4(dirLight, 1);
}