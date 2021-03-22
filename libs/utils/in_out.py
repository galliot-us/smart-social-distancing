import numpy as np
from numpy import linalg as LA


# Auxiliary methods taken from:
# https://github.com/yas-sim/object-tracking-line-crossing-area-intrusion/blob/master/object-detection-and-line-cross.py
def check_line_cross(boundary_line, trajectory):
    """
    Args:
        boundary_line: Two coordinates [x,y] are in 2-tuples [A,B]
                Boundaries of the in/out line.
                If someone crosses the line while having A to their right, they are going in the in direction (entering)
                Crossing the line while having A to their left means they are going in the out direction (leaving)
        trajectory: vector ((x1, y1), (x2, y2))

    Returns:
        (in, out) : tuple
             (1, 0) - if the trajectory crossed the boundary entering (in)
             (0, 1) - if the trajectory crossed the boundary leaving (out)
             (0, 0) - if the trajectory didn't cross the boundary.
    """
    traj_p0 = (trajectory[0][0], trajectory[0][1])  # Trajectory of an object
    traj_p1 = (trajectory[1][0], trajectory[1][1])
    b_line_p0 = (boundary_line[0][0], boundary_line[0][1])  # Boundary line
    b_line_p1 = (boundary_line[1][0], boundary_line[1][1])
    intersect = check_intersect(traj_p0, traj_p1, b_line_p0, b_line_p1)  # Check if intersect or not
    if intersect == False:
        return 0, 0

    angle = calc_vector_angle(traj_p0, traj_p1, b_line_p0, b_line_p1)  # Calculate angle between trajectory and boundary line
    if angle < 180: # in
        return 1, 0
    else: # out
        return 0, 1

def check_intersect(p1, p2, p3, p4):
    """
    Check if the line p1-p2 intersects the line p3-p4
    Args:
        p1: (x,y)
        p2: (x,y)
        p3: (x,y)
        p4: (x,y)

    Returns:
        boolean : True if intersection occurred
    """
    tc1 = (p1[0] - p2[0]) * (p3[1] - p1[1]) + (p1[1] - p2[1]) * (p1[0] - p3[0])
    tc2 = (p1[0] - p2[0]) * (p4[1] - p1[1]) + (p1[1] - p2[1]) * (p1[0] - p4[0])
    td1 = (p3[0] - p4[0]) * (p1[1] - p3[1]) + (p3[1] - p4[1]) * (p3[0] - p1[0])
    td2 = (p3[0] - p4[0]) * (p2[1] - p3[1]) + (p3[1] - p4[1]) * (p3[0] - p2[0])
    return tc1 * tc2 < 0 and td1 * td2 < 0

def calc_vector_angle(line1_p1, line1_p2, line2_p1, line2_p2):
    """
    Calculate the and return the angle made by two line segments line1(p1)-(p2), line2(p1)-(p2)
    Args:
        line1_p1: (x,y)
        line1_p2: (x,y)
        line2_p1: (x,y)
        line2_p2: (x,y)

    Returns:
        angle : [0, 360)
    """
    u = np.array(line_vectorize(line1_p1, line1_p2))
    v = np.array(line_vectorize(line2_p1, line2_p2))
    i = np.inner(u, v)
    n = LA.norm(u) * LA.norm(v)
    c = i / n
    a = np.rad2deg(np.arccos(np.clip(c, -1.0, 1.0)))
    if u[0] * v[1] - u[1] * v[0] < 0:
        return a
    else:
        return 360 - a

def line_vectorize(point1, point2):
    """
    Args:
        point1: (x,y)
        point2: (x,y)

    Returns:
        The vector of intersecting the points with a line line(point1)-(point2)
    """
    a = point2[0] - point1[0]
    b = point2[1] - point1[1]
    return [a, b]
