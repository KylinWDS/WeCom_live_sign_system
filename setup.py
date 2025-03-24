from setuptools import setup, find_packages

def read_requirements(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="wecom_live_sign_system",
    version="0.1.0",
    description="企业微信直播签到系统",
    author="Kylin",
    author_email="kylin_wds@163.com",
    packages=['src', 'tools'],
    include_package_data=True,
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        "dev": read_requirements('requirements-dev.txt'),
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "wecom-live-sign=src.main:main",
            "wecom-live-sign-check=tools.env_checker:check_environment",
            "wecom-admin-reset=tools.admin_reset_tool:main",
            "wecom-live-sign-test=tools.test_runner:run_tests",
            "wecom-live-sign-clean=tools.cleaner:clean_environment",
            "wecom-live-sign-db=tools.db_manager:main",
            "wecom-live-sign-log=tools.log_viewer:main",
            "wecom-live-sign-backup=tools.backup_tool:main",
            "wecom-live-sign-update=tools.update_tool:main",
            "wecom-live-sign-check-db=tools.db_checker:check_database",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 