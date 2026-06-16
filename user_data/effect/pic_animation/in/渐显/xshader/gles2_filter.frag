precision highp float;
varying vec2 uv0;
// #define texCoord uv0

// #define BLUR_MOTION 0x1
// #define BLUR_SCALE  0x2

uniform float inputHeight;
uniform float inputWidth;

uniform float blurStep;
uniform mat4 u_InvModel;
uniform vec2 blurDirection;

uniform sampler2D _MainTex;
#define inputImageTexture _MainTex

// #if defined(BLUR_TYPE) && BLUR_TYPE == BLUR_SCALE
// #define num 25
// #else
// #define num 7
// #endif

const float PI = 3.141592653589793;

/* random number between 0 and 1 */
float random(in vec3 scale, in float seed) {
    /* use the fragment position for randomness */
    return fract(sin(dot(gl_FragCoord.xyz + seed, scale)) * 43758.5453 + seed);
}

vec4 crossFade(in vec2 uv, in float dissolve) {
    return texture2D(inputImageTexture, uv).rgba;
}


void main() {

    float ratio = inputWidth / inputHeight;

    vec2 uv = (u_InvModel * vec4((uv0.x * 2.0 - 1.0) * ratio, uv0.y * 2.0 - 1.0, 0.0, 1.0)).xy;

    uv.x = (uv.x / ratio + 1.0) / 2.0;
    uv.y = (uv.y + 1.0) / 2.0;


    gl_FragColor = texture2D(inputImageTexture, uv) * step(uv.x, 1.0) * step(uv.y, 1.0) * step(0.0, uv.x) * step(0.0, uv.y);
	

    
}
