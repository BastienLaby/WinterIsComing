#version 120

varying vec3 Normal;

uniform sampler2D tex;

void main() {
    vec4 color = texture2D(tex, gl_TexCoord[0].st);
    if(color.xyz == vec3(0.0, 0.0, 0.0))
    {
        color = vec4(1.0) - 0.2 * gl_Color;
        color.a = 1.0;
    }
    gl_FragColor = color;
}