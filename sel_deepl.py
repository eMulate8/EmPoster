import os.path
import re
import time

import win32gui
import psutil
import wmi
import pyautogui
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.action_chains import ActionChains


class MoreThanFiveLetters(object):
    """
    Check that length of text in element more than five
    """

    def __init__(self, browser):
        self.browser = browser

    def __call__(self, driver):
        element = BeautifulSoup(self.browser.page_source,
                                'lxml').find('div', attrs={'aria-labelledby': "translation-results-heading"})
        return len(element.getText()) > 5


def find_element_by_xpath(browser, xpath):
    """
    Searching for an element on a web page by xpath
    within twenty seconds, if found returns this element, if timeout returns None
    """
    try:
        element = WebDriverWait(browser, 20).until(
            expected_conditions.presence_of_element_located((By.XPATH, xpath))
        )
    except TimeoutException:
        element = None
    return element


def check_field(browser):
    """
    Searching an element (where the text to be translated is inserted) 
    on a web page using several xpaths
    """
    xpath_list = [
        '/html/body/div[4]/main/div[5]/div/div[2]/section[1]/div[3]/div[2]/textarea',
        '/html/body/div[3]/main/div[5]/div[1]/div[2]/section[1]/div[3]/div[2]/d-textarea/div',
        '/html/body/div[4]/main/div[5]/div[1]/div[2]/section[1]/div[3]/div[2]/d-textarea/div',
        '/html/body/div[3]/main/div[6]/div[1]/div[2]/section[1]/div[3]/div[2]/d-textarea/div',
        '/html/body/div[3]/main/div[8]/div[1]/div[2]/section[1]/div[3]/div[2]/d-textarea/div',        '/html/body/div[1]/div[1]/div[2]/div/div[1]/main/div[2]/nav/div/div[2]/div/div/div[1]/section/div/div[2]/div[1]/section/div/div[1]/d-textarea/div[1]/p',
        '/html/body/div[3]/main/div[7]/div[1]/div[2]/section[1]/div[3]/div[2]/d-textarea/div',        '/html/body/div[1]/div[1]/div[3]/div/div[1]/main/div[2]/nav/div/div[2]/div/div/div[1]/section/div/div[2]/div[1]/section/div/div[1]/d-textarea/div[1]',        '/html/body/div[1]/div[1]/div[2]/div/div[1]/main/div[2]/nav/div/div[2]/div/div/div[1]/section/div/div[2]/div[1]/section/div/div[1]/d-textarea/div[1]'
    ]
    for xpath in xpath_list:
        field = find_element_by_xpath(browser, xpath)
        if field is not None:
            return field
    return None


def past_and_grab_text(browser, text):
    """
    Translating text from english to russian using deepl translator and firefox browser

    :param browser: browser class instance
    :param text: text for translating
    :return: translated text
    """
    browser.get('https://www.deepl.com/translator#en/ru/')
    field = check_field(browser)

    action = ActionChains(browser)
    if not field:
        print('field is none')
        return None
    action.click(on_element=field)
    pyautogui.moveTo(x=150, y=350, duration=0.1)
    pyautogui.mouseDown()
    pyautogui.mouseUp()
    action.perform()
    pyautogui.write(text)
    WebDriverWait(browser, 30).until(MoreThanFiveLetters(browser))
    time.sleep(10)
    translate_element = BeautifulSoup(browser.page_source,
                                      'lxml').find('div', attrs={'aria-labelledby': "translation-results-heading"})

    if not translate_element:
        translate_element = BeautifulSoup(browser.page_source,
                                          'lxml').find('div', attrs={'aria-labelledby': "translation-target-heading"})
    if translate_element:
        translate_result = translate_element.get_text()
    else:
        translate_result = None

    return translate_result


def focus_firefox():
    """
    Set focus to firefox window
    """
    while True:
        if any(proc.name() == 'firefox.exe' for proc in psutil.process_iter()):
            break
        time.sleep(1)
    firefox = win32gui.FindWindow(None, 'Mozilla Firefox')
    if firefox:
        win32gui.SetForegroundWindow(firefox)
        win32gui.SetActiveWindow(firefox)


def exit_firefox():
    """
    Terminate firefox process
    """
    c = wmi.WMI()
    for proc in c.Win32_Process(name='firefox.exe'):
        try:
            proc.Terminate()
        except wmi.x_wmi as ex:
            print(f"Error terminating Firefox process: {ex}")
        finally:
            proc.Dispose()


def split_text(text):
    """
    Splitting original text to parts that no more than 4990 symbols
    because 5000 is max symbols for translate
    """
    chunks = []
    while len(text) > 4990:
        chunks.append(text[:4990])
        text = text[4990:]
    if len(text) > 0:
        chunks.append(text)
    return chunks


def norm_text(text):
    """
    Inserting deleted spaces between upper letters during translation
    """
    text = re.sub(r'([^\r\n\t\f\vА-ЯЁ])([А-ЯЁ])', r'\1 \2', text)
    text = re.sub(r'(\.)(\w)', r'\1 \2', text)
    return text


def translate(text):
    """
    Main function for translate, here creates browser object,
    translating cycle is stated and errors are checked
    """
    translation = ''
    options = Options()
    options.headless = False
    with webdriver.Firefox(options=options, service=Service(log_path=os.devnull,
                                                            executable_path=GeckoDriverManager().install())) as browser:
        for errors in range(5):
            focus_firefox()
            if text:
                text_chunks = split_text(text)
            else:
                break
            try:
                for chunk in text_chunks:
                    chunk_translation = past_and_grab_text(browser, chunk)
                    if chunk_translation:
                        translation += chunk_translation
                    else:
                        raise TypeError
                break
            except Exception as e:
                print('error ', errors)
                print(e)
        else:
            print('Translation failed')
    exit_firefox()
    return norm_text(translation)
