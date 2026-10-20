"""Verbatim functions from commit bd8d01a; known misses/duplicates retained."""
import math

def distance(point1, point2):
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

def collisions(points, colliding_points):
    n = len(points)

    # Base case: If there are three or fewer points, calculate the perimeter of the triangle directly
    if n == 2:
        if distance(points[0], points[1]) <= 16:
            colliding_points.append((points[0], points[1]))
            return colliding_points
    elif n < 2:
        return colliding_points

    # Sort points by x-coordinate and y-coordinate
    points.sort(key=lambda p: (p[0], p[1]))

    # Divide points into two equal parts by x-coordinate
    left_half = points[:n // 2]
    right_half = points[n // 2:]

    median_line_x = (left_half[-1][0] + right_half[0][0]) / 2
    points_within_distance = [point for point in points if abs(point[0] - median_line_x) <= 8]

    for i in range(len(points_within_distance) - 1):
        if distance(points_within_distance[i], points_within_distance[i + 1]) <= 16:
            colliding_points.append((points_within_distance[i], points_within_distance[i + 1]))

    collisions(left_half, colliding_points)
    collisions(right_half, colliding_points)

    return colliding_points
