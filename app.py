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
import streamlit as st
import pandas as pd
from gemini_chat import render_chat_ui

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

# Streamlit UI
st.title("Lease Drop - Crude Oil Inquiry v2.0")

st.markdown("""
### Objective
Investigate if there has been a significant decrease or cessation ("drop") 
in reported crude oil production for a specific Texas oil lease within a defined time period.
""")

# Create tabs for different functionality
tab1, tab2 = st.tabs(["Data Retrieval", "AI Assistant"])

with tab1:
    st.subheader("Input Parameters")
    
    # Create two columns for the form
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("Lease Number:")
        st.markdown("(6 digits)")
        lease_num_input = st.text_input("", key="lease_num", placeholder="e.g., 123456")
        
        st.markdown("Beg Period:")
        st.markdown("(yymm or yy)")
        beg_period_input = st.text_input("", key="beg_period", placeholder="e.g., 2201")
    
    with col2:
        st.markdown("OR")
        st.markdown("Drilling Permit Number:")
        st.markdown("(6 digits)")
        drilling_permit_input = st.text_input("", key="drilling_permit", placeholder="e.g., 123456")
        
        st.markdown("End Period:")
        st.markdown("(yymm or yy)")
        end_period_input = st.text_input("", key="end_period", placeholder="e.g., 2301")
    
    if st.button("Get Lease Drop Data", key="submit_button"):
        # Basic validation
        validation_error = False
        
        # Check that exactly one identifier is provided
        if (not lease_num_input and not drilling_permit_input) or (lease_num_input and drilling_permit_input):
            st.error("Please provide either a Lease Number OR a Drilling Permit Number, not both or neither.")
            validation_error = True
        
        # Check that both period fields are filled
        if not beg_period_input or not end_period_input:
            st.error("Both Begin Period and End Period must be provided.")
            validation_error = True
        
        if not validation_error:
            # Determine which identifier to use
            identifier_type = "Lease Number" if lease_num_input else "Drilling Permit Number"
            identifier_value = lease_num_input if lease_num_input else drilling_permit_input
            
            with st.spinner(f"Accessing Lease Drop data for {identifier_type}: {identifier_value}... Please wait. This may take up to a minute."):
                # Call the function with the appropriate identifier
                html_content, error_message = access_lease_drop(identifier_type, identifier_value, beg_period_input, end_period_input)

                if error_message:
                    st.error(f"Error: {error_message}")
                elif html_content:
                    st.success("Data retrieval attempt finished. Parsing results...")
                    try:
                        # Parse the HTML table
                        try:
                            tables = pd.read_html(html_content)
                            if len(tables) > 0:
                                # Store the data in session state for the AI tab
                                st.session_state.lease_data = tables[0]
                                
                                # Display the table
                                st.subheader("Lease Drop Data:")
                                st.dataframe(tables[0])
                                
                                # Calculate and display summary statistics
                                if len(tables[0]) > 0:
                                    st.subheader("Summary Statistics:")
                                    
                                    # Try to find and analyze the production column
                                    production_col = None
                                    for col in tables[0].columns:
                                        if "CRUDE" in str(col).upper() and "OIL" in str(col).upper():
                                            production_col = col
                                            break
                                    
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
                                        
                                        st.dataframe(stats_df)
                                        
                                        # Check for lease drop
                                        if len(tables[0]) >= 2:
                                            # Sort by date if possible
                                            date_col = None
                                            for col in tables[0].columns:
                                                if "DATE" in str(col).upper() or "PERIOD" in str(col).upper():
                                                    date_col = col
                                                    break
                                            
                                            if date_col:
                                                try:
                                                    # Sort by date
                                                    tables[0] = tables[0].sort_values(by=date_col)
                                                    
                                                    # Get first and last production values
                                                    first_production = tables[0][production_col].iloc[0]
                                                    last_production = tables[0][production_col].iloc[-1]
                                                    
                                                    # Calculate percentage change
                                                    if first_production > 0:
                                                        pct_change = ((last_production - first_production) / first_production) * 100
                                                        
                                                        if pct_change <= -50:
                                                            st.warning(f"⚠️ Significant lease drop detected! Production decreased by {abs(pct_change):.2f}%")
                                                        elif pct_change < 0:
                                                            st.info(f"Production decreased by {abs(pct_change):.2f}%")
                                                        else:
                                                            st.success(f"Production increased by {pct_change:.2f}%")
                                                except Exception as e:
                                                    logger.error(f"Error analyzing production trend: {e}")
                                    else:
                                        st.info("Could not identify crude oil production column for analysis.")
                                else:
                                    st.info("No data rows found in the table.")
                            else:
                                st.warning("No tables found in the HTML content.")
                                st.subheader("Raw HTML Results:")
                                st.code(html_content)
                        except ValueError as ve:
                            logger.error(f"ValueError parsing HTML table: {ve}")
                            st.error(f"No tables found in the HTML. The query may have returned no results: {ve}")
                            st.subheader("Raw HTML Results (No Tables):")
                            st.code(html_content)
                    except Exception as parse_error:
                        logger.error(f"Error parsing HTML table: {parse_error}")
                        st.error(f"Successfully retrieved HTML, but failed to parse the data table: {parse_error}")
                        # Show raw HTML on parsing error too
                        st.subheader("Raw HTML Results (Parsing Error):")
                        st.code(html_content)
                else:
                    st.error("An unknown error occurred. No data or error message returned.")

with tab2:
    # Check if we have lease data in session state
    lease_data = st.session_state.get('lease_data', None)
    
    if lease_data is not None:
        render_chat_ui(lease_data)
    else:
        st.info("Please retrieve lease data in the 'Data Retrieval' tab first to enable AI assistance.")
        
        # Still allow chat without context if user wants to ask general questions
        if st.button("I just want to chat without lease data context"):
            render_chat_ui()