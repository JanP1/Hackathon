# gl_postprocess.py

import pygame
import numpy as np

from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader


VERT_SHADER_SRC = """
#version 120
attribute vec2 a_pos;
attribute vec2 a_tex;
varying vec2 v_tex;
void main() {
    v_tex = a_tex;
    gl_Position = vec4(a_pos, 0.0, 1.0);
}
"""


FRAG_SHADER_SRC = """
#version 120

uniform sampler2D u_scene;
uniform vec2  u_resolution;
uniform float u_time;
uniform float u_currentTime; // Aktualny czas w ms z Pygame

const int MAX_BULLETS = 16;
const int MAX_WAVES   = 8;

uniform int  u_numBullets;
uniform vec4 u_bullets[MAX_BULLETS]; // x,y,dir_x,dir_y

uniform int  u_numWaves;
// cx, cy, startTime (ms), thickness
uniform vec4 u_waves[MAX_WAVES];

// prędkość fali w pikselach na milisekundę
const float WAVE_SPEED = 0.5;
// parametry trójkątów
uniform float u_triLength;
uniform float u_triHalfWidth;
uniform float u_triStrength;

// parametry fal
uniform float u_waveStrength;

// tint (0..1) – ile czerwieni w obszarze efektu
uniform float u_triTint;
uniform float u_waveTint;

varying vec2 v_tex;

void main() {
    // Pygame ma Y do góry, GL do dołu – odwracamy
    vec2 uv = vec2(v_tex.x, 1.0 - v_tex.y);
    vec2 fragCoord = uv * u_resolution;

    vec2 displaced = fragCoord;

    // zbieramy, ile czerwonego tintu powinniśmy nałożyć (0..1)
    float tintFactor = 0.0;

    // -------------------------------
    // TRÓJKĄTY ZA POCISKAMI
    // -------------------------------
    for (int i = 0; i < MAX_BULLETS; ++i) {
        if (i >= u_numBullets) break;
        vec4 b = u_bullets[i];
        vec2 tip = b.xy;
        vec2 dir = normalize(b.zw + vec2(1e-6, 0.0)); // kierunek lotu
        dir = -dir; // trójkąt za pociskiem
        vec2 perp = vec2(-dir.y, dir.x);

        vec2 rel = displaced - tip;
        float d = dot(rel, dir);
        if (d < 0.0 || d > u_triLength) {
            continue;
        }
        float s = dot(rel, perp);
        float maxSide = u_triHalfWidth * (d / u_triLength);
        if (s < -maxSide || s > maxSide) {
            continue;
        }

        // normalizacja po długości 0..1
        float norm_d = d / u_triLength;

        // falowanie na boki (wzdłuż prostopadłej)
        float wave = sin(d * 0.08 - u_time * 6.0);
        float sideOffset = wave * u_triStrength * (1.0 - norm_d) * u_triHalfWidth * 0.5;
        float compress = 1.0 - u_triStrength * 0.35 * (1.0 - norm_d);
        float new_d = d * compress;
        float new_s = s + sideOffset;

        // przelicz z powrotem na xy
        vec2 srcRel = dir * new_d + perp * new_s;
        displaced = tip + srcRel;

        // im bliżej wierzchołka pocisku (norm_d blisko 0), tym mocniej świeci
        float localTint = (1.0 - norm_d) * u_triTint;
        tintFactor = max(tintFactor, localTint);
    }

    // -------------------------------
    // PIERŚCIENIE FAL
    // -------------------------------
    for (int i = 0; i < MAX_WAVES; ++i) {
        if (i >= u_numWaves) break;
        vec4 w = u_waves[i];
        vec2 center    = w.xy;
        float startTime = w.z;
        float thickness = w.w;

        float age = u_currentTime - startTime;
        if (age < 0.0) continue; // fala z przyszłości?
        float radius = age * WAVE_SPEED;

        float inner = max(0.0, radius - thickness * 0.5);
        float outer = radius + thickness * 0.5;

        vec2 rel = displaced - center;
        float dist = length(rel);
        if (dist <= inner || dist >= outer || dist <= 0.0) {
            continue;
        }

        float ringPos = (dist - radius) / (thickness * 0.5); // -1..1
        if (ringPos < -1.0 || ringPos > 1.0) continue;

        float wave = sin(dist * 0.15 - u_time * 4.5);
        float falloff = 1.0 - abs(ringPos);
        float offset = wave * u_waveStrength * thickness * falloff;

        float new_r = dist + offset;
        if (new_r <= 0.0) continue;

        float scale = new_r / dist;
        rel *= scale;
        displaced = center + rel;

        // maksymalny tint w środku grubości pierścienia
        float localTint = u_waveTint * falloff;
        tintFactor = max(tintFactor, localTint);
    }

    vec2 finalUV = displaced / u_resolution;
    finalUV = clamp(finalUV, vec2(0.0, 0.0), vec2(1.0, 1.0));

    vec4 col = texture2D(u_scene, finalUV);

    // delikatna, półprzezroczysta czerwień
    vec3 redColor = vec3(1.0, 0.15, 0.15);
    col.rgb = mix(col.rgb, redColor, clamp(tintFactor, 0.0, 1.0));

    gl_FragColor = col;
}
"""


class GLPostProcessor:
    """
    Bierze pygame.Surface (cały kadr gry), wrzuca do tekstury,
    odpalamy shader z trójkątami + pierścieniami, render na ekran.
    """

    MAX_BULLETS = 16
    MAX_WAVES = 8

    def __init__(self, width: int, height: int):
        self.width = int(width)
        self.height = int(height)

        # === SHADER ===
        self.program = compileProgram(
            compileShader(VERT_SHADER_SRC, GL_VERTEX_SHADER),
            compileShader(FRAG_SHADER_SRC, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.program)

        # uniformy
        self.u_scene = glGetUniformLocation(self.program, "u_scene")
        self.u_resolution = glGetUniformLocation(self.program, "u_resolution")
        self.u_time = glGetUniformLocation(self.program, "u_time")
        self.u_currentTime = glGetUniformLocation(self.program, "u_currentTime")

        self.u_numBullets = glGetUniformLocation(self.program, "u_numBullets")
        self.u_bullets = glGetUniformLocation(self.program, "u_bullets[0]")

        self.u_numWaves = glGetUniformLocation(self.program, "u_numWaves")
        self.u_waves = glGetUniformLocation(self.program, "u_waves[0]")

        self.u_triLength = glGetUniformLocation(self.program, "u_triLength")
        self.u_triHalfWidth = glGetUniformLocation(self.program, "u_triHalfWidth")
        self.u_triStrength = glGetUniformLocation(self.program, "u_triStrength")

        self.u_waveStrength = glGetUniformLocation(self.program, "u_waveStrength")

        # nowe uniformy do czerwonego tintu
        self.u_triTint = glGetUniformLocation(self.program, "u_triTint")
        self.u_waveTint = glGetUniformLocation(self.program, "u_waveTint")

        # wartości domyślne parametrów
        glUniform2f(self.u_resolution, float(self.width), float(self.height))
        glUniform1f(self.u_triLength, 220.0)
        glUniform1f(self.u_triHalfWidth, 70.0)
        glUniform1f(self.u_triStrength, 0.30)
        glUniform1f(self.u_waveStrength, 0.25)

        # domyślna siła czerwonego tintu (0..1)
        glUniform1f(self.u_triTint, 0.1)
        glUniform1f(self.u_waveTint, 0.1)

        # sampler
        glUniform1i(self.u_scene, 0)  # tekstura na jednostce 0

        # === FULLSCREEN QUAD ===
        # pos(x,y), tex(u,v)
        vertices = np.array(
            [
                #  x,   y,   u, v
                -1.0, -1.0, 0.0, 0.0,
                 1.0, -1.0, 1.0, 0.0,
                 1.0,  1.0, 1.0, 1.0,
                -1.0,  1.0, 0.0, 1.0,
            ],
            dtype=np.float32,
        )

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        # indeksy (dwa trójkąty)
        indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
        self.ibo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        # a_pos, a_tex
        self.a_pos = glGetAttribLocation(self.program, "a_pos")
        self.a_tex = glGetAttribLocation(self.program, "a_tex")

        # tekstura z kadrem gry
        self.scene_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.scene_tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glBindTexture(GL_TEXTURE_2D, 0)

        glDisable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def _upload_scene_texture(self, surface: pygame.Surface):
        # Pygame → bytes
        # 3 kanały RGB
        data = pygame.image.tostring(surface, "RGB", False)

        glBindTexture(GL_TEXTURE_2D, self.scene_tex)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            self.width,
            self.height,
            0,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            data,
        )
        glBindTexture(GL_TEXTURE_2D, 0)

    def _upload_bullets(self, bullets: list[tuple[float, float, float, float]]):
        # bullets: list[(x, y, vx, vy)]
        n = min(len(bullets), self.MAX_BULLETS)
        arr = np.zeros((self.MAX_BULLETS, 4), dtype=np.float32)
        for i in range(n):
            x, y, vx, vy = bullets[i]
            arr[i, 0] = x
            arr[i, 1] = y
            arr[i, 2] = vx
            arr[i, 3] = vy

        glUniform1i(self.u_numBullets, n)
        glUniform4fv(self.u_bullets, self.MAX_BULLETS, arr)

    def _upload_waves(self, waves: list[tuple[float, float, float, float]]):
        # waves: list[(cx, cy, startTime, thickness)]
        n = min(len(waves), self.MAX_WAVES)
        arr = np.zeros((self.MAX_WAVES, 4), dtype=np.float32)
        for i in range(n):
            cx, cy, startTime, thickness = waves[i]
            arr[i, 0] = cx
            arr[i, 1] = cy
            arr[i, 2] = startTime
            arr[i, 3] = thickness

        glUniform1i(self.u_numWaves, n)
        glUniform4fv(self.u_waves, self.MAX_WAVES, arr)

    def render(
        self,
        surface: pygame.Surface,
        bullets: list[tuple[float, float, float, float]],
        waves: list[tuple[float, float, float, float]],
        current_time_ms: float,
    ):
        # upload tekstury sceny
        self._upload_scene_texture(surface)

        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT)

        glUseProgram(self.program)

        # czas do animacji
        t = pygame.time.get_ticks() / 1000.0
        glUniform1f(self.u_time, t)

        # czas do obliczenia promienia fali
        glUniform1f(self.u_currentTime, float(current_time_ms))

        # dane distortu
        self._upload_bullets(bullets)
        self._upload_waves(waves)

        # quad
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)

        stride = 4 * 4  # 4 floaty (x, y, u, v)
        glEnableVertexAttribArray(self.a_pos)
        glVertexAttribPointer(self.a_pos, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))

        glEnableVertexAttribArray(self.a_tex)
        glVertexAttribPointer(self.a_tex, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8))

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.scene_tex)

        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

        glBindTexture(GL_TEXTURE_2D, 0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        glDisableVertexAttribArray(self.a_pos)
        glDisableVertexAttribArray(self.a_tex)

        glUseProgram(0)
