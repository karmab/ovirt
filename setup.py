from setuptools import setup

setup(name='ovirt',
      version='1.2.12',
      description='Script to manage ovirt engine',
      url='http://github.com/karmab/ovirt',
      author='Karim Boumedhel',
      author_email='karimboumedhel@gmail.com',
      license='GPL',
      scripts=['ovirt.py'],
      install_requires=[
          'pyparsing',
          'pyYAML',
          'ovirt-engine-sdk-python<=4.0',
          'prettytable',
          'requests',
      ],
      zip_safe=False)
