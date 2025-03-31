from setuptools import find_packages, setup

setup(
    name="folio",
    version="0.1.0",
    description="Portfolio Dashboard",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=2.2.1",
        "numpy>=1.26.4",
        "scikit-learn>=1.4.0",
        "xgboost>=2.0.3",
        "requests>=2.31.0",
        "PyYAML>=6.0.1",
        "tabulate>=0.9.0",
        "ta>=0.11.0",
        "mlflow>=2.21.2",
        "shap>=0.47.0",
        "matplotlib>=3.10.1",
        "tqdm>=4.65.0",
        "ruff>=0.3.3",
        "yfinance>=0.2.37",
        "dash>=2.14.2",
        "dash-bootstrap-components>=1.5.0",
        "plotly>=5.19.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "folio=folio.__main__:main",
        ],
    },
)
