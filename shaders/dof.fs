/*
@author Bastien Laby, december 2014
*/

#version 120
#pragma optionNV (unroll all)

varying vec2 fragUV;

uniform sampler2D uTexture;
uniform sampler2D uDepthTexture;

uniform ivec2 uScreenResolution;

uniform mat4 uInverseProjectionMatrix;

float u_near_plane = 0.01;
float u_far_plane = 100.0;
float u_focus_plane = 10.0;
int u_blursize = 5;

void main() {
    vec4 blurred_result = vec4(0);
    vec2 pixel_size = 1.0 / uScreenResolution;
    for(int x = -u_blursize; x <= u_blursize; x++)
        for(int y = -u_blursize; y <= u_blursize; y++)
            blurred_result += texture2D(uTexture, vec2(x * pixel_size.x + fragUV.s, y * pixel_size.y + fragUV.t));

    int nb_ponderate_pixel = u_blursize * 2 + 1;
    blurred_result = vec4(blurred_result.rgb / pow(2.0 * u_blursize + 1, 2.0), 1.0);

    // Ponderate the blur

    float depth = texture2D(uDepthTexture, fragUV).r;
    vec2 xy = fragUV * 2.0 - 1.0; // ?
    vec4 frag_view_position = uInverseProjectionMatrix * vec4(xy, depth, 1.0);
    frag_view_position.xyz /= frag_view_position.w;
    float frag_view_depth = - frag_view_position.z;

    float blur_coeff = 0.0;

    if(frag_view_depth < u_focus_plane)
    {
        blur_coeff = abs((frag_view_depth - u_focus_plane) / u_near_plane);
    }
    else
    {
        blur_coeff = abs((frag_view_depth - u_focus_plane) / u_far_plane);
    }

    blur_coeff = clamp(blur_coeff, 0, 1);
    gl_FragColor =  vec4(mix(texture2D(uTexture, fragUV).rgb, blurred_result.rgb, blur_coeff), 1.0);
}