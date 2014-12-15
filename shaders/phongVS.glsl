

varying vec3 normal,lightDir0,lightDir1, eyeVec;
uniform vec3 infiniteDir;

void main()
{
    normal = gl_NormalMatrix * gl_Normal;

    vec3 vVertex = (gl_ModelViewMatrix * gl_Vertex).xyz;

    lightDir0 = vec3(infiniteDir[0],-infiniteDir[1],infiniteDir[2]);

    eyeVec = -vVertex;

    gl_FrontColor = gl_Color;
    
    gl_Position = ftransform();

}