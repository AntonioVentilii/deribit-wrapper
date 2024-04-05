from setuptools import find_packages, setup

setup(
    name='deribit_wrapper',
    version='0.3.0',
    packages=find_packages(),
    description='A Python wrapper for seamless integration with Deribit\'s trading API, offering easy access to '
                'market data, account management, and trading operations.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Antonio Ventilii',
    author_email='antonioventilii@gmail.com',
    license='MIT',
    install_requires=[
        'requests',
        'numpy',
        'pandas',
        'urllib3',
        'progressbar2',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    url='https://github.com/AntonioVentilii/deribit-wrapper',
    project_urls={
        'Source Code': 'https://github.com/AntonioVentilii/deribit-wrapper',
        'Issue Tracker': 'https://github.com/AntonioVentilii/deribit-wrapper/issues',
    },
    keywords='deribit api wrapper cryptocurrency trading',
    entry_points={
        'console_scripts': [
            # Define console scripts here if needed
        ],
    },
)
