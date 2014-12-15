#version 120

uniform sampler2D Texture;
uniform float sx;

void main()
{
    float blur = 0.0;
    
    for(int x = -2; x <= 2; x++)
    {
        blur += texture2D(Texture, vec2(x * sx + gl_TexCoord[0].s, gl_TexCoord[0].t)).r * (3.0 - abs(float(x)));
    }
    
    gl_FragColor = vec4(vec3(blur / 9.0), 1.0);
}