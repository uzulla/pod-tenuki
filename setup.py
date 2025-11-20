from setuptools import setup, find_packages

setup(
    name="pod-tenuki",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.32.5",
        "google-cloud-speech>=2.34.0",
        "google-cloud-storage>=3.6.0",
        "openai>=2.8.1",
        "python-dotenv>=1.2.1",
        "pydub>=0.25.1",
        "tqdm>=4.67.1",
    ],
    entry_points={
        "console_scripts": [
            "pod-tenuki=pod_tenuki.main:main",
        ],
    },
)
