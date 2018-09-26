import os
from setuptools import setup, find_packages

VERSION = "0.1.0"

src_dir = os.path.dirname(__file__)


def read(filename):
    full_path = os.path.join(src_dir, filename)
    with open(full_path) as fd:
        return fd.read()


# cython requirements accessible from outside (cython+kivy does not work well)
requires_cython = 'Cython==0.26.1'
install_requires = [
    'python_version>="3.5"',
    'attrs',
    'click',
    'hx711',
    'RPi.GPIO',
    'PyYAML',
    'kivy==1.10.1',
]

tests_require = [
]

if __name__ == "__main__":
    setup(
        name="mixorama",
        version=VERSION,
        author="Aleksandr Bogdanov",
        author_email="alex@syn.im",
        license="none",
        url="https://github.com/synchrone/mix-o-rama",
        description="",
        long_description=read("README.md"),
        packages=find_packages(),
        install_requires=install_requires,
        tests_require=tests_require,
        entry_points='''
            [console_scripts]
            mixorama=mixorama.main:cli
        '''
    )
