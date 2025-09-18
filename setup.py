from setuptools import setup, find_packages
import os

# Get the directory containing this file
here = os.path.abspath(os.path.dirname(__file__))

# Read README
readme_path = os.path.join(here, "README.md")
try:
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "A comprehensive tool for analyzing Datadog usage costs and detecting anomalies"

# Read requirements
requirements_path = os.path.join(here, "requirements.txt")
try:
    with open(requirements_path, "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    # Fallback to hardcoded requirements if file not found
    requirements = [
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "plotly>=5.0.0",
        "flask>=2.0.0",
        "datadog-api-client>=2.0.0",
        "scikit-learn>=1.0.0",
        "scipy>=1.7.0",
        "statsmodels>=0.13.0",
        "click>=8.0.0",
        "pyyaml>=6.0",
        "python-dotenv>=0.19.0"
    ]

setup(
    name="datadog-cost-analyzer",
    version="1.0.0",
    author="OpenHands",
    author_email="openhands@all-hands.dev",
    description="A comprehensive tool for analyzing Datadog usage costs and detecting anomalies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/datadog-health/cost-optimization",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "datadog-cost-analyzer=datadog_cost_analyzer.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "datadog_cost_analyzer": ["templates/*", "static/*"],
    },
)