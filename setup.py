from setuptools import setup, find_packages

setup(
    name='nutriapp',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'PySide6',
        'SQLAlchemy',
        'pandas',
        'numpy',
    ],
    entry_points={
        'console_scripts': [
            'nutriapp=src.main:run_application',
        ],
    },
    author='Manus',
    description='Sistema de Gestão Nutricional Desktop',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/your_username/nutriapp_desktop', # Substitua pelo seu repositório
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)


