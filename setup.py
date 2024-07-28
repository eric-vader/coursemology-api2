from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

setup(
    name='coursemology_api',
    version='0.1.0',
    description='Coursemology API',
    long_description=readme,
    install_requires=['requests', 'pandas', 'tqdm', 'tqdm-loggable']
)
