#version 120

uniform sampler2D tex;

void main() {
    gl_TexCoord[0] = gl_TextureMatrix[0] * gl_MultiTexCoord0;
    gl_FrontColor = gl_Color;

	float height = texture2D(tex, gl_TexCoord[0].st).r;
	vec4 worldPos = gl_Vertex;
	worldPos.y = height * 10;
    gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * worldPos;
}