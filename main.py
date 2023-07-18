from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import numpy as np
import pandas as pd
from datetime import date
import os

# get prices on single page
def get_price_on_page(wd, price_li):
    listings = wd.find_elements(By.XPATH, "//li[@class='s-item s-item__pl-on-bottom']")

    for listing in listings:
        try:
            product_price = float(listing.find_element(By.XPATH, ".//span[@class='s-item__price']/span[1]").text.removeprefix("S$ ").replace(',', ''))
            price_li.append(product_price)
        except:
            continue

def scrape_product_data(wd, product_name, csv_path):
    # wait for searchbar to load then search for product
    WebDriverWait(wd, 20).until(
    EC.visibility_of_element_located(
        (By.XPATH, "//input[@class='gh-tb ui-autocomplete-input']")
        )
    )
    searchbar = wd.find_element(By.XPATH, "//input[@class='gh-tb ui-autocomplete-input']")
    searchbar.clear()
    searchbar.send_keys(product_name)
    wd.find_element(By.ID, "gh-btn").click()

    # Update product settings to brand new and non-auction
    WebDriverWait(wd, 20).until(
    EC.visibility_of_element_located(
        (By.XPATH, "//ul[@class='fake-tabs__items']")
        )
    )
    wd.find_element(By.XPATH, "//ul[@class='fake-tabs__items']/li[3]").click()

    WebDriverWait(wd, 20).until(
    EC.visibility_of_element_located(
        (By.XPATH, "//div[@class='srp-controls__resize-display']/span[1]/button")
        )
    )
    wd.find_element(By.XPATH, "//div[@class='srp-controls__resize-display']/span[1]/button").click()
    wd.find_element(By.XPATH, "//div[@class='srp-controls__resize-display']//ul[@id='s0-53-17-5-4[0]-71[1]-16-content-menu']/li[2]").click()

    # Get price on single page 
    price_li = []
    num_pgs = 1

    # get prices per page for num_pgs
    action = ActionChains(wd)
    for _ in range(0, num_pgs):
        next_button = wd.find_element(By.XPATH, "//a[@class='pagination__next icon-link']")
        get_price_on_page(wd, price_li)
        action.move_to_element(next_button).click().perform()

    # remove outliers
    q1 = np.percentile(price_li, 25, method='midpoint')
    q3 = np.percentile(price_li, 75, method='midpoint')
    iqr = q3 - q1
    lower = q1 - 1.5*iqr
    upper = q3 + 1.5*iqr

    filtered_price_li = list(filter(lambda x: (x>=lower and x<=upper), price_li))

    # calculate avergae price
    avg_price = round(sum(filtered_price_li) / len(filtered_price_li), 2)

    # read existing csv, append new info and save csv
    day = date.today().strftime("%Y-%m-%d")
    try:
        df = pd.read_csv(csv_path)
    except:
        df = pd.DataFrame(columns=['date', 'price'])

    if day in df['date'].values:            
        df.loc[df["date"] == day] = [day, avg_price]
    else:
        df.loc[len(df)] =  [day, avg_price]

    df.to_csv(csv_path, index=False)

    print("data saved to ", csv_path, "!")


# ebay url
ebay_url = "https://www.ebay.com.sg/"

# instantiate driver
wd = webdriver.Chrome()
wd.get(ebay_url)

# settings - change these
product_names = ["vstar universe booster box",
                 "pokemon 151 booster box",
                 "vmax climax booster box"
                 ]
results_dir = 'results'

for product_name in product_names:
    csv_path = os.path.join(results_dir, product_name + '.csv')
    scrape_product_data(wd, product_name, csv_path)

