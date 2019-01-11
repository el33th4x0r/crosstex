#! /usr/bin/python3


from distutils.core import setup


classifiers = [ 'Development Status :: 5 - Production/Stable'
              , 'Intended Audience :: Science/Research'
              , 'License :: OSI Approved :: GNU General Public License v2 (GPLv2)'
              , 'Operating System :: MacOS :: MacOS X'
              , 'Operating System :: POSIX :: Linux'
              , 'Operating System :: Unix'
              ]

setup(name='CrossTex',
      version='0.9.dev',
      author='Kai Mast (maintainer)',
      author_email='crosstex@systems.cs.cornell.edu',
      packages=['crosstex'
               ,'crosstex.style'
               ],
      scripts=['bin/crosstex'],
      url='https://github.com/kaimast/crosstex',
      license='GPLv2',
      description='CrossTeX is a bibliography management tool',
      classifiers=classifiers,
      requires=['ply', 'argparse', 'importlib']
      )
