from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="brainboost_configuration_package",  # Replace with your desired package name
    version="0.1.0",
    author="Pablo Tomas Borda",
    author_email="pablotomasborda@gmail.com",
    description="A package for brainboost configuration management by default /brainboost/global.config",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/brainboost_configuration_package",  # Replace with your repository URL
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        # List your package dependencies here
    ],
)
