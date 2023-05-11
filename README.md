# directory-crawlers
This repository contains the scraping of the businesses of each one of the states in individual folders.
It also has an installation guide with the necessary tools to set the environment and be able to scrape.

## Install the following tools for setup local enviroment:
1. Install Python 3.10.6 (AWS version)
2. Install required python dependencies, with pip or pip3 (python package manager system):

    - Scrapy:
        > pip install scrapy

        > pip install nltk

    - Selenium:
        > pip install selenium

    - Web driver:
        > pip install webdriver-manager
    - Pandas:
        > pip install pandas
    - Usadress:
        > pip install usaddress
    - Speach-recognition:
        > pip install SpeechRecognition
    - pydub para manipulación de audio:
        > pip install pydub

    - ffmepg drivers on OS:
        - MacOS:
            > brew install ffmpeg
        - Linux:
            > apt get install ffmpeg
3. Guide for scrapy installation:
    * https://docs.scrapy.org/en/latest/intro/install.html
    * Scraping example: https://oxylabs.io/blog/scrapy-web-scraping-tutorial
4. Guide for selenium installation:
    * https://pypi.org/project/selenium/
    * Scraping example: https://towardsdatascience.com/how-to-use-selenium-to-web-scrape-with-example-80f9b23a843a
5. Puppeteer is a Node.js library, therefore it can be installed by your npm package manager. Install nodejs v18.14.2 (AWS version):
    * npm i puppeteer
6. Guide for Puppeteer:
    * https://pptr.dev/
    * Scraping example: https://www.digitalocean.com/community/tutorials/how-to-scrape-a-website-using-node-js-and-puppeteer
7. Install ProtonVPN Client:
    * pip install protonvpn
    * Create free account on https://protonvpn.com/
    * Use the credentials on https://account.protonvpn.com/account for setup your client, not your user and password for login, they are diferents credentials.
