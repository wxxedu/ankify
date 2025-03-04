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
        "requests==2.32.3",
        "markdown2==2.5.3",
        "pyyaml==6.0.2",
        "tqdm==4.67.1",
        "python-dotenv==1.0.1",
        "certifi==2025.1.31",
        "charset-normalizer==3.4.1",
        "idna==3.10",
        "pygments==2.19.1",
        "urllib3==2.3.0",
    ],
    entry_points={
        "console_scripts": [
            "ankify=ankify.main:main",
        ],
    },
    python_requires=">=3.6",
)
