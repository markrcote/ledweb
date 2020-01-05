import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ledweb",
    version="0.1",
    author="Mark Côté",
    description="Display various things on an LED panel",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/markrcote/ledweb",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
