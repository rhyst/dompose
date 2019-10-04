from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='dompose',
    version='0.0.1',
    description='A docker-compose wrapper. Compose your docker-compose files.', 
    long_description=long_description, 
    long_description_content_type='text/markdown',
    url='https://github.com/rhyst/dompose',
    author='Rhys Tyers',
    author_email='',
    classifiers=[ 
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3.7',
    ],
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    python_requires='>=3.7',
    install_requires=['pyyaml','python-dotenv'],
    entry_points={
        'console_scripts': [
            'dompose=dompose:main',
        ],
    }
)