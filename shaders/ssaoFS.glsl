#version 120

uniform sampler2D uNormalTexture;
uniform sampler2D uDepthTexture;
uniform sampler2D uRandomTexture;

uniform mat4x4 uInverseProjection;

uniform float znear;
uniform float zfar;

uniform float distanceThreshold;
uniform vec2 filterRadius;

varying vec2 uv;

const int sampleCount = 16;
const vec2 samples[] = vec2[](    // These are the Poisson Disk Samples
    vec2( -0.94201624,  -0.39906216 ),
    vec2(  0.94558609,  -0.76890725 ),
    vec2( -0.094184101, -0.92938870 ),
    vec2(  0.34495938,   0.29387760 ),
    vec2( -0.91588581,   0.45771432 ),
    vec2( -0.81544232,  -0.87912464 ),
    vec2( -0.38277543,   0.27676845 ),
    vec2(  0.97484398,   0.75648379 ),
    vec2(  0.44323325,  -0.97511554 ),
    vec2(  0.53742981,  -0.47373420 ),
    vec2( -0.26496911,  -0.41893023 ),
    vec2(  0.79197514,   0.19090188 ),
    vec2( -0.24188840,   0.99706507 ),
    vec2( -0.81409955,   0.91437590 ),
    vec2(  0.19984126,   0.78641367 ),
    vec2(  0.14383161,  -0.14100790 )
   );


void main()
{



    // reconstruct fragment attributes
    float fragDepth = texture2D(uDepthTexture, uv).r;
    vec4 fragPos = uInverseProjection * vec4(uv.st, fragDepth, 1.0);
    fragPos.xyz /= fragPos.w;
    vec3 fragNormal = normalize(texture2D(uNormalTexture, uv.st).rgb * 2.0 - 1.0);

    float occlusion = 0;

    for (int i = 0; i < sampleCount; ++i)
    {
        // reconstruct sample attributes
        vec2 sampleTexCoord = uv + (samples[i] * (filterRadius));
        float sampleDepth = texture2D(uDepthTexture, sampleTexCoord).r;

        vec4 samplePos = uInverseProjection * vec4(sampleTexCoord, sampleDepth, 1.0);
        samplePos.xyz /= samplePos.w;

        vec3 sampleDir = normalize(samplePos.xyz - fragPos.xyz);
        float d = abs(samplePos.xyz - fragPos.xyz);

        float NdotS = max(dot(fragNormal, sampleDir), 0);
        // distance between SURFACE-POSITION and SAMPLE-POSITION
        float VPdistSP = distance(fragPos, samplePos);
 
        // a = distance function
        float a = 1.0 - smoothstep(distanceThreshold, distanceThreshold * 2, VPdistSP);
        // b = dot-Product
        float b = NdotS;
 
        occlusion += (a * b);
        
    }

    occlusion = 1 - (occlusion / sampleCount);

    gl_FragColor = vec4(occlusion, occlusion, occlusion, 1.0);


}