from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="handycode",
    version="2.1.0",
    author="AuraTechno",
    author_email="your-email@example.com",
    description="AI Code Assistant for DeepSeek - Claude Code alternative",
    long_description=long_description,
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
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
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