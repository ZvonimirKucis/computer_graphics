import numpy as np

from OpenGL import GL as gl
from OpenGL import GLU as glu
from OpenGL import GLUT as glut

import sys
import csv

WIDTH = 640
HEIGHT = 480
DCM = False

CONTROL_POINTS_FILENAME = 'points.csv'
OBJECT_FILENAME = 'aircraft747.obj'

# control points for B spline
points = []
with open(CONTROL_POINTS_FILENAME) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count != 0:
            points.append([int(row[0]), int(row[1]), int(row[2])])
        line_count += 1

# B spline points and tangents
curve_points = []
tangent_vectors = []
diff2_values = []
t_values = np.arange(0.0, 1.0, 0.05)
periodic_sample_matrix = np.matrix('-1 3 -3 1 ; 3 -6 3 0 ; -3 0 3 0 ; 1 4 1 0')
tangent_matrix = np.matrix('-1 3 -3 1 ; 2 -4 2 0 ; -1 0 1 0')
diff2_matrix = np.matrix('-1 3 -3 1 ; 2 -4 2 0')

for i in range(len(points) - 3):
    points_vector = np.array([points[i], 
                            points[i + 1],
                            points[i + 2],
                            points[i + 3]])
    periodic_mul = (1/6) * (periodic_sample_matrix * points_vector)
    tangent_mul = (1/2) * (tangent_matrix * points_vector)
    diff2_mul = (1/2) * (diff2_matrix * points_vector)
    for t in t_values:
        t_vector = np.array([pow(t, 3), pow(t, 2), t, 1])
        curve_point = np.asarray(t_vector * periodic_mul)[0]
        tangent_vector = np.asarray(t_vector[1:] * tangent_mul)[0]
        diff2_value = np.asarray(np.array([2*t, 1]) * diff2_mul)[0]

        curve_points.append(curve_point)
        tangent_vectors.append(tangent_vector)
        diff2_values.append(diff2_value)


# load object
object_vertices = []
object_edges = []
with open(OBJECT_FILENAME) as object_file:
    for line in object_file:
        tokens = line.split()
        if len(tokens) > 0 and tokens[0] == 'v':
            object_vertices.append(tokens[1:4])            
        elif len(tokens) > 0 and tokens[0] == 'f':
            object_edges.append(tokens[1:4])

object_vertices = np.array(object_vertices, float)
object_edges = np.array(object_edges, int)

def initGL(width, height):
    gl.glClearColor(1, 1, 0.95, 0.0)
    gl.glClearDepth(1.0)
    gl.glDepthFunc(gl.GL_LESS)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glShadeModel(gl.GL_SMOOTH)
    
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    glu.gluPerspective(45.0, float(width)/float(height), 0.1, 100.0)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    
def idle(value):
    global i
    global n

    i += 1
    if i >= n:
        i = 0
        
    glut.glutPostRedisplay()
    glut.glutTimerFunc(20, idle, 0)
    
def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glLoadIdentity()
    gl.glTranslatef(-10, 0, -80)
    gl.glRotate(30, 10.0, 10.0, 13.0)

    # scene
    gl.glPushMatrix()
    gl.glBegin(gl.GL_LINE_STRIP)
    gl.glColor3f(0.87, 0.39, 0.29)
    for point in curve_points:
        gl.glVertex3f(point[0], point[1], point[2])   
    gl.glEnd()
    gl.glPopMatrix()
    
    gl.glPushMatrix()
    gl.glBegin(gl.GL_LINES)
    gl.glColor3f(0.47, 0.12, 0.58)
    gl.glVertex3f(curve_points[i][0], curve_points[i][1], curve_points[i][2])
    gl.glVertex3f(curve_points[i][0] + tangent_vectors[i][0] * 0.8, 
                    curve_points[i][1] + tangent_vectors[i][1] * 0.8, 
                    curve_points[i][2] + tangent_vectors[i][2] * 0.8)
    gl.glEnd()
    gl.glPopMatrix()
    
    gl.glPushMatrix()
    animate(dcm=DCM)
    gl.glPopMatrix()
    glut.glutSwapBuffers()

def animate(dcm=False):  
    curve_point = curve_points[i]
    curve_tangent = tangent_vectors[i]
    temp_object_vertices = object_vertices
    gl.glPushMatrix()
    gl.glTranslatef(curve_point[0],
                    curve_point[1],
                    curve_point[2])
    gl.glScalef(6, 6, 6)

    if dcm:
        curve_diff2 = diff2_values[i]

        w = curve_tangent / np.linalg.norm(curve_tangent)
        u = np.cross(curve_tangent, curve_diff2)
        u = u / np.linalg.norm(u)
        v = np.cross(w, u)
        v = v / np.linalg.norm(v)

        R = np.column_stack([v, u, w])
        R = np.linalg.inv(R)

        obj_vertices_rot = []
        for vertex in object_vertices:
            v = np.array(vertex)
            v_rot = np.ndarray.tolist( np.dot(v, R) )
            if np.isnan(v_rot[0]):
                v_rot = np.random.rand(3)
                v_rot = v_rot / np.linalg.norm(v_rot)
            obj_vertices_rot.append(v_rot)
        temp_object_vertices = obj_vertices_rot
    else:
        curr_orient = np.array([0, 0, 1])  
        rotation_axis = np.cross(curr_orient, curve_tangent)

        dot_curr_next = np.dot(curr_orient, curve_tangent)
        curr_mag = np.linalg.norm(curr_orient)
        next_mag = np.linalg.norm(curve_tangent)

        rotation_angle = np.rad2deg(np.arccos(dot_curr_next / (curr_mag * next_mag)))
        gl.glRotate(rotation_angle, rotation_axis[0], rotation_axis[1], rotation_axis[2])

    gl.glBegin(gl.GL_TRIANGLES)
    gl.glColor3f(0.19, 0.4, 0.75)
    for edge in object_edges:
        for v_i in edge:
            gl.glVertex3f(temp_object_vertices[v_i-1][0],
                        temp_object_vertices[v_i-1][1],
                        temp_object_vertices[v_i-1][2])
    gl.glEnd()
    gl.glPopMatrix()

# main
n = len(curve_points)
i = 0

glut.glutInit(sys.argv)
glut.glutInitDisplayMode(glut.GLUT_RGBA | glut.GLUT_DOUBLE | glut.GLUT_DEPTH)
glut.glutInitWindowSize(WIDTH, HEIGHT)
window = glut.glutCreateWindow(b'Animation')
glut.glutDisplayFunc(display)
glut.glutTimerFunc(20, idle, 0)
initGL(WIDTH, HEIGHT)
glut.glutMainLoop()