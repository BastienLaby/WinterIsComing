#version 120

uniform sampler2D Texture;
uniform float sy;

void main()
{
    float blur = 0.0;
    
    for(int y = -2; y <= 2; y++)
    {
        blur += texture2D(Texture, vec2(gl_TexCoord[0].s, y * sy + gl_TexCoord[0].t)).r * (3.0 - abs(float(y)));
    }
    
    gl_FragColor = vec4(vec3(blur / 9.0), 1.0);

}