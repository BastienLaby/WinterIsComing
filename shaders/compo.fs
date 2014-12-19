/*
@author Bastien Laby, december 2014
*/

#version 120
#pragma optionNV (unroll all)

varying vec2 fragUV;

uniform sampler2D uColorTexture;
uniform sampler2D uIllumTexture;
uniform sampler2D uIDTexture;

uniform vec2 uScreenResolution;

vec4 blurXY(sampler2D tex, vec2 uv, int blurSize) {
    vec4 blur = vec4(0);
    float offsetX = 2 * 1.0/(1.0*uScreenResolution.x);
    float offsetY = 2 * 1.0/(1.0*uScreenResolution.y);
    for(int x = -blurSize; x <= blurSize; x++)
        for(int y = -blurSize; y <= blurSize; y++)
            blur += texture2D(tex, vec2(x * offsetX + uv.s, y * offsetY + uv.t));
    return vec4(blur.rgb / pow(2.0*blurSize+1, 2.0), 1.0);
}

void main() {

   // Get Basic textures
    vec4 color = texture2D(uColorTexture, fragUV);
    vec4 illum = texture2D(uIllumTexture, fragUV);
    vec4 id = texture2D(uIDTexture, fragUV);

    // Color + Light
    float light = illum.b;
    color = id.g * (color * (light + 0.8)) + id.r * color;

    // Blur snow
    vec4 idblurred = blurXY(uIDTexture, fragUV, 3);
    vec4 colorblurred = blurXY(uColorTexture, fragUV, 3);
    vec4 total = color * idblurred.g + (color * 0.2) + colorblurred * idblurred.r;

    // Window halo
    gl_FragColor = total;

}