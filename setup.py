"""Setup file for the gator package."""
import setuptools

setuptools.setup(
    name='gator',
    version='1.0.0',
    description='Central dataset aggregator and content manager for sqrl planner.',
    packages=setuptools.find_packages(),
    python_requires='>=3.9',
)
