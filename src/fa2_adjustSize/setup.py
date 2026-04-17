from setuptools import setup, Extension
from Cython.Build import cythonize
import sys

def main():
    fa2util_path = None
    
    # Passed by meson
    for i, arg in enumerate(sys.argv):
        if arg.endswith('fa2util.pyx'):
            fa2util_path = sys.argv.pop(i)
            break
    
    if not fa2util_path:
        fa2util_path = 'src/fa2_adjustSize/fa2util.pyx'
    
    extensions = [
        Extension(
            name='fa2util',
            sources=[fa2util_path],
            extra_compile_args=['-O3', '-fopenmp'],
            extra_link_args=['-fopenmp'],
        )
    ]

    setup(
        ext_modules=cythonize(
            extensions,
            compiler_directives={
                'language_level': '3',
                'boundscheck': False,
                'wraparound': False,
                'cdivision': True,
                'initializedcheck': False,
                'nonecheck': False,
            },
        ),
        zip_safe=False,
    )

if __name__ == '__main__':
    main()