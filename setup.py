import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dataroute",
    version="0.1.0",
    author="Alexander K.",
    author_email="ip387525@gmail.com",
    description="ETL platform with its own dtrt language for describing ETL data routes between different sources",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/1SKcode/dataroute",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)