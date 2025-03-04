import setuptools

setuptools.setup(
    name="ankify",
    version="0.1.0",
    author="Xiuxuan Wang",
    author_email="xiuxuan.wang@u.nus.edu",
    description="Tool to import markdown flashcards to Anki",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/user/ankify",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "requests",
        "markdown2",
        "pyyaml",
        "tqdm",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "ankify=ankify.main:main",
        ],
    },
    python_requires=">=3.6",
)
