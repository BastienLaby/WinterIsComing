#version 120

uniform sampler2D tex;

void main() {
    vec4 color = texture2D(tex, gl_TexCoord[0].st);
    gl_FragColor = color;
    if(gl_FragColor.x <= 0.0 && gl_FragColor.y <= 0.0 && gl_FragColor.z <= 0)
    {
    	gl_FragColor = gl_Color;
    }
}