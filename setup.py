from setuptools import setup, find_packages

setup(
    name="humanness-evaluator",
    version="0.1.0",
    description="Batch antibody humanness evaluation using BioPhiSkill and OASis",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pandas>=1.5.0",
        "openpyxl>=3.0.0",
    ],
)
