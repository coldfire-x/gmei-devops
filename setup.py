from distutils.core import setup

setup(name='gmei',
      version='0.0.1',
      description='gmei internal tool',
      author='Pengfei Xue',
      author_email='pengphy@gmail.com',
      url='https://github.com/pengfei-xue/gmei-devops/',
      platforms=['any'],
      scripts=['bin/gmei'],
      packages=['gmei', 'gmei.tools'],
      install_requires=[
          'colorama',
      ])
