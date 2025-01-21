from setuptools import setup, find_packages

setup(
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={
        "opensubmarine": ["py.typed"],
        "opensubmarine.contracts.access.Ownable": ["*.pyi"],
    },
    zip_safe=False,  # Required for mypy to find py.typed files
)