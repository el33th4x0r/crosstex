from distutils.core import setup


classifiers = [ 'Development Status :: 5 - Production/Stable'
              , 'Intended Audience :: Science/Research'
              , 'License :: OSI Approved :: GNU General Public License v2 (GPLv2)'
              , 'Operating System :: MacOS :: MacOS X'
              , 'Operating System :: POSIX :: Linux'
              , 'Operating System :: Unix'
              ]

setup(name='CrossTex',
      version='0.8.dev',
      author='Robert Escriva (maintainer)',
      author_email='escriva@cs.cornell.edu',
      packages=['crosstex'
               ,'crosstex.style'
               ],
      scripts=['bin/crosstex'],
      url='http:///',
      license='GPLv2',
      description='CrossTeX is a bibliography management tool',
      classifiers=classifiers,
      requires=['ply', 'argparse', 'importlib']
      )
