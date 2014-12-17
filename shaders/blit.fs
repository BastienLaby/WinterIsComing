#version 120

varying vec2 fragUV;
uniform sampler2D uTexture;

void main()
{
    gl_FragColor = texture2D(uTexture, fragUV);
}