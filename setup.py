from distutils.core import setup

setup(name='pyscrapbook',
      version='0.1.0',
      description='Markdown notetaking program',
      author='Daniel Dunn',
      author_email='dannydunn@eternityforest.com',
      packages=['pyscrapbook'],

       install_requires=[
              'send2trash'
          ],

      entry_points={
          'console_scripts': [
              'scrapbook = pyscrapbook.__main__:main']})
