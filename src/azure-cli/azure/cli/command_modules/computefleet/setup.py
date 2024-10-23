from setuptools import setup, find_packages

setup(
    name='azure-cli-computefleet',
    version='1.0.0',
    description='Microsoft Azure Command-Line Tools Compute Fleet Module',
    author='Your Name',
    author_email='rahuls@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'azure-cli-core',
        'azure-cli',
    ],
    entry_points={
        'console_scripts': [
            'azext_computefleet=azext_computefleet.__main__:main',
        ],
    },
)