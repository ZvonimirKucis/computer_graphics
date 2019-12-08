import math
import random
import numpy as np
import sys, os

from OpenGL import GL as gl
from OpenGL import GLU as glu
from OpenGL import GLUT as glut
from PIL import Image

WIDTH = 640
HEIGHT = 480
FPS = 30
TIMER_MS = int (1000/FPS) # converting FPS to ms

# particle system configuration
TEXTURE = os.path.abspath('textures/snow.png')
GRAVITY = 3.0
NUM_PARTICLES = 1000
STEP_TIME = 0.01
PARTICLE_SIZE = 0.05
START_COLOR = [1.0, 0.0 ,0.2]
END_COLOR = [0.0, 1.0, 0.2]

class Particle():
    def __init__(self, pos, velocity, life_span):
        self.pos = pos
        self. velocity = velocity
        self.color = [0.0, 0.0, 0.0]
        self.time_alive = 0
        self.alpha = 1
        self.life_span = life_span

    def adjust_rotation(self):
        matrix = (gl.GLfloat * 16)()
        gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX, matrix)
        matrix = list(matrix)
        curr_orient = np.array([0, 0, 1])
        view_vector = np.array([matrix[2], matrix[6], matrix[10]])  
        rotation_axis = np.cross(curr_orient, view_vector)

        dot_curr_next = np.dot(curr_orient, view_vector)
        curr_mag = np.linalg.norm(curr_orient)
        next_mag = np.linalg.norm(view_vector)

        rotation_angle = np.rad2deg(np.arccos(dot_curr_next / (curr_mag * next_mag)))
        gl.glRotate(rotation_angle, rotation_axis[0], rotation_axis[1], rotation_axis[2])

    def adjust_color(self):
        self.alpha = 1 - self.time_alive / self.life_span
        self.color[0] = self.alpha * START_COLOR[0] + (1 - self.alpha) * END_COLOR[0]
        self.color[1] = self.alpha * START_COLOR[1] + (1 - self.alpha) * END_COLOR[1]
        self.color[2] = self.alpha * START_COLOR[2] + (1 - self.alpha) * END_COLOR[2]
        for i in range(len(self.color)):
            if self.color[i] < 0:
                self.color[i] = 0
            if self.color[i] > 1:
                self.color[i] = 1

class ParticleSystem():
    def __init__(self, texture):
        self.texture = texture
        self.angle = 0
        self.next_step = 0
        self.particles = self._init_particles()

        print("Loading...")
        for _ in range(int(NUM_PARTICLES / 4)):
            self._step()
        print("Done.")

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

        for i in range(len(self.particles)):
            p = self.particles[i]
            p.adjust_color()
            gl.glColor4f(p.color[0], p.color[1], p.color[2], (1 - p.time_alive / p.life_span))
            size = PARTICLE_SIZE / 2
            p.adjust_rotation()
            pos = p.pos
            gl.glBegin(gl.GL_QUADS)   
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

    def _create_particle(self):
        velocity = self._cur_velocity()
        for i in range(len(velocity)):
            velocity[i] += 0.5 * random.random() - 0.25 # [-0.25, 0.25]

        p = Particle(
            np.array([0.0, 0.0, 0.0]),
            velocity,
            random.random() + 1 # [1, 2]
        )
        return p

    def _step(self):
        self.angle += 0.5 * STEP_TIME
        if self.angle > 2 * math.pi:
            self.angle -= 2 * math.pi

        for i in range(NUM_PARTICLES):
            p = self.particles[i]

            p.pos += p.velocity * STEP_TIME
            p.velocity += np.array([0, -GRAVITY * STEP_TIME, 0])
            p.time_alive += STEP_TIME
            if p.time_alive > p.life_span:
                self.particles[i] = self._create_particle()

def load_texture(filename):
    texture = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
    image = Image.open(filename)
    img_data = np.array(list(image.getdata()), np.uint8)
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
    gl.glMatrixMode(gl.GL_MODELVIEW)

def display():
    global ps
    global delta_move

    gl.glClearColor(1, 1, 0.95, 0.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glLoadIdentity()
    move_me(delta_move)
    gl.glPushMatrix()
    gl.glTranslate(0, 0, -10)
    gl.glScale(2, 2, 2)
    ps.draw()
    gl.glPopMatrix()
    gl.glFlush()
    glut.glutSwapBuffers()

def update(value):
    global ps
    ps.advance(TIMER_MS / 1000)
    glut.glutPostRedisplay()
    glut.glutTimerFunc(TIMER_MS, update, 0)

def process_normal_input(key, x, y):
    if key.decode("UTF-8") == chr(27): # escape
        print('Closing application...')
        sys.exit(0)

def press_key(key, x, y):
    global delta_angle
    global delta_move

    if key == glut.GLUT_KEY_LEFT:
        delta_angle = -0.1
    elif key == glut.GLUT_KEY_RIGHT:
        delta_angle = 0.1
    elif key == glut.GLUT_KEY_UP:
        delta_move = 10
    elif key == glut.GLUT_KEY_DOWN:
        delta_move = -10

def release_key(key, x, y):
    global delta_angle
    global delta_move

    if key == glut.GLUT_KEY_LEFT:
        delta_angle = 0
    elif key == glut.GLUT_KEY_RIGHT:
        delta_angle = 0
    elif key == glut.GLUT_KEY_UP:
        delta_move = 0
    elif key == glut.GLUT_KEY_DOWN:
        delta_move = 0

def move_me(delta):
    global x,y,z
    global lx,ly,lz

    x = x + delta * lx * 0.1
    z = z + delta * lz * 0.1
    glu.gluLookAt(x, y, z, x + lx, y, z + lz, 0, 1, 0)

if __name__ == '__main__':
    delta_move = 0
    x=0.0; y=1; z=1.0
    lx=0; ly=0; lz=-1

    glut.glutInit(sys.argv)
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_DEPTH)
    glut.glutInitWindowSize(WIDTH, HEIGHT)
    window = glut.glutCreateWindow(b'Particle system')

    # init and load
    initGL()
    texture = load_texture(TEXTURE)
    ps = ParticleSystem(texture)

    # input commands
    glut.glutIgnoreKeyRepeat(1)
    glut.glutSpecialFunc(press_key)
    glut.glutSpecialUpFunc(release_key)
    glut.glutKeyboardFunc(process_normal_input)

    glut.glutDisplayFunc(display)
    glut.glutReshapeFunc(handle_resize)
    glut.glutTimerFunc(TIMER_MS, update, 0)
    glut.glutMainLoop()