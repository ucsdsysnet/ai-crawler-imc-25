from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
import time
import json
from urllib.parse import urlparse
import pandas as pd


def normalize_url(url):
    parsed_url = urlparse(url)
    # Remove 'www.' prefix from netloc if it exists
    netloc = parsed_url.netloc
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    
    # Use the netloc and path to normalize
    return netloc, parsed_url.path.rstrip('/')

def are_same_website(url1, url2):
    norm_url1 = normalize_url(url1)
    norm_url2 = normalize_url(url2)
    return norm_url1 == norm_url2

def is_this_file_cloudflare_block(raw_html):
    CLOUDFLARE_STRINGS = ['Ray ID', 'cRay']

    # if ".html" not in filename:
    #     return False
        
    for s in CLOUDFLARE_STRINGS:
        if s in raw_html and 'Cloudflare' in raw_html:
            return True
        elif s in raw_html:
            return True
    
    return False

def html_cf_block_or_challenge(raw_html):
    if is_this_file_cloudflare_block(raw_html):
        if 'dn-cgi/styles/cf.errors.css' in raw_html:
            return "BLOCK"
        elif 'cRay' in raw_html:
            return "CHALLENGE"
        else:
            return "BLOCK"
    else:
        return "NA"


responses = {}
websites = []  # load from file or define your list of websites
user_agents = ["Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)", 
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36']

for website in websites:
    j = 0
    print("testing website: ", website)
    responses[website] = {}
    
    # Loop through each user-agent
    for user_agent in user_agents:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument(f"user-agent={user_agent}")
        chrome_options.add_argument("--headless=new")
        chrome_options.set_capability('goog:loggingPrefs', {"performance": "ALL"})

        # Initialize the WebDriver
        driver = webdriver.Chrome(options=chrome_options)

        try:
            print(website, user_agent)
            # Open the website
            driver.set_page_load_timeout(15)  # increase timeout if needed, 15 seems plenty
            driver.get(website)

            time.sleep(1)  # Wait extra for the page to load

            # Get the performance logs
            logs = driver.get_log("performance")
                
            html = driver.page_source
            print(html_cf_block_or_challenge(html))
            cf_status = html_cf_block_or_challenge(html)

            # Parse the logs and extract HTTP responses
            for log in logs:
                log_json = json.loads(log["message"])["message"]
                # print(log_json)
                if log_json["method"] == "Network.responseReceived":
                    response = log_json["params"]["response"]
                    # print(response)
                    url = response["url"]

                    status = response["status"]

                    responses[website][user_agent] = {}
                    responses[website][user_agent]['code'] = status
                    responses[website][user_agent]["cloudflare_status"] = cf_status

                    # capture weird chrome error that returns 200 despite a network error
                    if not are_same_website(url, website):
                        if "data:image" in url:
                            responses[website][user_agent] = "NET_ERR"
                        else:
                            responses[website][user_agent] = str(status) + "_" + url
                    break  # Stop after the first response

        except Exception as e:
            print(e)
            # Handle exceptions (e.g., network issues, page not found)
            exception_str = str(e).split('\n')[0]
            responses[website][user_agent] = exception_str

        finally:
            # Close the driver
            driver.quit()

# Print the responses
for website, user_agent_responses in responses.items():
    print(f"Website: {website}")
    for user_agent, response in user_agent_responses.items():
        print(f"  User-Agent: {user_agent}\n  Response: {response} ")

# Save the responses to a json if desired
# with open('responses.json', 'w') as f:
#     json.dump(responses, f, indent=4)
