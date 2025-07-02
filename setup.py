from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.readlines()

setup(
    name="jetraw-tools",
    version="0.7.3",
    python_requires=">3.8",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    author="Santiago Cano-Muniz",
    author_email="santiago.cano-muniz@unibas.ch",
    description="A collection of tools and helpers to work with the JetRaw compression libraries.",
    url="https://github.com/phisanti/jetraw_tools",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "jetraw-tools=jetraw_tools.main:app",
        ],
    },
)
