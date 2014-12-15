#version 120

varying float depth;
float near= 200;
float far = 0;  

void main()
{                   

    vec4 viewPos = (gl_ModelViewMatrix * gl_Vertex);
    
    depth = (-viewPos.z-near)/(far-near);

    gl_Position = ftransform();
}