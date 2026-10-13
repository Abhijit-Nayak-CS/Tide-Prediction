from setuptools import find_packages, setup
from typing import List

HYPHEN_E_DOT = '-e .'

def get_requirements(file_path: str) -> List[str]:
    """Requirements.txt se libraries read karne ke liye"""
    requirements = []
    with open(file_path) as file_obj:
        requirements = file_obj.readlines()
        requirements = [req.replace("\n", "") for req in requirements]
        if HYPHEN_E_DOT in requirements:
            requirements.remove(HYPHEN_E_DOT)
    return requirements

setup(
    name='chandipur_pxe_portal',
    version='1.0.0',
    author='Abhijit Nayak',
    author_email='abhijit@drdo.pxe.in',
    packages=find_packages(),
    install_requires=get_requirements('requirements.txt')
)