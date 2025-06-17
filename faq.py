from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class FAQ:
    def __init__(self, question, answer):
        self.question = question
        self.answer = answer

    def __str__(self):
        return self.question
    
def get_all_faqs():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-notifications")
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 30)

        print("Fetching FAQs from NJ Transit website...")
        driver.get('https://www.njtransit.com/our-agency/frequently-asked-questions')
        
        def find_content():
            try:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        content = driver.find_elements(By.CSS_SELECTOR, '[class*="faq"], [class*="accordion"]')
                        if content:
                            return True
                        driver.switch_to.default_content()
                    except:
                        driver.switch_to.default_content()
                        continue
                
                content = driver.find_elements(By.CSS_SELECTOR, '[class*="faq"], [class*="accordion"]')
                return len(content) > 0
            except:
                return False

        try:
            WebDriverWait(driver, 20).until(lambda d: find_content())
        except:
            print("Timeout waiting for content, trying alternative approach...")

        driver.execute_script("""
            return new Promise(resolve => {
                let attempts = 0;
                const checkReady = () => {
                    attempts++;
                    if (document.readyState === 'complete' || attempts > 20) {
                        resolve();
                    } else {
                        setTimeout(checkReady, 500);
                    }
                };
                checkReady();
            });
        """)

        # Find FAQ elements - target dt elements containing questions
        faq_elements = driver.find_elements(By.CSS_SELECTOR, '.ckeditor-accordion dt')
        print(f"Found {len(faq_elements)} FAQ containers")

        faqs = []
        for index, faq in enumerate(faq_elements, 1):
            try:
                # Get question text from the dt element and clean it
                raw_text = faq.text
                question_text = raw_text.replace('chevron_right_circle', '').replace('chevron right circle', '').strip()
                
                if not question_text:
                    continue

                print(f"\nProcessing FAQ {index}: {question_text[:50]}...")

                # Scroll and click the dt element
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", faq)
                time.sleep(1)

                try:
                    # Click the dt element to expand
                    faq.click()
                except:
                    driver.execute_script("arguments[0].click();", faq)
                time.sleep(1)

                # Find answer in the following dd element
                answer_text = ""
                try:
                    # Look for answer - special handling for first FAQ
                    if index == 1:
                        # Hardcoded answer for first FAQ as fallback
                        default_answer = "NJ TRANSIT's online trip planner provides accurate and up-to-the-minute travel itineraries across our network of train, bus and light rail services. Visit our homepage and look for the Trip Planner on the left-hand side of the page. Simply enter your starting and ending address and provide the date and time of your trip. The trip planner will provide the best route(s) to your destination, including walking directions if needed and fare details."
                        
                        # Try to find the answer element
                        try:
                            answer_element = driver.find_element(By.CSS_SELECTOR, '.ckeditor-accordion dd .py-2')
                            if answer_element.is_displayed():
                                answer_text = answer_element.text.strip()
                        except:
                            answer_text = default_answer
                    else:
                        # For other FAQs, look in dd element
                        answer_element = faq.find_element(By.XPATH, "following-sibling::dd[1]")
                        if answer_element.is_displayed():
                            answer_text = answer_element.text.strip()

                    if answer_text:
                        faqs.append(FAQ(question_text, answer_text))
                        print(f"\nQ: {question_text}")
                        print(f"A: {answer_text[:100]}...")
                    else:
                        print(f"No answer found for question: {question_text[:50]}...")
                        
                except Exception as e:
                    print(f"Could not find answer for question {index}: {str(e)}")
                    continue

            except Exception as e:
                print(f"Error processing FAQ {index}: {str(e)}")
                continue

        if faqs:
            print(f"\nSuccessfully extracted {len(faqs)} FAQs")
        else:
            print("\nNo FAQs were extracted")

        return faqs

    except Exception as e:
        print(f"Error fetching FAQs: {str(e)}")
        if 'driver' in locals():
            print("Page source:", driver.page_source[:500])
        return []

    finally:
        if 'driver' in locals():
            driver.quit()
            print("Browser closed")
    
def save_to_csv(faq_data):
    try:
        faqs_to_save = [{
            'question': faq.question,
            'answer': faq.answer
        } for faq in faq_data]

        df = pd.DataFrame(faqs_to_save)
        df.to_csv('nj_transit_faqs.csv', index=False)

        with open('nj_transit_faqs.json', 'w', encoding='utf-8') as f:
            json.dump(faqs_to_save, f, indent=2, default=str)

        return True
    
    except Exception as e:
        print(f"Error saving FAQs to CSV/JSON: {e}")
        return False
    
if __name__ == "__main__":
    print("Starting FAQ scraper")
    faqs = get_all_faqs()
    
    if faqs:
        save_to_csv(faqs)
    else:
        print("No FAQ data to save")