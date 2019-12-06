import math
import random
import numpy as np
import sys, os

from OpenGL.GL import *
from OpenGL import GL as gl
from OpenGL import GLU as glu
from OpenGL import GLUT as glut
from PIL import Image

WIDTH = 640
HEIGHT = 480
FPS = 30
TIMER_MS = int (1000/FPS) # converting FPS to ms
TEXTURE = os.path.abspath('textures/snow.png')
GRAVITY = 3.0
NUM_PARTICLES = 1000
STEP_TIME = 0.01
PARTICLE_SIZE = 0.05

class Particle():
    def __init__(self, pos, velocity, color, time_alive, life_span):
        self.pos = pos
        self. velocity = velocity
        self.color = color
        self.time_alive = time_alive
        self.life_span = life_span

    def _rotate(self, v, axis, degrees):
        axis = axis / np.linalg.norm(axis) # normalizing
        radians = degrees * math.pi / 180
        s = math.sin(radians)
        c = math.cos(radians)
        return v * c + axis * axis.dot(v) * (1 - c) + np.cross(v, axis) * s;

    def adjust_position(self):
        axis = np.array([1, 0, 0])
        angle = -30
        return self._rotate(self.pos, axis, angle)

class ParticleSystem():
    def __init__(self, texture):
        self.texture = texture
        self.angle = 0
        self.color_time = 0
        self.next_step = 0
        self.particles = self._init_particles()

        for _ in range(250):
            self._step()

    def advance(self, dt):
        while dt > 0:
            if self.next_step < dt:
                dt -= self.next_step
                self._step()
                self.next_step = STEP_TIME
            else:
                self.next_step -= dt
                dt = 0

    def draw(self):
        self.particles.sort(key = lambda x : x.pos[2])

        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        gl.glBegin(gl.GL_QUADS)
        for i in range(len(self.particles)):
            p = self.particles[i]
            gl.glColor4f(p.color[0], p.color[1], p.color[2], (1 - p.time_alive / p.life_span))
            size = PARTICLE_SIZE / 2
            pos = p.adjust_position()

            gl.glTexCoord2f(0, 0)
            gl.glVertex3f(pos[0] - size, pos[1] - size, pos[2])
            gl.glTexCoord2f(0, 1)
            gl.glVertex3f(pos[0] - size, pos[1] + size, pos[2])
            gl.glTexCoord2f(1, 1)
            gl.glVertex3f(pos[0] + size, pos[1] + size, pos[2])
            gl.glTexCoord2f(1, 0)
            gl.glVertex3f(pos[0] + size, pos[1] - size, pos[2])

        gl.glEnd()


    def _init_particles(self):
        p = []
        for _ in range(NUM_PARTICLES):
            p.append(self._create_particle())
        return p

    def _cur_velocity(self):
        return np.array([2 * math.cos(self.angle), 2.0, 2 * math.sin(self.angle)])

    def _cur_color(self):
        color = None
        if self.color_time < 0.16667: # 1/6
            color = np.array([1, self.color_time * 6, 0])
        elif self.color_time < 0.33333: # 1/3
            color = np.array([(0.33333 - self.color_time) * 6, 1, 0])
        elif self.color_time < 0.5: # 1/2
            color = np.array([0, 1, (self.color_time - 0.33333) * 6])
        elif self.color_time < 0.66667: # 2/3
            color = np.array([0, (0.66667 - self.color_time) * 6, 1])
        elif self.color_time < 0.83333: # 5/6
            color = np.array([(self.color_time - 0.66667) * 6, 0, 1])
        else:
            color = np.array([1, 0, (1 - self.color_time) * 6])

        for i in range(len(color)):
            if color[i] < 0:
                color[i] = 0
            if color[i] > 1:
                color[i] = 1
        return color

    def _create_particle(self):
        velocity = self._cur_velocity()
        for i in range(len(velocity)):
            velocity[i] += 0.5 * random.random() - 0.25 # [-0.25, 0.25]

        p = Particle(
            np.array([0.0, 0.0, 0.0]),
            velocity,
            self._cur_color(),
            0,
            random.random() + 1 # [1, 2]
        )
        return p

    def _step(self):
        self.color_time += STEP_TIME / 10
        while self.color_time >= 1:
            self.color_time -= 1

        self.angle += 0.5 * STEP_TIME
        while self.angle > 2 * math.pi:
            self.angle -= 2 * math.pi

        for i in range(NUM_PARTICLES):
            p = self.particles[i]

            p.pos += p.velocity * STEP_TIME
            p.velocity += np.array([0, -GRAVITY * STEP_TIME, 0])
            p.time_alive += STEP_TIME
            if p.time_alive > p.life_span:
                self.particles[i] = self._create_particle()

def load_texture(filename):
    texture = glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
    image = Image.open(filename)
    #img_data = numpy.array(list(image.getdata()), numpy.uint8)
    flipped_image = image.transpose(Image.FLIP_TOP_BOTTOM)
    img_data = flipped_image.convert("RGBA").tobytes()
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, image.width, image.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img_data)
    return texture

def initGL():
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glEnable(gl.GL_COLOR_MATERIAL)
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

def handle_resize(width, heigth):
    gl.glViewport(0, 0, width, heigth)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    glu.gluPerspective(45, width/heigth, 1, 200)

def display():
    global ps
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    gl.glTranslate(0, 0, -10)
    gl.glScale(2, 2, 2)
    ps.draw()
    glut.glutSwapBuffers()

def update(value):
    global ps
    ps.advance(TIMER_MS / 1000)
    glut.glutPostRedisplay()
    glut.glutTimerFunc(TIMER_MS, update, 0)

if __name__ == '__main__':
    glut.glutInit(sys.argv)
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_DEPTH)
    glut.glutInitWindowSize(WIDTH, HEIGHT)
    glut.glutCreateWindow(b'Particle system')
    initGL()
    texture = load_texture(TEXTURE)
    ps = ParticleSystem(texture)
    glut.glutDisplayFunc(display)
    glut.glutReshapeFunc(handle_resize)
    glut.glutTimerFunc(20, update, 0)
    glut.glutMainLoop()
