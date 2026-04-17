# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from cython.parallel cimport prange, threadid
from cython cimport view
cimport openmp
from libc.math cimport sqrt as csqrt

include "fa2util.py"


cdef void _apply_repulsion_parallel(
    double[:] x,
    double[:] y,
    double[:] mass,
    double[:] size,
    double[:, :] dx_accum,
    double[:, :] dy_accum,
    bint adjust_size,
    double coefficient,
) noexcept nogil:
    cdef Py_ssize_t i, j, node_count = x.shape[0]
    cdef int tid
    cdef double x_dist
    cdef double y_dist
    cdef double distance2
    cdef double distance
    cdef double factor
    cdef double mass_factor

    for i in prange(node_count, schedule="guided", nogil=True):
        tid = threadid()
        for j in range(i):
            x_dist = x[i] - x[j]
            y_dist = y[i] - y[j]
            mass_factor = mass[i] * mass[j]

            if adjust_size:
                distance = csqrt(x_dist * x_dist + y_dist * y_dist) - size[i] - size[j]
                if distance == 0:
                    continue
                if distance > 0:
                    factor = coefficient * mass_factor / distance / distance
                else:
                    factor = 100.0 * coefficient * mass_factor
            else:
                distance2 = x_dist * x_dist + y_dist * y_dist
                if distance2 == 0:
                    continue
                factor = coefficient * mass_factor / distance2

            dx_accum[tid, i] += x_dist * factor
            dy_accum[tid, i] += y_dist * factor
            dx_accum[tid, j] -= x_dist * factor
            dy_accum[tid, j] -= y_dist * factor


def apply_repulsion(nodes, adjustSize, coefficient):
    cdef Py_ssize_t node_count = len(nodes)
    cdef Py_ssize_t i
    cdef int thread_count
    cdef bint adjust_size = adjustSize
    cdef double coeff = coefficient
    cdef view.array x_buf
    cdef view.array y_buf
    cdef view.array mass_buf
    cdef view.array size_buf
    cdef view.array dx_accum_buf
    cdef view.array dy_accum_buf
    cdef double[:] x
    cdef double[:] y
    cdef double[:] mass
    cdef double[:] size
    cdef double[:, :] dx_accum
    cdef double[:, :] dy_accum

    if node_count < 2:
        return

    thread_count = openmp.omp_get_max_threads()

    x_buf = view.array(shape=(node_count,), itemsize=sizeof(double), format="d")
    y_buf = view.array(shape=(node_count,), itemsize=sizeof(double), format="d")
    mass_buf = view.array(shape=(node_count,), itemsize=sizeof(double), format="d")
    size_buf = view.array(shape=(node_count,), itemsize=sizeof(double), format="d")
    dx_accum_buf = view.array(shape=(thread_count, node_count), itemsize=sizeof(double), format="d")
    dy_accum_buf = view.array(shape=(thread_count, node_count), itemsize=sizeof(double), format="d")

    x = x_buf
    y = y_buf
    mass = mass_buf
    size = size_buf
    dx_accum = dx_accum_buf
    dy_accum = dy_accum_buf

    for i in range(node_count):
        x[i] = nodes[i].x
        y[i] = nodes[i].y
        mass[i] = nodes[i].mass
        size[i] = nodes[i].size

    for i in range(thread_count):
        for j in range(node_count):
            dx_accum[i, j] = 0.0
            dy_accum[i, j] = 0.0

    with nogil:
        _apply_repulsion_parallel(x, y, mass, size, dx_accum, dy_accum, adjust_size, coeff)

    for i in range(node_count):
        nodes[i].dx = 0.0
        nodes[i].dy = 0.0
        for j in range(thread_count):
            nodes[i].dx += dx_accum[j, i]
            nodes[i].dy += dy_accum[j, i]
