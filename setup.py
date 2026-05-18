from setuptools import setup, find_packages

setup(
    name="prompt-forge",
    version="1.0.0",
    description="Senior Dev Prompt Generator — turn rough task descriptions into expert-quality AI prompts",
    author="MONISMALIK1",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=["click>=8.0"],
    entry_points={
        "console_scripts": [
            "pf=prompt_forge.cli:main",
            "prompt-forge=prompt_forge.cli:main",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Programming Language :: Python :: 3",
    ],
)
