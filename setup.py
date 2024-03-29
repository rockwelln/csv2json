# pylint: skip-file
from setuptools import setup


with open("README.md", "r") as f:
    long_description = f.read()


setup(
    name="nx_csv2json",
    author="Norman Denayer",
    author_email="denayer.norman@gmail.com",
    description="turns csv entries to json entries based on csv headers",
    url="https://github.com/rockwelln/csv2json",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="0.3.0",
    license="MIT",
    keywords="csv JSON",
    python_requires=">=3.6",
    py_modules=["csv2json"],
    entry_points={"console_scripts": ["csv2json=csv2json:main"]},
    install_requires=["dataclasses; python_version < '3.7'"],
    extras_require={
        "dev": ["pytest", "pytest-cov", "black", "wheel", "twine"],
        "test": ["pytest", "pytest-cov"],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: Other/Proprietary License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
