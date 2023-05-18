from setuptools import setup

setup(
    name='ppica_selenium_browser_manager',
    version='1.0.0',
    description='A package for managing web browser instances and a dictionary generator using Selenium',
    author='Pablo Picapietra',
    packages=['selenium_browser_manager'],
    install_requires=[
        'selenium',
        'typing',
        'SpeechRecognition',
        'pydub',
        'webdriver_manager',
        'undetected-chromedriver',
    ]
)
