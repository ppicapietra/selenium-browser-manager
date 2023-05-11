from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys

from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException, ElementNotInteractableException

import re
import os
import random
import requests
import subprocess
import logging
import speech_recognition as speechRecognition
import undetected_chromedriver as webdriver

from typing import Union, Dict, Any

class BrowserManager:
    
    def __init__(self, initial_url, config:Dict[str, Any]):
        """
        Initializes a web browser instance with specified configurations.

        Parameters:
        -----------
        initial_url: A string representing the URL to be loaded when the browser is launched and in every new tab.
        config: dict
            A dictionary of configurations to be applied to the browser instance. It can contain the following keys:
            - "window": list. Arguments to be passed to the browser instance when it is initialized.
            - "headless": boolean. headless running mode
            - "timeout": int. Value representing the maximum amount of time to wait for an event to occurs (in seconds).

        Returns:
        --------
        None

        """
        # Define options for browser initialization

        self._initial_url = initial_url

        self._options = webdriver.ChromeOptions()

        ## browser props
        if config is not None:
            # browser instance params
            window_props = config.get('window', None)
            if window_props:
                for arg in window_props:
                    self._options.add_argument(arg)
            # stablish general preferences to improve scrapping
            self._options.add_argument('--lang=en-US')
            self._options.add_argument('--blink-settings=imagesEnabled=false') # don't load images. Faster results
            self._options.add_argument('--disable-popup-blocking') # allow new tabs
            self._options.add_argument('--no-sandbox')
            self._options.add_argument('--disable-dev-shm-usage')
            self._options.add_argument('--disable-extensions')
            self._options.add_argument('--disable-gpu')
            self._options.add_argument('--disable-setuid-sandbox')
            self._options.add_argument('--disable-web-security')
            self._options.add_argument('--ignore-certificate-errors')
            self._options.add_argument('--disable-infobars')
            self._options.add_argument('--window-size=1920,1080')
            self._options.add_argument('--start-maximized')
            self._options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36')
            
            # config: headless
            if 'headless' in config and config['headless']:
                self._options.add_argument('--headless')

            ## main config
            self._browser = webdriver.Chrome(options=self._options)

            # extra browser configurations to avoid selenium detection
            self._browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
            
            # config: time to wait before trigger timeoutException
            default_timeout = 30
            if "timeout" in config:
                self._timeout = config.get("timeout", default_timeout)
     
        ## auxiliar objects
        # wait object
        self._wait = WebDriverWait(self._browser, self._timeout)
        # previous tab handler
        self._previous_tab_handler = None

    
    # statics methods

    @staticmethod
    def _get_selector_type(selector_string: str):
        css_regex = re.compile(r"^\S") # Verify if the selector starts with a non-space character
        xpath_regex = re.compile(r"^//") # Verify if the selector starts with "//"

        if xpath_regex.search(selector_string):
            return By.XPATH
        elif css_regex.search(selector_string):
            return By.CSS_SELECTOR
            
    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        if isinstance(value, int):
            self._timeout = value
            self._wait = WebDriverWait(self._browser, self._timeout)
        else:
            raise ValueError("timeout must be a int value")
        
    # instance methods

    ## public methods
    def get_webdriver_instance(self) -> webdriver.Chrome:
        """
        Returns the webdriver.Chrome object associated with the class instance.
        
        Returns:
            webdriver.Chrome: The webdriver.Chrome object associated with the class instance.
        """
        return self._browser

    def close_current_tab(self):
        self._browser.close()
    
    def history(self, steps: int):
        """
        Move the WebDriver instance through the browser history by the specified number of steps.
        
        Args:
            steps (int): The number of steps to move in the browser history. If the value is positive, 
                         the WebDriver instance will move forward through the history; if it is negative, 
                         the WebDriver instance will move backward through the history.
        Raises:
            TypeError: If steps is not an integer.
        """
        if not isinstance(steps, int):
            raise TypeError('steps must be an integer')
        
        self._browser.execute_script(f'window.history.go({steps})') 

    def click_on(self, element_or_selector: Union[str, WebElement]):
        """Click on the element specified by the given selector.

        Args:
            element_or_selector (Union[str, WebElement]): The selector string for the element to be clicked or a WebElement to be clicked.

        Raises:
            ElementClickInterceptedException: If the element is not clickable.

        Returns:
            None
        """

        if isinstance(element_or_selector, str):
            selector_type = BrowserManager._get_selector_type(element_or_selector)

            try:
                element = self._wait.until(EC.element_to_be_clickable((selector_type, element_or_selector)))
                # put element in visible area
                self._browser.execute_script("arguments[0].scrollIntoView();", element)
                element.click()
            except ElementClickInterceptedException:
                # something is covering our element
                element = self.get(element_or_selector)
                if isinstance(element, WebElement):
                    self._browser.execute_script("arguments[0].click();", element)
                else:
                    raise TypeError(f"Expected WebElement but got {type(element)}")
        else:
            element = element_or_selector
            try:
                self._browser.execute_script("arguments[0].scrollIntoView();", element)
                
                # check if we have to do something with the target attribute
                if self._force_links_target and element.tag_name == "a" and self._force_links_target == "_blank":
                    new_tab_on_click = True
                element.click()
            except ElementClickInterceptedException:
                self._browser.execute_script("arguments[0].click();", element)

            # finally, if we open a new tab with current config, go to the new tab
            if new_tab_on_click:
                self._switch_to_new_window()

    def get(self, selector: str, results_in_list: bool = False) -> Union[WebElement, list]:
        """
        Finds and returns the element that matches the given selector (if only one matched) or a collection of them.

        Args:
            selector: A string representing the selector to use to find the element.
            results_in_list: A boolean that indicates if results have to be always in a list even when just one element is founded.

        Returns:
            The WebElement that matches the given selector or a list of WebElements if multiple are found.

        Raises:
            TimeoutException: If the element is not found within the specified timeout period.
        """
        selector_type = BrowserManager._get_selector_type(selector)

        try:
            elements = self._wait.until(EC.presence_of_all_elements_located(
                (selector_type, selector)))
            total_matched = len(elements)
            if total_matched == 1 and not results_in_list:
                return elements[0]
            elif total_matched > 1:
                return elements
        except TimeoutException:
            logging.info(f"Element with selector {selector} not founded within timeout period")
            raise TimeoutException
    
    def new_tab(self, url = None):
        """
        Opens a new tab in the browser with the initial URL provided in the `BrowserManager`
        instance and switches to the newly created tab, closing the current tab later.

        Returns:
            None
        """

        # Open a new tab with the specified URL
        url_aux = self._initial_url if url == None else url
        self._browser.execute_script("window.open('" + url_aux + "');")

        # Switch to the context of the new tab
        self._browser.switch_to.window(self._browser.window_handles[-1])

        # Get the current window
        current_window_tab_handle = self._browser.current_window_handle

        # Close all tabs except for the current one
        for window_tab_handle in self._browser.window_handles:
            if window_tab_handle != current_window_tab_handle:
                self._browser.switch_to.window(window_tab_handle)
                self._browser.close()

        # Switch to the context of the main window
        self._browser.switch_to.window(current_window_tab_handle)

        return

   
        """
        Executes some string-supplied JS code on the current page of the browser instance.

        Returns:
            None
        """

        # Execute supplied JS code
        self._browser.execute_script(script)

    def switch_to_tab(self, tab_id:Union[str, int]):
        """
        Switches to tab on the browser instance.

        Args:
            tab_id (Union[str,int]): The index of the tab on window_handles list or window_handler

        Returns:
            None
        """

        # Switch to the context of the new tab
        try:
            if isinstance(tab_id, int):
                self._browser.switch_to.window(self._browser.window_handles[tab_id])
            else:
                self._browser.switch_to.window(tab_id)
        except:
            raise Exception("Identificador no existente o fuera de los límites")

        return
    
    def is_element_interactable(self, selector: str, timeout: int = None) -> bool:
        """
        Checks if the element identified by the given selector is visible and interactable.

        Args:
            selector: A string representing the selector to use to find the element.
            timeout: A custom timeout value.

        Returns:
            True if the element is visible and interactable, False otherwise.
        """
        original_timeout = self._timeout
        if timeout:
            self.timeout = timeout
        selector_type = BrowserManager._get_selector_type(selector)
        try:
            element = self._wait.until(EC.visibility_of_element_located((selector_type, selector)))
            is_interactable = element.is_displayed() and element.is_enabled()
        except TimeoutException:
            is_interactable = False
        finally:
            self.timeout = original_timeout
        return is_interactable

    def wait_until_element_has_gone(self, selector: str, timeout: int = None) -> None:
         """
        returns the control to caller when element is not present

        Args:
            selector: A string representing the selector to use to find the element.
            timeout: A custom timeout value.

        Returns:
            None

        Raises:
            TimeoutException: If the element is not removed within the specified timeout period.
        """
         original_timeout = self._timeout
         if timeout:
            self.timeout = timeout
         selector_type = BrowserManager._get_selector_type(selector)
         try:
            self._wait.until_not(EC.presence_of_element_located(
               (selector_type, selector)))
            self.timeout = original_timeout
         except TimeoutException:
             self.timeout = original_timeout
             raise TimeoutException      

    def resolveCaptcha(self, captcha_version: str="google-v2") -> bool:
        """
        Resolves a reCAPTCHA on the current page.

        Args:
            captcha_version (str, optional): The version of the reCAPTCHA to resolve. Defaults to "V2".

        Returns:
            bool: True if the reCAPTCHA was successfully resolved, False otherwise.

        Raises:
            None
        """

        if captcha_version == 'V2':

            ############################
            ######## CAPTCHA v2 ########
            ############################
            
            iframes_list = self.get("iframe")
            iframes_length = len(iframes_list)

            if iframes_length > 0: # if there are iframes to switch later
                audio_btn_index = -1
                for index in range(iframes_length-1, -1, -1):
                    self._browser.switch_to.default_content() # we asure that we are in the main context
                    iframes_list = self.get("iframe")
                    current_iframe = iframes_list[index]
                    self._browser.switch_to.frame(current_iframe)
                    try:
                        audio_btn = self.get("#recaptcha-audio-button") or self.get("#recaptcha-anchor")
                        audio_btn.click()
                        # audioBtnFound = True
                        audio_btn_index = index
                        break
                    except Exception:
                        logging.info(f"NO CAPTCHA DETECTED")
                        return True
                    
                # Download,save and convert to text audio captcha
                captcha_audio_link = ""
                try:
                    captcha_audio_link = self.get(".rc-audiochallenge-tdownload-link").get_attribute('href')
                    logging.info("getting captcha audio file...")
                except TimeoutException:
                    ban_notification = self.get(".rc-doscaptcha-header-text")
                    if isinstance(ban_notification, WebElement):
                        banned_phrases = ["try again later", "vuelve a intentarlo"]
                        are_we_banned = any(phrase in ban_notification.text.lower() for phrase in banned_phrases)
                        if are_we_banned:
                            logging.info(f"Seems that you've been banned. Time to sit and wait")
                            return False
                    
                response = requests.get(captcha_audio_link, stream=True)

                # save the audio file
                file_name = f"bm_captcha_{random.randint(11111, 99999)}"
                with open(f'{file_name}.mp3', "wb") as handle:
                    for data in response.iter_content():
                        handle.write(data)

                recognizer = speechRecognition.Recognizer()

                # we need audio file on wav format
                subprocess.run(['ffmpeg', '-i', f'{file_name}.mp3', f'{file_name}.wav'], capture_output=True, text=True, input="y")

                # open the file
                with speechRecognition.AudioFile(f'{file_name}.wav') as source:
                    # listen for the data (load audio to memory)
                    audio_data = recognizer.record(source)
                    try:
                    # recognize (convert from speech to text)
                        captcha_text_recognized = recognizer.recognize_google(audio_data)
                    except Exception:
                        return False
                    # Send text to input response
                    self._browser.switch_to.default_content()
                    iframes_list = self.get("iframe")
                    current_iframe = iframes_list[audio_btn_index]
                    self._browser.switch_to.frame(current_iframe)
                    recognized_text_input = self.get("#audio-response")
                    recognized_text_input.send_keys(captcha_text_recognized)
                    recognized_text_input.send_keys(Keys.ENTER)
                logging.info("Deleting temporal files...")
                try:
                    os.remove(f'{file_name}.mp3')
                except OSError:
                    logging.info(f"Try to delete file but it doesn't exist")
                try:
                    os.remove(f'{file_name}.wav')
                except OSError:
                    logging.info(f"Try to delete file but it doesn't exist")
                
                # return to main context
                self._browser.switch_to.default_content()
                logging.info(f"Captcha resolved")
                return True