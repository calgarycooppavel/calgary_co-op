import json  
import time 
import os
import csv
from datetime import datetime
import re
from email.message import EmailMessage
import ssl
import smtplib
import shutil

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By  
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as ec 
from selenium.common.exceptions import TimeoutException  
from selenium.webdriver.common.keys import Keys 
import pandas as pd
import numpy as np
from supabase import create_client, Client

# Function to load configuration from a JSON file
def get_config():
    with open("config.json", "r") as file:
        config = json.load(file)
    return config

# Function to initialize and configure the Chrome WebDriver
def start_chrome():
    ruta = ChromeDriverManager().install()
    options = Options()
    user_agent = config['user_agent']

    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--start-maximized")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")  
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--no-sandbox")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--no-first-run")
    options.add_argument("--no-proxy-server")
    options.add_argument("--disable-blink-features-AutomationControlled")

    exp_opt = [
        "enable-automation",
        "ignore-certificate-errors",
        "enable-logging"
    ]
    options.add_experimental_option("excludeSwitches", exp_opt)

    prefs = {
        "profile.default_content_setting_values.notifications" : 2,
        "credentials_enable_service" : False
    }
    options.add_experimental_option("prefs", prefs)

    serv = Service(ruta)
    driver = webdriver.Chrome(service=serv, options=options)

    return driver

# Function to log in to Calgary Coop
def login(driver):
    driver.get("https://login.mycalgarycoop.com/?redirect=shoponline.calgarycoop.com%2Fcrowfoot%2Fssologin%3Fpath%3Dnull%26anonimousUserID%3D2618989")
    user_name = config['user_calgarycoop']
    user_input = wait.until(ec.presence_of_element_located((By.ID, 'okta-signin-username')))
    for i in user_name:
        user_input.send_keys(i)
        time.sleep(0.2)
    password = config['password_calgarycoop']
    password_input = wait.until(ec.presence_of_element_located((By.ID, 'okta-signin-password')))
    for i in password:
        password_input.send_keys(i)
        time.sleep(0.2)
    time.sleep(2)
    wait.until(ec.presence_of_element_located((By.ID, 'okta-signin-submit'))).click()
    time.sleep(3)
    try:
        wait.until(ec.presence_of_element_located((By.XPATH, '//*[@id="app"]/div/main/div/div/div[2]/button[3]/div/div'))).click()
        time.sleep(5)
    except:
        pass  
    time.sleep(5)
    try:
        wait.until(ec.element_to_be_clickable((By.CLASS_NAME, "u_ellipsis_container")))
        print('Login successfully')
    except:
        print('Wrong credentials')
        driver.quit()

# Function to select a pickup location
def select_pickup_location(pos, wait):
    wait.until(ec.element_to_be_clickable((By.CLASS_NAME, "u_ellipsis_container"))).click()
    time.sleep(2)
 
    css_se = 'compose[view="components/store-selector/templates/store-selector-list-item.html"]'
    locations = wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, css_se)))
    amount = len(locations)
    address = locations[pos].text
    locations[pos].find_element(By.CSS_SELECTOR, 'button').click()
    time.sleep(2)
    wait.until(ec.element_to_be_clickable((By.CLASS_NAME, 'store-select-start-btn'))).click()
    
    return amount, address

# Function to check if a brand exists in a text
def brand_in_text(brands, text):
    text = text.lower()  
    for brand in brands:
        pattern = rf'\b{re.escape(brand.lower())}\b' 
        if re.search(pattern, text):
            return brand  
    for brand in brands:
        if 'Department' in brand:
            return brand
    return ""    

# Function to append data to a CSV file
def append_to_csv(data, filename):
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        if not file_exists:
            writer.writerow(data.keys())
            
        rows = zip(*data.values())
        writer.writerows(rows)

# Function to extract product information from the website
def get_information_product(adddress, driver, wait):
    # Code for extracting product data from the website...
    url = driver.current_url
    time.sleep(1)
    if '#/' in url:
        url = url.replace('#/', '')
    time.sleep(1)
    wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button[ref = "categoryBtn"]'))).click()
    time.sleep(4)

    div_categories = wait.until(ec.presence_of_element_located((By.CLASS_NAME, 'categories-categories')))
    list_categories = div_categories.find_elements(By.CLASS_NAME, 'categories-category-header')
    
    for i ,category in enumerate(list_categories):
        if i in [10, 11, 12, 13, 14, 15, 16, 17]:
            continue
        category.click()
        time.sleep(3)
        try:
            subcategories = wait.until(ec.presence_of_all_elements_located((By.CLASS_NAME, 'pp-subcategory-item')))
        except TimeoutException :
                reboot(driver)
                
        for i in range(len(subcategories)):
            time.sleep(2)
            try:
                subcategories = wait.until(ec.presence_of_all_elements_located((By.CLASS_NAME, 'pp-subcategory-item')))
            except TimeoutException :
                reboot(driver)
                    
            subcategorie = subcategories[i].find_element(By.CLASS_NAME, 'pp-subcategory-link')
            subcategorie_text = subcategorie.text
            subcategorie.click()
            time.sleep(2)
              
            try:
                buttons_more = wait.until(ec.presence_of_all_elements_located((By.CLASS_NAME, 'filter-side-bar-more-btn')))
                for button in buttons_more:
                    button.click()
                    time.sleep(1)
            except:
                pass
            time.sleep(2)
            
            
            brand_con = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.filter-side-bar-filters-container.b_filter-Brands')))
            brands = brand_con.find_elements(By.CLASS_NAME, 'filter-side-bar-filter-name')
            numbers = brand_con.find_elements(By.CLASS_NAME, 'filter-side-bar-filter-btn')
            list_brands = []
            for brand in brands:
                title_brand = brand.get_attribute('title')
                if title_brand == '':
                    list_brands.append(brand.text)
                else:
                    list_brands.append(title_brand)
                num = 0
            for number in numbers:
                text_num = number.text.split('\n')[1].replace('(', '').replace(')', '')
                num += int(text_num)
     
                
            body = driver.find_element("tag name", "body")
            cont = 0
            while cont < 20:
                body.send_keys(Keys.PAGE_DOWN)  
                time.sleep(1) 
                products = wait.until(ec.presence_of_all_elements_located((By.CLASS_NAME, 'outer-product-container')))
                if len(products) >= num-10:
                    break
                cont += 1    
                
            data ={
                'title': [],
                'url': [], 
                'image': [],
                'current_price': [],
                'original_price': [],
                'on_sale' : [],
                'weight': [],
                'volume': [],
                'brand': [],
                'price_per_kg': [],
                'stock': [],
                'category': [],
                'subcategory': [],
                'store_name': [],
                'store' : [],
                'state' : [],
                'zip_code': [],
                'country': [],
                'scraping_date': []
                #'id':[]
                }
            for product in products:

                title = product.find_element(By.CLASS_NAME, 'pc-title').text
                data['title'].append(title)
                
                url_image = product.find_element(By.CSS_SELECTOR, '.pc-image.au-target').get_attribute('src')
                url_produt = f'{url}#/product/{url_image.split("/")[-1].split(".")[0]}'
                data['url'].append(url_produt)
                data['image'].append(url_image)
                
                current_price = product.find_element(By.CLASS_NAME, 'product-price').text.replace('$', '')
                try:
                    product.find_element(By.CSS_SELECTOR, '.au-target.pc-price-section.showing-discount')
                    if len(current_price.split()) == 1:
                        original_price = product.find_element(By.CSS_SELECTOR, '.au-target.discount-price.cross-off-price').text.replace('$', '')
                    else:
                        original_price = current_price.split(' ')[0]
                        current_price = current_price.split(' ')[1]     
                except:
                    original_price = current_price
                current_price = re.findall(r'\d+\.\d+|\d+', current_price)[0]
                original_price = re.findall(r'\d+\.\d+|\d+', original_price)[0]
                data['current_price'].append(float(current_price))
                data['original_price'].append(float(original_price))
                
                if current_price == original_price:
                    on_offer = False
                else :
                    on_offer = True
                data['on_sale'].append(on_offer)
                
                text_weight = product.find_elements(By.CLASS_NAME, 'pc-amount')
                weight = ''
                volume = ''
                price_per_kg = ''
                
                if len(text_weight) == 1:
                    text = text_weight[0].text
                    text_ar = text.split()
                    
                    if text_ar[1] == 'gr':
                        text_gr = text_ar[0]
                        if '.' in text_gr:
                            text_gr = text_gr.replace('.', '')
                        weight = f'0.{text_gr}'
                    if text_ar[1] == 'kg':
                        weight = text_ar[0]
                    if text_ar[1] == 'ml':
                        volume = text_ar[0]
                else:
                    text = text_weight[0].text
                    pattern = r'\d+(?:\.\d+)?(?:g|kg)'
                    matches = re.findall(pattern, text)[0]  
                    if matches:  
                        if matches[-2] == 'k':
                            weight = matches.replace('kg', '')  
                        else:
                            weight =f"0.{matches.replace('g', '')}"  
                        
                    pattern = r'\$(\d+(?:\.\d+)?)\s*/kg'
                    matches1 = re.findall(pattern, text)[0]
                    if matches1:
                        price_per_kg = matches1                 
                if weight != '':
                    weight = float(weight)
                data['weight'].append(weight)
                if volume != '':
                    volume = float(volume)
                data['volume'].append(volume)
                brand_ = brand_in_text(list_brands, title) 
                data['brand'].append(brand_)
                if price_per_kg == '' and current_price != '' and weight != '':
                    price_per_kg = round(1/float(weight)*float(current_price), 2)
                if price_per_kg != '':
                    price_per_kg = float(price_per_kg)
                data['price_per_kg'].append(price_per_kg)
                data['stock'].append('In stock')
               
                my_xpath = '//*[@id="main-content"]/router-view/div/div/product-display/section/div[1]/div[1]/span[1]/a'
                category_text = wait.until(ec.element_to_be_clickable((By.XPATH, my_xpath))).text
                data['category'].append(category_text)
                data['subcategory'].append(subcategorie_text)
                
                address_list = adddress.split("\n")
                store_name = address_list[0]
                data['store_name'].append(store_name)
                data['store'].append('CO-OP')
                data['state'].append('Alberta')
                if len(address_list) > 1:
                    list_code = address_list[1].split()[-2:]
                    zip_code = f'{list_code[0]} {list_code[1]}'
                else:
                    print('Problems getting the zip_code:')
                    print(adddress)
                    zip_code = ''
                data['zip_code'].append(zip_code)
                
                data['country'].append('Canada')
                date_=datetime.today().strftime('%b-%d-%Y')
                data['scraping_date'].append(date_)
                # id = f'{url_produt}-{date_}'
                # data['id'].append(id)
                
            print(f'Writing {len(products)} new records from: =>{subcategorie_text} =>{category_text} =>{store_name}')
            append_to_csv(data, 'calgary_data.csv')
            
            my_xpath = '//*[@id="main-content"]/router-view/div/div/product-display/section/div[1]/div[1]/span[1]/a'
            try:
                wait.until(ec.element_to_be_clickable((By.XPATH, my_xpath))).click()
            except TimeoutException :
                reboot(driver)
                
            time.sleep(2)
        try:
            wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button[ref = "categoryBtn"]'))).click()
        except TimeoutException :
            reboot(driver)
        time.sleep(2)
    try:
        wait.until(ec.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/header-container/header/div[2]/div/div[1]/a'))).click()
    except TimeoutException :
            reboot(driver)
    time.sleep(2)   

# Function to send an email with the extracted data
def send_email():
    email_sender = config['email_sender']
    password = config['password_app_gmail']
    email_reciver = config['email_reciver']
    
    subject = 'Scraping data'
    body = f"Scraping is complete as of {datetime.today().strftime('%b-%d-%Y')}"
    #file_path = "calgary_data.csv"  
    
    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_reciver
    em['Subject'] = subject
    em.set_content(body)
    
    # with open(file_path, "rb") as file:
    #     em.add_attachment(file.read(),
    #                       maintype="application",
    #                       subtype="octet-stream",
    #                       filename=file_path)
    
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(email_sender, password)
        smtp.sendmail(email_sender, email_reciver, em.as_string())

    print("✅ Email sent with attachment.")

# Function to restart the browser session and continue scraping
def reboot(driver):
    global cont_reboot
    # Close the current browser session
    driver.quit()
    if cont_reboot<3:
        cont_reboot +=1
        # Restart Chrome and initialize a new driver instance
        driver = start_chrome()
        wait = WebDriverWait(driver, 10)

        # Log in again
        login(driver)

        # Check if the data file exists and count unique store names
        if os.path.exists('calgary_data.csv'):
            df = pd.read_csv("calgary_data.csv")
            elementos_unicos = df['store_name'].nunique()
        else:
            elementos_unicos = 0  # If the file doesn't exist, set unique elements count to 0
            
        # Select the first pickup location
        amount, address = select_pickup_location(0, wait)

        # Iterate through available store locations, skipping already processed ones
        for i in range(elementos_unicos, amount - 1):
            _, address = select_pickup_location(i, wait)
            get_information_product(address, driver, wait)
            time.sleep(3)  # Pause to prevent overwhelming the server

        # Close the browser session after completion
        driver.quit()
 
    
def copy_supabase():
    SUPABASE_URL = config['supabese_url']
    SUPABASE_KEY = config['supabase_key']

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    csv_file_path = "calgary_data.csv"
    bucket_name = "data_calgary"  
    file_name_in_bucket = f"calgary_data_{datetime.today().strftime('%b-%d-%Y')}.csv" 

    with open(csv_file_path, "rb") as file:

        try:
            supabase.storage.from_(bucket_name).upload(file_name_in_bucket, file)
            os.remove('calgary_data.csv')
        except Exception as e:
            print(f"Ocurrió un error al subir el archivo: {e}")



def copy_table_supabase():

    SUPABASE_URL = "https://uhniskbuflofwspemjqo.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVobmlza2J1ZmxvZndzcGVtanFvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczOTcwNjM1NywiZXhwIjoyMDU1MjgyMzU3fQ.2gB9T6UdHIAnanRFYrMWq-yNteBoRQ3NXfZQiRHrygY"
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    csv_path = "calgary_data.csv"  
    df = pd.read_csv(csv_path)
    df = df.replace({np.nan: None})
    data = df.to_dict(orient="records")
    response = supabase.table("calgary_data").insert(data).execute()

    if "error" in response:
        print("Error al insertar datos:", response["error"])
    else:
        print("Datos insertados correctamente en Supabase.")





# Main execution block
if __name__ == "__main__":
    cont_reboot = 0
    config = get_config()
    driver = start_chrome()
    wait = WebDriverWait(driver, 10)
    
    login(driver)
    amount, address = select_pickup_location(0, wait)
    time.sleep(3)
    get_information_product(address, driver, wait)
    
    for i in range(amount-1):
        pos = i+1
        _, address = select_pickup_location(pos, wait)
        get_information_product(address, driver, wait)
        time.sleep(3)
    copy_table_supabase()     
    copy_supabase() 
    send_email()
    driver.quit()
