import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="fluke_28x_dmm_util",
    version="0.3.4",
    description="Utility for interacting with Fluke 289 and 287 Series multimeters.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/N0ury/dmm_util",
    author="N0ury",
#    author_email="info@realpython.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
    ],
    packages=["fluke_28x_dmm_util"],
    install_requires=["pyserial"],
#    entry_points={
#        "console_scripts": [
#            "realpython=reader.__main__:main",
#        ]
#    },
    python_requires='>=3.10'
)
