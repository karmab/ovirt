from setuptools import setup

setup(name='ovirt',
      version='1.2.5',
      description='Ovirt utility',
      url='http://github.com/karmab/ovirt',
      author='Karim Boumedhel',
      author_email='karimboumedhel@gmail.com',
      license='GPL',
      scripts=['ovirt.py', 'foreman.py'],
      install_requires=[
          'pyparsing',
          'pyYAML',
          'ovirt-engine-sdk-python',
          'prettytable',
          'requests',
          'simplejson',
      ],
      zip_safe=False)
