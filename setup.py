from setuptools import setup, find_packages

setup(
    name="handycode",
    version="2.1.0",
    author="AuraTechno",
    description="AI Code Assistant for DeepSeek - Claude Code alternative",
    long_description="HandyCode - AI Code Assistant for command line",
    long_description_content_type="text/markdown",
    url="https://github.com/AuraTechno/HandyCode",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "handycode=handycode.main:main",
            "hc=handycode.main:main",
        ],
    },
)