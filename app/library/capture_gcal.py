#!/usr/bin/env python3
import os
import time
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def get_cache_dir():
    cache_dir = (
        Path(os.getenv("XDG_CACHE_DIR", Path.home() / ".cache")) / "timeframe_chrome"
    )
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def crop(filename: str):
    im = Image.open(filename)
    left, top = 452, 129
    width, height = 540, 960
    im = im.crop((left, top, left + width, top + height))
    im.save(filename, "PNG")


options = Options()
for argument in [
    "--headless=new",
    "--no-sandbox",
    "--disable-gpu",
    "--hide-scrollbars",
    "--disable-extensions",
    "--window-size=992,1260",
    "--disable-web-security",
    f"--user-data-dir={get_cache_dir()}",
    "--allow-running-insecure-content",
    "--force-device-scale-factor=1",
    "--high-dpi-support=1",
    "--proxy-server='direct://'",
    "--proxy-bypass-list=*",
]:
    options.add_argument(argument)


driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()),
    options=options,
)

print("Getting page...")
driver.get("https://calendar.google.com/calendar/u/2/r/day")

if driver.find_elements(By.CSS_SELECTOR, "div#root") or driver.find_elements(
    By.CSS_SELECTOR, "main.main"
):
    print("Google Calendar requires login, please do it manually.")
    time.sleep(300)

driver.execute_script("document.body.style.zoom='180%'")

time.sleep(1)
for xpath in [
    "//div[@aria-label='Show side panel']",
    "//*[text()='Sorry, there was an error loading Google Tasks.']/../..",
]:
    if e := driver.find_elements(By.XPATH, xpath):
        driver.execute_script("arguments[0].style.visibility='hidden'", e[0])


# Main button, in case we need to contract the sidebar.
# elem = driver.find_element(By.CSS_SELECTOR, "div[aria-label='Main drawer']")
elem = driver.find_element(By.CSS_SELECTOR, "html")
elem.send_keys("t")
time.sleep(2)

filename = "/tmp/gcal_screenshot.png"
driver.save_screenshot(filename)
crop(filename)

driver.close()