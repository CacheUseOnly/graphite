from setuptools import setup, Extension
from Cython.Build import cythonize
import sys

def main():
    fa2util_path = None
    
    # Passed by meson
    for i, arg in enumerate(sys.argv):
        if arg.endswith('fa2util.py'):
            fa2util_path = sys.argv.pop(i)
            break
    
    if not fa2util_path:
        fa2util_path = 'src/fa2_adjustSize/fa2util.py'
    
    extensions = [
        Extension(
            name='fa2util',
            sources=[fa2util_path],
        )
    ]

    setup(
        ext_modules=cythonize(extensions),
        zip_safe=False,
    )

if __name__ == '__main__':
    main()