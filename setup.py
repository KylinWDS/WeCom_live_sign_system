from setuptools import setup, find_packages

setup(
    name="wecom_live_sign_system",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.4.0",
        "SQLAlchemy>=2.0.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "pandas>=1.5.0",
        "openpyxl>=3.0.10",
        "matplotlib>=3.5.0",
        "pyecharts>=1.8.0",
        "loguru>=0.6.0"
    ],
    python_requires=">=3.8",
) 