from setuptools import setup, find_packages

setup(
    name='image-description-generator',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'streamlit',
        'transformers',
        'mistralai',
        'Pillow',
        'deepl',
        'pyperclip',
    ],
    entry_points={
        'console_scripts': [
            'image-description-generator=src.image_description:main',
        ],
    },
)
