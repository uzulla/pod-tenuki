from setuptools import setup, find_packages

setup(
    name="pod-tenuki",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.28.0",
        "google-cloud-speech>=2.17.0",
        "google-cloud-storage>=2.7.0",
        "openai>=1.0.0",
        "python-dotenv>=0.21.0",
        "pydub>=0.25.1",
        "tqdm>=4.64.1",
    ],
    entry_points={
        "console_scripts": [
            "pod-tenuki=pod_tenuki.main:main",
        ],
    },
)
