from os import path
from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))

with open(path.join(HERE, "VERSION"), encoding="utf-8") as f:
    VERSION = f.read().strip()

setup(author="Andrew Michaud",
      author_email="bots+isthisska@mail.andrewmichaud.com",

      entry_points={
          "console_scripts": ["isthisska_bot = isthisska_bot.__main__:main"]
      },

      install_requires=["backoff>=1.8.0", "botskeleton>=3.2.1", "bs4", "Pillow"],
      python_requires=">=3.6",

      license="BSD3",

      name="isthisska_bot",

      packages=find_packages(),

      url="https://github.com/alixnovosi/isthisska_bot",

      version=VERSION)
