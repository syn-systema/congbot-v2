from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import logging
import os
from datetime import datetime
import traceback
import pandas as pd
import json

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Helper function to log page source (without saving files)
def log_page_info(driver, prefix="debug"):
    if driver is None:
        logger.warning("Cannot log page info: driver is None")
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        current_url = driver.current_url
        page_title = driver.title
        logger.info(f"{prefix} URL: {current_url}")
        logger.info(f"{prefix} Title: {page_title}")
    except Exception as e:
        logger.error(f"Failed to log page info: {e}")

# Function to access Lease Drop - Crude Oil Inquiry
def access_lease_drop(identifier_type, identifier_value, beg_period, end_period):
    """
    Access the Texas Comptroller's website and retrieve lease drop data.
    
    Args:
        identifier_type (str): Type of identifier to use ('Lease Number' or 'Drilling Permit Number')
        identifier_value (str): Value of the identifier
        beg_period (str): Beginning period in YYMM format
        end_period (str): Ending period in YYMM format
        
    Returns:
        tuple: (html_content, error_message)
            - html_content: HTML content from the Texas Comptroller's website
            - error_message: Error message if unsuccessful, None otherwise
    """
    logger.info(f"Starting Lease Drop - Crude Oil Inquiry for {identifier_type}: {identifier_value}, Period: {beg_period}-{end_period}")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Use a standard user agent
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    # Anti-detection measures
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # Explicitly enable cookies - enhanced settings
    options.add_experimental_option("prefs", {
        "profile.default_content_settings.cookies": 1,
        "profile.cookie_controls_mode": 0,
        "profile.block_third_party_cookies": False,
        "profile.default_content_setting_values.cookies": 1,
        "profile.cookie_behavior": 0
    })
    
    # Add additional cookie-related arguments
    options.add_argument("--enable-cookies")
    options.add_argument("--disable-cookie-encryption")

    driver = webdriver.Chrome(options=options)
    # Further anti-detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Set window size to a standard desktop size
    driver.set_window_size(1366, 768)

    try:
        # Step 1: Visit the main index page to establish session
        logger.info("Navigating to main index page...")
        driver.get("https://mycpa.cpa.state.tx.us/cong/Index.jsp")
        time.sleep(5) # Allow more time for session setup
        logger.info("Main index page loaded.")
        log_page_info(driver, "main_index_page")
        
        # Manually set a cookie to indicate cookie support
        driver.execute_script("document.cookie='cookiesEnabled=true; path=/;'")
        
        # Step 2: Navigate to the check page to verify cookies
        logger.info("Navigating to check page...")
        driver.get("https://mycpa.cpa.state.tx.us/cong/loginForward.do?phase=check")
        time.sleep(5)  # Allow time for check page processing
        logger.info("Check page loaded.")
        log_page_info(driver, "check_page")

        # Step 3: Check for cookie error message on the check page itself
        if "Cookies are required" in driver.page_source or "Cookies are required" in driver.title:
            logger.warning("Cookie warning detected on check page. Attempting recovery...")
            
            # Multiple recovery attempts
            for attempt in range(3):
                logger.info(f"Cookie recovery attempt {attempt+1}/3")
                
                # Try different cookie enabling approaches
                driver.execute_script("navigator.cookieEnabled = true;")
                driver.execute_script("document.cookie='cookiesEnabled=true; path=/;'")
                
                # Clear cache and cookies, then re-establish
                driver.execute_script('window.localStorage.clear();')
                driver.execute_script('window.sessionStorage.clear();')
                driver.delete_all_cookies()
                
                # Revisit the main page to establish new cookies
                driver.get("https://mycpa.cpa.state.tx.us/cong/Index.jsp")
                time.sleep(3)
                
                # Try the check page again
                driver.get("https://mycpa.cpa.state.tx.us/cong/loginForward.do?phase=check")
                time.sleep(5)
                
                log_page_info(driver, f"cookie_recovery_attempt_{attempt+1}")
                
                # Check if we've resolved the cookie issue
                if "Cookies are required" not in driver.page_source and "Cookies are required" not in driver.title:
                    logger.info(f"Cookie issue resolved on attempt {attempt+1}")
                    break
                    
            # Final check after all recovery attempts
            if "Cookies are required" in driver.page_source or "Cookies are required" in driver.title:
                logger.error("Cookie error persists even after recovery attempts.")
                return None, "Cookies are required and could not be enabled. Please try running the application again."
        
        # Step 4: Try navigating to the Lease Drop page (prefer direct link click if possible)
        logger.info("Attempting navigation to Lease Drop - Crude Oil page...")
        target_url = "https://mycpa.cpa.state.tx.us/cong/reportLeaseDropCOForward.do"
        
        # Option A: Try clicking the link (might be more robust if session relies on navigation flow)
        try:
            logger.info("Trying to find and click the 'Lease Drop-Crude Oil' link...")
            lease_drop_link = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Lease Drop-Crude Oil')] | //a[contains(text(), 'Lease Drop - Crude Oil')] ")) # Handle variations
            )
            logger.info("Link found. Clicking...")
            time.sleep(0.5)
            lease_drop_link.click()
            time.sleep(8) # Wait for navigation after click
        except TimeoutException:
            logger.warning("'Lease Drop-Crude Oil' link not found or clickable. Proceeding with direct navigation.")
            # Option B: Direct navigation if link fails
            driver.get(target_url)
            time.sleep(8)
        except Exception as link_click_error:
            logger.error(f"Error clicking link: {link_click_error}. Proceeding with direct navigation.")
            driver.get(target_url)
            time.sleep(8)

        # Step 5: Verify successful navigation
        logger.info(f"Current URL after navigation attempt: {driver.current_url}")
        logger.info(f"Current page title: {driver.title}")
        
        if "Lease Drop - Crude Oil" in driver.title or "reportLeaseDropCOForward.do" in driver.current_url:
            logger.info("Successfully reached Lease Drop - Crude Oil page")
            log_page_info(driver, "success_lease_drop_page")

            # --- Find and fill the form ---            
            try:
                logger.info("Locating form elements...")
                logger.info(f"Current URL: {driver.current_url}")
                logger.info(f"Page title: {driver.title}")
                
                # Log the page source to help debug form elements
                logger.info("Logging page source for debugging form elements")
                log_page_info(driver, "before_form_interaction")
                
                # Print all form elements on the page for debugging
                try:
                    all_inputs = driver.find_elements(By.TAG_NAME, "input")
                    logger.info(f"Found {len(all_inputs)} input elements on the page")
                    for i, inp in enumerate(all_inputs):
                        input_type = inp.get_attribute("type")
                        input_name = inp.get_attribute("name")
                        input_id = inp.get_attribute("id")
                        logger.info(f"Input #{i}: type={input_type}, name={input_name}, id={input_id}")
                except Exception as e:
                    logger.error(f"Error listing input elements: {e}")
                
                # Try multiple selector strategies for the form elements
                # Determine which field to fill based on identifier type
                if identifier_type == "Lease Number":
                    # Try multiple approaches to find the lease number field
                    lease_num_input = None
                    selectors = [
                        (By.NAME, "leaseNum"),  # Updated to match actual field name
                        (By.ID, "leaseNum"),    # Updated to match actual field ID
                        (By.XPATH, "//input[@name='leaseNum']"),
                        (By.XPATH, "//input[contains(@name, 'lease')]"),
                        (By.XPATH, "//label[contains(text(), 'Lease')]/following::input[1]"),
                        (By.CSS_SELECTOR, "input[name='leaseNum']")
                    ]
                    
                    for selector_type, selector_value in selectors:
                        try:
                            logger.info(f"Trying to find Lease Number input with {selector_type}: {selector_value}")
                            element = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((selector_type, selector_value))
                            )
                            if element:
                                lease_num_input = element
                                logger.info(f"Found Lease Number input with {selector_type}: {selector_value}")
                                break
                        except Exception as e:
                            logger.warning(f"Selector {selector_type}: {selector_value} failed: {e}")
                    
                    if lease_num_input is None:
                        raise TimeoutException("Could not find Lease Number input field with any selector")
                    
                    lease_num_input.clear()
                    lease_num_input.send_keys(identifier_value)
                    logger.info(f"Filled Lease Number: {identifier_value}")
                else:
                    # Try multiple approaches to find the drilling permit field
                    drilling_permit_input = None
                    selectors = [
                        (By.NAME, "DPN"),  # Updated to match actual field name
                        (By.ID, "DPN"),    # Updated to match actual field ID
                        (By.XPATH, "//input[@name='DPN']"),
                        (By.XPATH, "//input[contains(@name, 'DPN')]"),
                        (By.XPATH, "//input[contains(@id, 'DPN')]"),
                        (By.XPATH, "//label[contains(text(), 'Permit')]/following::input[1]"),
                        (By.CSS_SELECTOR, "input[name='DPN']")
                    ]
                    
                    for selector_type, selector_value in selectors:
                        try:
                            logger.info(f"Trying to find Drilling Permit input with {selector_type}: {selector_value}")
                            element = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((selector_type, selector_value))
                            )
                            if element:
                                drilling_permit_input = element
                                logger.info(f"Found Drilling Permit input with {selector_type}: {selector_value}")
                                break
                        except Exception as e:
                            logger.warning(f"Selector {selector_type}: {selector_value} failed: {e}")
                    
                    if drilling_permit_input is None:
                        raise TimeoutException("Could not find Drilling Permit input field with any selector")
                    
                    drilling_permit_input.clear()
                    drilling_permit_input.send_keys(identifier_value)
                    logger.info(f"Filled Drilling Permit Number: {identifier_value}")
                
                # Try multiple approaches to find the period fields
                beg_period_input = None
                selectors = [
                    (By.NAME, "begFilPrd"),  # Updated to match actual field name
                    (By.ID, "begFilPrd"),    # Updated to match actual field ID
                    (By.XPATH, "//input[@name='begFilPrd']"),
                    (By.XPATH, "//input[contains(@name, 'beg')]"),
                    (By.XPATH, "//label[contains(text(), 'Beg')]/following::input[1]"),
                    (By.CSS_SELECTOR, "input[name='begFilPrd']")
                ]
                
                for selector_type, selector_value in selectors:
                    try:
                        logger.info(f"Trying to find Begin Period input with {selector_type}: {selector_value}")
                        element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((selector_type, selector_value))
                        )
                        if element:
                            beg_period_input = element
                            logger.info(f"Found Begin Period input with {selector_type}: {selector_value}")
                            break
                    except Exception as e:
                        logger.warning(f"Selector {selector_type}: {selector_value} failed: {e}")
                
                if beg_period_input is None:
                    raise TimeoutException("Could not find Begin Period input field with any selector")
                
                end_period_input = None
                selectors = [
                    (By.NAME, "endFilPrd"),  # Updated to match actual field name
                    (By.ID, "endFilPrd"),    # Updated to match actual field ID
                    (By.XPATH, "//input[@name='endFilPrd']"),
                    (By.XPATH, "//input[contains(@name, 'end')]"),
                    (By.XPATH, "//label[contains(text(), 'End')]/following::input[1]"),
                    (By.CSS_SELECTOR, "input[name='endFilPrd']")
                ]
                
                for selector_type, selector_value in selectors:
                    try:
                        logger.info(f"Trying to find End Period input with {selector_type}: {selector_value}")
                        element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((selector_type, selector_value))
                        )
                        if element:
                            end_period_input = element
                            logger.info(f"Found End Period input with {selector_type}: {selector_value}")
                            break
                    except Exception as e:
                        logger.warning(f"Selector {selector_type}: {selector_value} failed: {e}")
                
                if end_period_input is None:
                    raise TimeoutException("Could not find End Period input field with any selector")
                
                time.sleep(0.3) # Small delay
                beg_period_input.clear()
                beg_period_input.send_keys(beg_period)
                time.sleep(0.3)

                end_period_input.clear()
                end_period_input.send_keys(end_period)
                time.sleep(0.3)
                
                # Find and click submit button with multiple approaches
                submit_button = None
                selectors = [
                    (By.XPATH, "//input[@type='submit'][contains(@value, 'Submit')]"),
                    (By.XPATH, "//button[contains(text(),'Submit')]"),
                    (By.XPATH, "//input[@type='button'][contains(@value, 'Submit')]"),
                    (By.XPATH, "//a[contains(text(), 'Submit')]"),
                    (By.CSS_SELECTOR, "input[type='submit']"),
                    (By.XPATH, "//input[@type='submit']"),
                    (By.XPATH, "//button[@type='submit']")
                ]
                
                for selector_type, selector_value in selectors:
                    try:
                        logger.info(f"Trying to find Submit button with {selector_type}: {selector_value}")
                        element = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((selector_type, selector_value))
                        )
                        if element:
                            submit_button = element
                            logger.info(f"Found Submit button with {selector_type}: {selector_value}")
                            break
                    except Exception as e:
                        logger.warning(f"Selector {selector_type}: {selector_value} failed: {e}")
                
                if submit_button is None:
                    # Last resort: try to find any button or input that might be a submit button
                    try:
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        inputs = driver.find_elements(By.XPATH, "//input[@type='submit' or @type='button']")
                        logger.info(f"Found {len(buttons)} buttons and {len(inputs)} input buttons")
                        
                        # Log all potential submit elements
                        for i, btn in enumerate(buttons):
                            btn_text = btn.text
                            btn_type = btn.get_attribute("type")
                            logger.info(f"Button #{i}: text='{btn_text}', type={btn_type}")
                        
                        for i, inp in enumerate(inputs):
                            inp_value = inp.get_attribute("value")
                            inp_type = inp.get_attribute("type")
                            logger.info(f"Input button #{i}: value='{inp_value}', type={inp_type}")
                        
                        # Try to find a button with text or value containing "submit", "search", "find", etc.
                        for btn in buttons:
                            if any(keyword in btn.text.lower() for keyword in ["submit", "search", "find", "go", "query"]):
                                submit_button = btn
                                logger.info(f"Found potential submit button with text: {btn.text}")
                                break
                        
                        if submit_button is None:
                            for inp in inputs:
                                inp_value = inp.get_attribute("value") or ""
                                if any(keyword in inp_value.lower() for keyword in ["submit", "search", "find", "go", "query"]):
                                    submit_button = inp
                                    logger.info(f"Found potential submit button with value: {inp_value}")
                                    break
                    except Exception as e:
                        logger.error(f"Error in last resort button search: {e}")
                
                if submit_button is None:
                    raise TimeoutException("Could not find Submit button with any selector")
                
                logger.info("Form elements located and filled.")

                logger.info("Submitting the form...")
                # Scroll into view just in case
                driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                time.sleep(0.5)
                
                # Log page info before clicking
                log_page_info(driver, "before_submit_click")
                
                submit_button.click()
                logger.info("Submit button clicked")
                
                # Wait for potential navigation/result loading
                # A more robust wait would look for a specific element on the results page
                logger.info("Waiting after submission...")
                time.sleep(10) 
                logger.info("Form submitted. Logging page source.")
                log_page_info(driver, "after_form_submission")

                results_html = driver.page_source
                logger.info("Returning page source after submission.")
                return results_html, None # Return HTML content, no error

            except TimeoutException:
                logger.error("Failed to find one or more form elements within the timeout period.")
                log_page_info(driver, "error_finding_form_elements")
                return None, "Error: Could not find form elements. Check element names/XPATH."
            except Exception as e:
                logger.error(f"An error occurred during form interaction: {e}")
                log_page_info(driver, "error_during_form_interaction")
                return None, f"An error occurred during form interaction: {e}"

        else:
             # Final check for cookie error page
            if "Cookies are required" in driver.page_source or "Cookies are required" in driver.title:
                 logger.error("Failed to reach target page; landed on cookie error page.")
                 log_page_info(driver, "final_cookie_error")
                 return None, "Navigation failed, ended up on 'Cookies are required' page. Please try again later."
            else:
                 logger.error("Failed to reach Lease Drop - Crude Oil page. Unknown state.")
                 log_page_info(driver, "navigation_failure_unknown")
                 return None, "Failed to reach Lease Drop - Crude Oil page after navigation attempts."

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        logger.error(traceback.format_exc()) # Log full traceback
        log_page_info(driver, "general_error")
        return None, f"General error during access attempt: {str(e)}"
    finally:
        logger.info("Closing WebDriver.")
        # Ensure driver is quit even if returned earlier
        if 'driver' in locals() and driver:
             driver.quit()

def process_lease_data(html_content):
    """
    Process the HTML content from the Texas Comptroller's website and extract lease data.
    
    Args:
        html_content (str): HTML content from the Texas Comptroller's website
        
    Returns:
        tuple: (tables, production_col, date_col, stats_df, pct_change, error_message)
            - tables: List of pandas DataFrames containing the lease data
            - production_col: Name of the production column
            - date_col: Name of the date column
            - stats_df: DataFrame containing summary statistics
            - pct_change: Percentage change in production
            - error_message: Error message if unsuccessful, None otherwise
    """
    try:
        # Parse the HTML table
        try:
            tables = pd.read_html(html_content)
            if len(tables) > 0:
                # Try to find and analyze the production column
                production_col = None
                
                # First try to find a column with "CRUDE OIL"
                for col in tables[0].columns:
                    if "CRUDE" in str(col).upper() and "OIL" in str(col).upper():
                        production_col = col
                        break
                
                # Next try to find a column with "GROSS BARRELS"
                if production_col is None:
                    for col in tables[0].columns:
                        if "GROSS" in str(col).upper() and "BARRELS" in str(col).upper():
                            production_col = col
                            break
                
                # If not found, try to find columns with just "BARRELS" or "BBL"
                if production_col is None:
                    for col in tables[0].columns:
                        if "BARRELS" in str(col).upper() or "BBL" in str(col).upper():
                            production_col = col
                            break
                
                # Last resort: look for any numeric column with values that could be production
                if production_col is None:
                    for col in tables[0].columns:
                        # Try to convert to numeric and see if it has reasonable values
                        try:
                            numeric_col = pd.to_numeric(tables[0][col], errors='coerce')
                            # Check if this column has non-zero values and not too many NaNs
                            if numeric_col.sum() > 0 and numeric_col.count() > len(tables[0]) * 0.5:
                                production_col = col
                                break
                        except:
                            continue
                
                if production_col:
                    # Convert to numeric, coercing errors to NaN
                    tables[0][production_col] = pd.to_numeric(tables[0][production_col], errors='coerce')
                    
                    # Calculate statistics
                    stats_df = pd.DataFrame({
                        'Statistic': ['Count', 'Mean', 'Median', 'Min', 'Max', 'Std Dev'],
                        'Value': [
                            tables[0][production_col].count(),
                            tables[0][production_col].mean(),
                            tables[0][production_col].median(),
                            tables[0][production_col].min(),
                            tables[0][production_col].max(),
                            tables[0][production_col].std()
                        ]
                    })
                    
                    # Extract period information from the table
                    # In the Texas Comptroller's website, the period is often in rows with "Period: YYMM" format
                    # or in a column with "DATE" or "PERIOD" in the name
                    date_col = None
                    
                    # First try to find a column with "DATE" or "PERIOD" in the name
                    for col in tables[0].columns:
                        if "DATE" in str(col).upper() or "PERIOD" in str(col).upper():
                            date_col = col
                            break
                    
                    # If no date column found, try to extract from "Period: YYMM" format in rows
                    if date_col is None:
                        date_col = 'Period'
                        tables[0][date_col] = None
                        
                        # Check if "Primary Taxpayer #" column exists and contains period information
                        if 'Primary Taxpayer #' in tables[0].columns:
                            current_period = None
                            for i, row in tables[0].iterrows():
                                primary_taxpayer = str(row.get('Primary Taxpayer #', ''))
                                if 'Period:' in primary_taxpayer:
                                    # Extract the period (e.g., "Period: 1602" -> "1602")
                                    current_period = primary_taxpayer.split('Period:')[1].strip()
                                
                                # Assign the current period to this row
                                if current_period:
                                    tables[0].at[i, date_col] = current_period
                            
                            # Remove rows without production data (like period header rows)
                            tables[0] = tables[0].dropna(subset=[production_col])
                        else:
                            # If we can't find period information, return an error
                            return tables, production_col, None, stats_df, None, "Could not identify date column for analysis"
                    
                    # Check for lease drop
                    if len(tables[0]) >= 2:
                        try:
                            # Sort by date
                            tables[0] = tables[0].sort_values(by=date_col)
                            
                            # Filter out rows with zero or NaN production values
                            non_zero_df = tables[0][tables[0][production_col] > 0].copy()
                            
                            if len(non_zero_df) >= 2:
                                # Get first and last production values from non-zero rows
                                first_production = non_zero_df[production_col].iloc[0]
                                last_production = non_zero_df[production_col].iloc[-1]
                                
                                # Calculate percentage change
                                pct_change = ((last_production - first_production) / first_production) * 100
                                return tables, production_col, date_col, stats_df, pct_change, None
                            else:
                                # If we don't have enough non-zero values, return the data without percentage change
                                return tables, production_col, date_col, stats_df, None, "Not enough non-zero production values to calculate percentage change"
                        except Exception as e:
                            logger.error(f"Error analyzing production trend: {e}")
                            return tables, production_col, date_col, stats_df, None, f"Error analyzing production trend: {e}"
                    else:
                        return tables, production_col, date_col, stats_df, None, "Not enough data points to analyze trend"
                else:
                    return tables, None, None, None, None, "Could not identify crude oil production column for analysis"
            else:
                return [], None, None, None, None, "No tables found in the HTML content"
        except ValueError as ve:
            logger.error(f"ValueError parsing HTML table: {ve}")
            return [], None, None, None, None, f"No tables found in the HTML. The query may have returned no results: {ve}"
    except Exception as parse_error:
        logger.error(f"Error parsing HTML table: {parse_error}")
        return [], None, None, None, None, f"Error parsing HTML table: {parse_error}"

def save_to_database(connection, query_info, tables=None, stats_df=None, pct_change=None):
    """
    Save query information and results to a database.
    
    Args:
        connection: Database connection object
        query_info (dict): Dictionary containing query information
        tables (list): List of pandas DataFrames containing the lease data
        stats_df (DataFrame): DataFrame containing summary statistics
        pct_change (float): Percentage change in production
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create a cursor
        cursor = connection.cursor()
        
        # Insert query information
        query_id = None
        if query_info:
            # Convert query_info to JSON string
            query_info_json = json.dumps(query_info)
            
            # Insert query information
            cursor.execute(
                """
                INSERT INTO lease_queries 
                (timestamp, identifier_type, identifier_value, beg_period, end_period, status, error_message, query_info) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, 
                (
                    query_info.get("timestamp"), 
                    query_info.get("identifier_type"), 
                    query_info.get("identifier_value"), 
                    query_info.get("beg_period"), 
                    query_info.get("end_period"), 
                    query_info.get("status"), 
                    query_info.get("error_message"), 
                    query_info_json
                )
            )
            
            # Get the ID of the inserted query
            query_id = cursor.lastrowid
        
        # Insert lease data
        if tables and len(tables) > 0 and query_id:
            # Convert DataFrame to records
            records = tables[0].to_dict(orient='records')
            
            # Convert records to JSON string
            records_json = json.dumps(records)
            
            # Insert lease data
            cursor.execute(
                """
                INSERT INTO lease_data 
                (query_id, data_json, pct_change) 
                VALUES (?, ?, ?)
                """, 
                (query_id, records_json, pct_change)
            )
        
        # Insert statistics
        if stats_df is not None and query_id:
            # Convert DataFrame to records
            stats_records = stats_df.to_dict(orient='records')
            
            # Convert records to JSON string
            stats_json = json.dumps(stats_records)
            
            # Insert statistics
            cursor.execute(
                """
                INSERT INTO lease_statistics 
                (query_id, statistics_json) 
                VALUES (?, ?)
                """, 
                (query_id, stats_json)
            )
        
        # Commit the transaction
        connection.commit()
        
        return True
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        
        # Rollback the transaction
        if connection:
            connection.rollback()
        
        return False
