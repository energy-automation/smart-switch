import re
import time
import datetime

import RPi.GPIO as GPIO

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Get todays date in a format suitable for the site
today = datetime.datetime.today()
today = today.strftime('%d.%m.%Y')

# The web adress where we can find the table with prices
entsoe_url = f"https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=false&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime={today}+00:00|CET|DAY&biddingZone.values=CTY|10YNL----------L!BZN|10YNL----------L&resolution.values=PT60M&dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)"

# Finds a substring in a string and cuts of everything before that occurrence.
def goto(haystack, needle):
    position = haystack.find(needle)

    if position == 0:
        return haystack

    return haystack[position:]
    
# Download and extract prices    
def retrieve_prices():
    # Create the automated browser object
    browser = webdriver.Chrome()

    # Have it go to the url annd return the entire content of the page
    browser.get(entsoe_url)
    html = browser.page_source

    # Write html content to disk for testing and debugging if needed. 
    with open('content.txt', 'w') as f:
        f.write(html)
        
    # And close the browser
    browser.quit()
    
        # Read the content of the file.
    with open('content.txt', 'r') as f:
        html = f.readlines()
    html = ''.join(html)
    html = html.replace('\n', '')

    # Find the start of the hours column
    html = goto(html, 'DayAheadPricesMongoEntity')
    
    # Define what we are looking for
    pattern = 'data-view-detail-link<\/span>"&gt;<\/span>(.*?)<span'
    matches = re.findall(pattern, html)

    # Display all the matches
    for m in matches:
        print(m)
    
    # Make sure there are exactly 24 prices
    assert(len(matches) == 24)
    
    # Return as numbers
    return [float(i) for i in matches]
    

if __name__ == '__main__':
    switch_pin = 40    # GPIO21
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(switch_pin, GPIO.OUT)

    old_day = -1
    old_hour = -1
    
    prices = None
    
    # Run forever
    while True:
        now = datetime.datetime.now()
        
        # New day? Download new prices
        if now.day != old_day:
            prices = retrieve_prices()
            old_day = now.day
            
        # New hour? Check if price is below average
        if now.hour != old_hour:
            average_price = sum(prices) / len(prices)
            if prices[now.hour] < average_price:
                print('Switch on')
                GPIO.output(switch_pin, GPIO.HIGH)
            else:
                print('Switch off') 
                GPIO.output(switch_pin, GPIO.LOW)                
            old_hour = now.hour
            
        # Sleep for a while  
        time.sleep(10)