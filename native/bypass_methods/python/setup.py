from setuptools import setup, find_packages

setup(
    name="undownunlock",
    version="0.1.0",
    description="Python tools for the UndownUnlock DirectX hooking library",
    author="UndownUnlock Team",
    packages=find_packages(),
    install_requires=[
        # Read requirements from file
        line.strip()
        for line in open("requirements/requirements.txt")
        if not line.startswith("#") and line.strip()
    ],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
) 