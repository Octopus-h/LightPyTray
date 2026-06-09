import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lightpytray",
    version="1.0.0",
    author="octopus-h",
    description="A pure ctypes Windows system tray library with zero dependencies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/octopus-h/lightpytray",
    packages=setuptools.find_packages(),
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Desktop Environment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",        # 根据你用的最低 Python 版本
    platforms=["Windows"],
)