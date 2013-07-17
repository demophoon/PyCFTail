from setuptools import setup
setup(
    name='PyCFTail',
    version='0.1',
    description="Stalk Campfire room without needing to join.",
    author='Michael J. Wheeler',
    author_email='mwheeler@mwheeler.net',
    license='MIT',
    url='https://github.com/mwheeler1982/PyCFTail',
    install_requires=[
        'keyring',
        'argparse >= 1.2',
        'pinder >= 1.0',
        'pytz',
    ],
    packages=['PyCFTail'],
    scripts=['PyCFTail/PyCFTail.py'],
)