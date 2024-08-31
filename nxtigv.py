import os
import re
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Email utilities
def generate_temp_email():
    """Generate a temporary email address."""
    endpoint = 'https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1'
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        temp_email = response.json()[0]
        print(f"Generated temporary email: {temp_email}")
        return temp_email
    except requests.exceptions.RequestException as e:
        print(f"Failed to create a temporary email: {e}")
        return None


def check_incoming_emails(login, domain):
    """Check for incoming emails using the temp email service."""
    check_mail_endpoint = f'https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}'
    try:
        response = requests.get(check_mail_endpoint)
        response.raise_for_status()
        emails = response.json()
        print(f"Checked for emails. Found {len(emails)} emails.")
        return emails
    except requests.exceptions.RequestException as e:
        print(f"Failed to check emails: {e}")
        return []


def fetch_email_details(login, domain, email_id):
    """Fetch details of a specific email using the email ID."""
    fetch_mail_endpoint = f'https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={email_id}'
    try:
        response = requests.get(fetch_mail_endpoint)
        response.raise_for_status()
        email_details = response.json()
        print(f"Fetched email details for email ID {email_id}.")
        return email_details
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch email details: {e}")
        return None


def extract_verification_code_from_html(html_body):
    """Extract verification code from email HTML content."""
    soup = BeautifulSoup(html_body, 'html.parser')
    text = soup.get_text()
    pattern = r'Verification code:\s*(\d{6})'
    match = re.search(pattern, text)
    if match:
        print(f"Verification code extracted: {match.group(1)}")
        return match.group(1)
    else:
        print("No verification code found in the email content.")
        return None


# WebDriver setup and configuration
def setup_webdriver():
    """Setup the Chrome WebDriver with necessary options."""
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_driver_path = os.path.join(os.path.dirname(__file__), 'resources\chromedriver.exe')
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("WebDriver setup complete.")
    return driver


# Registration process
def perform_registration(driver, temp_email, registration_url):
    """Perform registration using a temporary email."""
    try:
        driver.get(registration_url)
        print("Navigated to registration page.")

        # Wait for the registration button and click it
        wait = WebDriverWait(driver, 15)
        go_register_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#go-register')))
        go_register_button.click()
        print("Clicked on 'Go Register' button.")

        # Fill in the registration form
        email_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#create-email')))
        email_input.send_keys(temp_email)
        print(f"Entered email: {temp_email}")

        password_input = driver.find_element(By.CSS_SELECTOR, '#create-password')
        password_input.send_keys(temp_email)
        print(f"Entered password: {temp_email}")

        repassword_input = driver.find_element(By.CSS_SELECTOR, '#create-repassword')
        repassword_input.send_keys(temp_email)
        print(f"Re-entered password: {temp_email}")

        checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#privacy-policy')))
        checkbox.click()
        print("Accepted privacy policy by ticking checkbox.")

        click_specific_send_code_button(driver)

        return True
    except Exception as e:
        print(f"An error occurred during registration: {e}")
        return False


def click_specific_send_code_button(driver):
    """Click the second 'send-code' button directly."""
    try:
        # Locate all buttons with the ID 'send-code'
        send_code_buttons = driver.find_elements(By.CSS_SELECTOR, '#send-code')

        # Ensure there is a second 'send-code' button
        if len(send_code_buttons) > 1:
            # Click the second 'send-code' button (index 1)
            driver.execute_script("arguments[0].click();", send_code_buttons[1])
            print("Clicked the second 'send-code' button successfully.")
        else:
            print("Second 'send-code' button not found.")
    except Exception as e:
        print(f"Error clicking the second 'send-code' button: {e}")


def enter_verification_code(driver, verification_code):
    """Enter the verification code and complete the registration."""
    try:
        captcha_field = driver.find_element(By.CSS_SELECTOR, '#captcha')
        captcha_field.send_keys(verification_code)
        print(f"Entered verification code: {verification_code}")

        register_button = driver.find_element(By.CSS_SELECTOR, '#register')
        register_button.click()
        print("Clicked on the 'Register' button.")
    except Exception as e:
        print(f"Failed to enter verification code or click register: {e}")


# Main process
def main_registration_process():
    """Main function to perform registration multiple times."""
    # Get user inputs for the registration URL and number of attempts
    registration_url = input("Enter the registration URL: ")
    run_count = int(input("Enter the number of times to run the registration process: "))

    for attempt in range(run_count):
        print(f"\n--- Starting registration attempt {attempt + 1} of {run_count} ---")
        temp_email = generate_temp_email()
        if not temp_email:
            print("Skipping attempt due to email generation failure.")
            continue

        print(f"Generated Temp Email: {temp_email}")
        login, domain = temp_email.split('@')

        driver = setup_webdriver()

        if perform_registration(driver, temp_email, registration_url):
            start_time = time.time()
            while time.time() - start_time < 120:  # Wait for 120 seconds
                emails = check_incoming_emails(login, domain)
                if emails:
                    latest_email = emails[0]
                    email_id = latest_email['id']
                    print(f"Received email with ID: {email_id}")

                    email_details = fetch_email_details(login, domain, email_id)
                    if email_details:
                        html_body = email_details.get('htmlBody', '')
                        verification_code = extract_verification_code_from_html(html_body)
                        if verification_code:
                            enter_verification_code(driver, verification_code)
                            print("Verification successful. Registration process completed.")
                            time.sleep(5)  # Wait to see the result before closing
                            break
                else:
                    print("No emails received yet. Checking again...")
                time.sleep(5)
        else:
            print("Registration attempt failed.")

        driver.quit()
        print(f"--- Finished registration attempt {attempt + 1} of {run_count} ---")


def show_intro():
    print("===========================================")
    print("Welcome to IGV Pass Script!")
    print("This script is brought to you by NXTGENCAT.")
    print("===========================================")


# Run the registration process
show_intro()
main_registration_process()
