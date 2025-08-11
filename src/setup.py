from setuptools import setup, find_packages
import os

# Read the README file
readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = "PrimeMinister - AI Council Decision System"

# Read requirements
requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
with open(requirements_path, 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="primeminister",
    version="1.0.0",
    author="Eric Benner",
    author_email="ebennerit@gmail.com",
    description="An AI CLI tool that uses a council of AI personalities to provide well-rounded advice",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eb3095/primeminister",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "primeminister=primeminister.cli:main",
            "pm=primeminister.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "primeminister": ["config.json"],
    },
    keywords="ai, cli, decision-making, openai, gpt, council, advice",
    project_urls={
        "Bug Reports": "https://github.com/eb3095/primeminister/issues",
        "Source": "https://github.com/eb3095/primeminister",
        "Documentation": "https://github.com/eb3095/primeminister/blob/main/README.md",
    },
)
