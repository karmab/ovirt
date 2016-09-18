from setuptools import setup

setup(name='ovirt',
      version='1.2.11',
      description='Script to manage ovirt engine',
      url='http://github.com/karmab/ovirt',
      author='Karim Boumedhel',
      author_email='karimboumedhel@gmail.com',
      license='GPL',
      scripts=['ovirt.py'],
      install_requires=[
          'pyparsing',
          'pyYAML',
          'ovirt-engine-sdk-python',
          'prettytable',
          'requests',
      ],
      zip_safe=False)
