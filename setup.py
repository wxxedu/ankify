import setuptools

setuptools.setup(
    name="ankify",
    version="2.1.0",
    author="Xiuxuan Wang",
    author_email="xiuxuan.wang@u.nus.edu",
    description="Tool to import markdown flashcards to Anki",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/wxxedu/ankify",
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
        "pydantic==2.10.6",
        "pygments==2.19.1",
        "python-frontmatter==1.1.0",
        "asyncio==3.4.3",
        "aiohttp==3.11.13",
        "aiohappyeyeballs==2.5.0",
        "aiosignal==1.3.2",
        "annotated-types==0.7.0",
        "attrs==25.1.0",
        "certifi==2025.1.31",
        "charset-normalizer==3.4.1",
        "frozenlist==1.5.0",
        "idna==3.10",
        "multidict==6.1.0",
        "propcache==0.3.0",
        "pydantic_core==2.27.2",
        "typing_extensions==4.12.2",
        "urllib3==2.3.0",
        "yarl==1.18.3",
        "mcp==1.3.0"
    ],
    entry_points={
        "console_scripts": [
            "ankify=ankify.main:main",
        ],
    },
    python_requires=">=3.6",
)
