""" Contains triangle strip generation functions for GeometrySegment. """

from typing import List, Tuple
from copy import deepcopy
from .msh_model import *

def create_models_triangle_strips(models: List[Model]) -> List[Model]:
    """ Create the triangle strips for a list of models geometry. """

    for model in models:
        if model.geometry is not None:
            for segment in model.geometry:
                segment.triangle_strips = create_triangle_strips(segment.triangles)

    return models

def create_triangle_strips(segment_triangles: List[List[int]]) -> List[List[int]]:
    """ Create the triangle strips for a list of triangles. """

    triangles = deepcopy(segment_triangles)
    strips: List[List[int]] = []

    # The general idea here is we loop based off if 'triangles' is empty or not.
    #
    # For each iteration of the loop we create a new strip starting from the first
    # triangle still in 'triangles'.
    #
    # Then we loop, attempting to find a triangle to add the strip each time. If we
    # find one then we continue the loop, else we break out of it and append the
    # created strip.

    def create_strip() -> List[int]:
        strip: List[int] = [triangles[0][0],
                            triangles[0][1],
                            triangles[0][2]]
        strip_head: Tuple[int, int] = (strip[1], strip[2])

        triangles.remove(triangles[0])

        while True:
            def find_next_vertex():
                nonlocal triangles

                even: bool = len(strip) % 2 == 0

                for tri, edge, last_vertex in iterate_triangle_edges_last_vertex(triangles, even):
                    if edge == strip_head:
                        triangles.remove(tri)
                        return last_vertex

                return None

            next_vertex: int = find_next_vertex()

            if next_vertex is None:
                break

            strip.append(next_vertex)
            strip_head = (strip_head[1], next_vertex)

        return strip

    while triangles:
        strips.append(create_strip())

    return strips

def iterate_triangle_edges_last_vertex(triangles: List[List[int]], even: bool):
    """ Generator for iterating through the of each triangle in a list edges.
        Yields (triangle, edge, last_vertex). """

    if even:
        for tri in triangles:
            yield tri, (tri[0], tri[1]), tri[2]
            yield tri, (tri[0], tri[2]), tri[1]
            yield tri, (tri[1], tri[2]), tri[0]
    else:
        for tri in triangles:
            yield tri, (tri[1], tri[0]), tri[2]
            yield tri, (tri[2], tri[0]), tri[1]
            yield tri, (tri[2], tri[1]), tri[0]
