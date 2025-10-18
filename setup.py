from setuptools import setup, find_packages

setup(
    name="flexmetric",
    version="0.5.5",
    author="Nikhil Lingadhal",
    description="A secure flexible Prometheus exporter for commands, databases, functions.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/nikhillingadhal1999/flexmetric",
    project_urls={
        "Homepage": "https://github.com/nikhillingadhal1999", 
        "Source": "https://github.com/nikhillingadhal1999/flexmetric",
        "Tracker": "https://github.com/nikhillingadhal1999/flexmetric/issues",
    },
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "prometheus_client",
        "PyYAML",
        "psutil",
        "setuptools",
        "wheel",
        "twine",
        "flask",
        "clickhouse-connect",
        "psycopg2-binary",
        "ollama"
    ],
    entry_points={
        "console_scripts": [
            "flexmetric = flexmetric.metric_process.prometheus_agent:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
