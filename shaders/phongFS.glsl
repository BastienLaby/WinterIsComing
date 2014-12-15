#version 120

varying vec3 normal, lightDir0, lightDir1, eyeVec;

uniform float  intensity;
uniform vec4 infiniteRGB;

void main (void)
{

    vec4 color = vec4(infiniteRGB[0],infiniteRGB[1],infiniteRGB[2],1);
    
    vec4 final_color =
    (color  * gl_FrontMaterial.ambient);
    +
    (gl_LightSource[0].ambient * gl_FrontMaterial.ambient) +
    (gl_LightSource[1].ambient * gl_FrontMaterial.ambient);

    vec3 N = normalize(normal);
    vec3 L0 = normalize(lightDir0);
    vec3 L1 = normalize(lightDir1);

    float lambertTerm0 = dot(N,L0);
    float lambertTerm1 = dot(N,L1);

    if(lambertTerm0 > 0.0)
    {
        final_color += gl_LightSource[0].diffuse *
                       gl_FrontMaterial.diffuse *
                       lambertTerm0*intensity*2;

        vec3 E = normalize(eyeVec);
        vec3 R = reflect(-L0, N);
        float specular = pow( max(dot(R, E), 0.0),
                         gl_FrontMaterial.shininess );
        final_color += gl_LightSource[0].specular *
                       gl_FrontMaterial.specular *
                       specular;
    }

    if(lambertTerm1 > 0.0)
    {
        final_color += gl_LightSource[1].diffuse *
                       gl_FrontMaterial.diffuse *
                       lambertTerm1;

        vec3 E = normalize(eyeVec);
        vec3 R = reflect(-L1, N);
        float specular = pow( max(dot(R, E), 0.0),
                         gl_FrontMaterial.shininess );
        final_color += gl_LightSource[1].specular *
                       gl_FrontMaterial.specular *
                       specular;
    }

    gl_FragColor = final_color;

}