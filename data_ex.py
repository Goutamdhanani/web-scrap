from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time

def extract_popup_data(driver):
    try:
        # Wait for the modal to appear and the spinner to disappear
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "modal-content"))
        )
        
        # Check for and wait for spinner to disappear
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element((By.CLASS_NAME, "spinner-border"))
        )
        
        # Get the inner HTML of the modal
        modal = driver.find_element(By.CLASS_NAME, "modal-content")
        modal_html = modal.get_attribute('innerHTML')
        modal_soup = BeautifulSoup(modal_html, 'html.parser')
        
        # Initialize empty strings for PAN and GSTIN
        pan = None
        gstin = None
        
        # Find the table within the modal
        table = modal_soup.find('table', class_='table table-borderless table-sm table-responsive-lg table-striped font-sm')
        
        if table:
            # Find all rows in the table
            rows = table.find_all('tr')
            for row in rows:
                # Check for the PAN number
                if 'PAN No.' in row.text:
                    td = row.find_all('td')[1]  # Get the second <td> element
                    pan_span = td.find('span', class_='mr-1 fw-600')
                    pan = pan_span.text.strip() if pan_span else None
                
                # Check for the GSTIN
                if 'GSTIN No.' in row.text:
                    td = row.find_all('td')[1]  # Get the second <td> element
                    gstin_span = td.find('span', class_='mr-1 fw-600')
                    gstin = gstin_span.text.strip() if gstin_span else None
        
        # Close the modal
        close_button = driver.find_element(By.CLASS_NAME, "close")
        driver.execute_script("arguments[0].click();", close_button)
        
        return {
            'PAN': pan,
            'GSTIN': gstin,
        }
    except Exception as e:
        print(f"Error extracting popup data: {e}")
        return {
            'PAN': None,
            'GSTIN': None,
        }

def get_project_details(link):
    project_code = link.text.strip()
    project_name = link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'shadow')]//span[@class='font-lg fw-600']").text.strip()
    project_type = link.find_element(By.XPATH, "./following::span[1]").text.strip()

    contact_div = link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'shadow')]//div[@class='mt-1']")
    spans = contact_div.find_elements(By.XPATH, ".//span")
    phone = spans[0].text.strip() if len(spans) > 0 else 'N/A'
    email = spans[1].text.strip() if len(spans) > 1 else 'N/A'
    address = spans[2].text.strip() if len(spans) > 2 else 'N/A'

    validity_element = link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'shadow')]//span[@class='text-orange ml-1']")
    validity = validity_element.text.strip()

    return {
        'Code': project_code,
        'Name': project_name,
        'Type': project_type,
        'Phone': phone,
        'Email': email,
        'Address': address,
        'Valid Upto': validity,
    }

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode

# Initialize the WebDriver
driver = webdriver.Chrome(options=chrome_options)

# Navigate to the page
url = "https://hprera.nic.in/PublicDashboard"
driver.get(url)

# Wait for the page to load
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.XPATH, "//a[@title='View Application']"))
)

# Find all project links
project_links = driver.find_elements(By.XPATH, "//a[@title='View Application']")

# Limit to 6 projects
project_links = project_links[:6]

print(f"Found {len(project_links)} project links")

projects = []

for i, link in enumerate(project_links):
    project_code = link.text.strip()
    if "Previous Detail >>" in project_code or project_code == "":
        continue
    try:
        # Print processing status
        print(f"Processing project {i+1}/{len(project_links)}: {project_code}")

        # Extract basic project details
        project_data = get_project_details(link)
        
        # Extract popup data
        driver.execute_script("arguments[0].click();", link)
        
        # Wait for modal to open and the content to load
        time.sleep(2)  # Additional delay before extracting data
        
        popup_data = extract_popup_data(driver)
        project_data.update(popup_data)

        projects.append(project_data)
        
        time.sleep(1)  # Add a delay to avoid overwhelming the server
    except Exception as e:
        print(f"Failed to process project {project_code}: {e}")

# Close the browser
driver.quit()

# Save the data to a JSON file
with open('projects.json', 'w', encoding='utf-8') as f:
    json.dump(projects, f, ensure_ascii=False, indent=4)

print(f"Extracted information for {len(projects)} projects and saved to projects.json")
