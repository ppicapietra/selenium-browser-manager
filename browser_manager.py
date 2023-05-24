from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys

from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException, ElementNotInteractableException, InvalidElementStateException

import re
import os
import time
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
    def EC(self):
        return EC

    @property
    def driver(self) -> webdriver.Chrome:
        return self._browser
    
    @property
    def wait(self) -> WebDriverWait:
        return self._wait
    
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

    def click(self, element_or_selector: Union[str, WebElement]):
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
                self._wait.until(lambda driver: element if element.is_displayed() and element.is_enabled() else False)
                element.click()
            except TimeoutException or ElementClickInterceptedException:
                self._browser.execute_script("arguments[0].click();", element)
                 
    def fill(self, element_or_selector: Union[str, WebElement], text_to_send: str):
        """type on the element specified by the given selector.

        Args:
            element_or_selector (Union[str, WebElement]): The selector string for the element or a WebElement where the text has to be entered.

        Raises:
            InvalidElementStateException: If the element is not writable.
            TypeError: If the element is not the correct type to receive text.
            NoSuchElementException: If the element can't be found.
            TimeoutException: If the element can't be found within timeout period.

        Returns:
            None
        """

        try:
            if isinstance(element_or_selector, str):
                selector_type = BrowserManager._get_selector_type(element_or_selector)
                element = self._wait.until(EC.element_to_be_clickable((selector_type, element_or_selector)))
                # put element in visible area
                self._browser.execute_script("arguments[0].scrollIntoView();", element)
                element.send_keys(text_to_send)
            else:
                element = element_or_selector
                self._browser.execute_script("arguments[0].scrollIntoView();", element)
                element.send_keys(text_to_send)

        except ElementNotInteractableException:
            raise TypeError(f"WebElement type is wrong. Type of WebElement selected: {type(element)}")
        except InvalidElementStateException:
            # element could no be filled
            raise InvalidElementStateException("Element is not receiving text inputs")
        
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

    def go(self, url: str) -> None:
        """
        Load the url on the current tab.

        Args:
            url (str): The url to load on the current tab

        Returns:
            None
        """
        self._browser.get(url)

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
            captcha_version (str, optional): The version of the reCAPTCHA to resolve. Defaults to "google-v2".

        Returns:
            bool: True if the reCAPTCHA was successfully resolved, False otherwise.

        Raises:
            None
        """
        # change timeout value and restore at the end
        original_timeout_value = self._timeout
        self.timeout = 1

        logging.info("Resolving captcha...")

        if captcha_version == 'google-v2':

            ###################################
            ######## GOOGLE CAPTCHA v2 ########
            ###################################
            
            # selectors
            # reCaptcha_checkbox_selector = '.ctp-checkbox-container input[type="checkbox"]' # cloudflare
            
            reCaptcha_checkbox_class_name = "recaptcha-checkbox-unchecked"
            reCaptcha_audio_button_id_name = "recaptcha-audio-button"
            audio_file_link_class_name = 'rc-audiochallenge-tdownload-link'

            reCaptcha_checkbox_selector = f'.{reCaptcha_checkbox_class_name}' # google
            reCaptcha_audio_button_selector = f"#{reCaptcha_audio_button_id_name}"
            reCaptcha_audio_button_alt_selector = '#recaptcha-anchor'
            audio_file_link_selector = f'.{audio_file_link_class_name}'
            reCaptcha_modal_header_selector = '.rc-doscaptcha-header-text'
            reCaptcha_answer_text_input_selector = '#audio-response'

            # start doing magic
            self._browser.switch_to.default_content()
            try:
                iframes_list = self.get("iframe", True)
            except TimeoutException:
                # there is no captcha
                return True
            
            reCaptcha_checkbox_triggered = False
            reCaptcha_iframe_founded = False
            # looking for a checkbox that triggers captcha
            for index, current_iframe in enumerate(reversed(iframes_list)):
                # we get "inside" the iframe
                try:
                    self._browser.switch_to.default_content()
                    self._browser.switch_to.frame(current_iframe)
                except Exception:
                    continue
                
                if reCaptcha_checkbox_class_name in self._browser.page_source:
                    try:
                        checkbox_trigger = self.get(reCaptcha_checkbox_selector)
                        checkbox_trigger.click_safe()
                        reCaptcha_checkbox_triggered = True
                    except Exception:
                        pass

            # here we assume we have a captcha modal opened
            # looking for an audio button in captcha
            if reCaptcha_checkbox_triggered:
                # safe waiting until reCaptcha modal opened be available to work with
                time.sleep(1)
            self._browser.switch_to.default_content()
            try:
                iframes_list = self.get("iframe", True)
            except TimeoutException:
                # there is no captcha
                return True
            # iterating over existing iframes
            for index, current_iframe in enumerate(reversed(iframes_list)):
                try:
                    self._browser.switch_to.default_content()
                    self._browser.switch_to.frame(current_iframe)
                except Exception:
                    continue
                    
                # is there an audio button option in this iframe?
                if not reCaptcha_audio_button_id_name in self._browser.page_source and not reCaptcha_audio_button_alt_selector in self._browser.page_source:
                    # try next iframe
                    continue
                else:
                    reCaptcha_iframe_founded = True
                    
                try:
                    # here we are "inside" the iframe founded as the captcha iframe
                    try:
                        audio_btn = self.get(reCaptcha_audio_button_selector)
                    except TimeoutException:
                        audio_btn = self.get(reCaptcha_audio_button_alt_selector)

                    audio_btn.click_safe()
                    break
                except Exception:
                    # There is no reCaptcha
                    pass
                
            if not reCaptcha_iframe_founded:
                # no reCatptcha iframe founded
                self.timeout = original_timeout_value
                logging.info(f"NO CAPTCHA DETECTED")
                return True
            
            # let's break it down those audios

            # loop from here
            # Download,save and convert to text audio captcha
            keep_resolving = True
            captcha_audio_link = None
            while keep_resolving:
                try:
                    captcha_audio_link = self.get(audio_file_link_selector)
                    captcha_audio_link_url = captcha_audio_link.get_attribute('href') if isinstance(captcha_audio_link, WebElement) else None
                except TimeoutException:
                    try:
                        ban_notification = self.get(reCaptcha_modal_header_selector)
                        if isinstance(ban_notification, WebElement):
                            banned_phrases = ["try again later", "vuelve a intentarlo"]
                            are_we_banned = any(phrase in ban_notification.text.lower() for phrase in banned_phrases)
                            if are_we_banned:
                                logging.info(f"Seems that you've been banned. Time to sit and wait")
                                self.timeout = original_timeout_value
                                return False
                    except TimeoutException:
                        pass
                    keep_resolving = False
                    break
                
                response = requests.get(captcha_audio_link_url, stream=True)

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
                    # recognize (convert from speech to text)
                    try:
                        audio_text_recognized = recognizer.recognize_google(audio_data)
                    except Exception:
                        self.timeout = original_timeout_value
                        return False
                    # Send text to input response
                    answer_text_input = self.get(reCaptcha_answer_text_input_selector)
                    answer_text_input.send_keys(audio_text_recognized)
                    answer_text_input.send_keys(Keys.ENTER)
                logging.info(f"Captcha resolved")
                try:
                    os.remove(f'{file_name}.mp3')
                except OSError:
                    pass
                try:
                    os.remove(f'{file_name}.wav')
                except OSError:
                    pass
                
                # safe waiting until captcha modal window disappear, if no more captchas are shown
                time.sleep(1)

                self._browser.switch_to.default_content()
                try:
                    iframes_list = self.get("iframe", True)
                except TimeoutException:
                    keep_resolving = False
                    break

                keep_resolving = False
                # looking for audio link element in existing iframes
                for index, current_iframe in enumerate(reversed(iframes_list)):
                    try:
                        self._browser.switch_to.default_content()
                        self._browser.switch_to.frame(current_iframe)
                    except Exception:
                        # there is no captcha
                        break
                    if audio_file_link_class_name in self._browser.page_source and self.is_element_interactable(audio_file_link_selector):
                        current_link_element = self.get(audio_file_link_selector)
                        if current_link_element != captcha_audio_link:
                            captcha_audio_link = current_link_element # ensuring the link element is not the last one
                            keep_resolving = True
                            break
                    else:
                        continue
                if not keep_resolving:
                    break
                
            # return to main context
            self._browser.switch_to.default_content()
            self.timeout = original_timeout_value
            return True
