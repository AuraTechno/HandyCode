from setuptools import setup, find_packages

setup(
    name="handycode",
    version="2.3.1",
    author="AuraTechno",
    description="AI Code Assistant for DeepSeek",
    long_description="HandyCode - AI Code Assistant",
    long_description_content_type="text/markdown",
    url="https://github.com/AuraTechno/HandyCode",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=["requests>=2.28.0"],
    entry_points={
        "console_scripts": [
            "handycode=handycode.main:main",
            "hc=handycode.main:main",
        ],
    },
)