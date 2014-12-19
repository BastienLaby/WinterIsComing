/*
@author Bastien Laby, december 2014
*/

#version 120

varying vec2 fragUV;

void main()
{
    fragUV = gl_Vertex.xy;
    gl_Position = gl_Vertex * 2.0 - 1.0;
}