from setuptools import setup, find_packages


setup(
    name="sanicmin",
    version="1.0.3",
    packages=find_packages(),
    author="Infernox-Dev",
    description="A plugin for Sanic framework to minimize data transfer",
    long_description_content_type="text/markdown",
    url="https://github.com/infernox-dev/sanicmin",
    install_requires=[
        "htmlmin",
        "rcssmin",
        "rjsmin",
        "sanic",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
