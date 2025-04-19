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

# Create a container for the form
form_container = st.container()

with form_container:
    st.markdown("### Input Parameters")
    
    # Create two columns for the identifier section
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Lease Number:**")
        lease_num_input = st.text_input(
            "(6 digits)", 
            max_chars=6,
            value="011457", # Default example
            key="lease_number"
        )

    with col2:
        st.markdown("**OR**")
        st.markdown("**Drilling Permit Number:**")
        drilling_permit_input = st.text_input(
            "(6 digits)",
            max_chars=6,
            key="drilling_permit"
        )

    # Create two columns for the period section
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**Beg Period:**")
        beg_period_input = st.text_input(
            "(yymm or yy)",
            max_chars=4,
            value="2201", # Default example
            key="beg_period"
        )

    with col4:
        st.markdown("**End Period:**")
        end_period_input = st.text_input(
            "(yymm or yy)",
            max_chars=4,
            value="2301", # Default example
            key="end_period"
        )

    # Add a divider
    st.markdown("---")

# Validation and submission
if st.button("Get Lease Drop Data", key="submit_button"):
    # Basic validation
    validation_error = False
    
    # Check that exactly one identifier is provided
    if (lease_num_input and drilling_permit_input) or (not lease_num_input and not drilling_permit_input):
        st.error("Please provide EITHER Lease Number OR Drilling Permit Number (not both, not neither).")
        validation_error = True
    
    # Check that begin and end periods are provided
    if not beg_period_input or not end_period_input:
        st.error("Both Begin Period and End Period are required.")
        validation_error = True
    
    if not validation_error:
        # Determine which identifier to use
        identifier_type = "Lease Number" if lease_num_input else "Drilling Permit Number"
        identifier_value = lease_num_input if lease_num_input else drilling_permit_input
        
        with st.spinner(f"Accessing Lease Drop data for {identifier_type}: {identifier_value}... Please wait. This may take up to a minute."):
            # Call the function with the appropriate identifier
            html_content, error_message = access_lease_drop(identifier_type, identifier_value, beg_period_input, end_period_input)

            if error_message:
                st.error(f"Failed to retrieve data: {error_message}")
            elif html_content:
                st.success("Data retrieval attempt finished. Parsing results...")
                try:
                    # Parse the HTML table
                    try:
                        # Try to use lxml parser first (faster and more robust)
                        tables = pd.read_html(html_content, flavor='lxml')
                        if tables:
                            df = tables[0]
                            st.success("Data retrieved successfully!")
                            
                            # Process the dataframe
                            # Remove rows where all columns are NaN
                            df = df.dropna(how='all')
                            
                            # Display the data
                            st.subheader("Lease Drop Data")
                            st.dataframe(df)
                            
                            # Calculate and display summary statistics
                            if 'Gross Barrels' in df.columns:
                                numeric_cols = ['Gross Barrels', 'Taxable Barrels', 'Gross Value', 'Net Value']
                                summary_df = df[numeric_cols].apply(pd.to_numeric, errors='coerce').describe()
                                st.subheader("Summary Statistics")
                                st.dataframe(summary_df)
                                
                                # Calculate total barrels
                                total_barrels = df['Gross Barrels'].apply(pd.to_numeric, errors='coerce').sum()
                                st.metric("Total Gross Barrels", f"{total_barrels:,.0f}")
                                
                                # Visualize the data
                                st.subheader("Production Over Time")
                                try:
                                    # Extract period information
                                    periods = []
                                    current_period = None
                                    for _, row in df.iterrows():
                                        if isinstance(row[1], str) and 'Period:' in row[1]:
                                            current_period = row[1].replace('Period:', '').strip()
                                        elif current_period and pd.notna(row['Gross Barrels']):
                                            periods.append((current_period, row['Gross Barrels']))
                                    
                                    if periods:
                                        period_df = pd.DataFrame(periods, columns=['Period', 'Gross Barrels'])
                                        period_df['Gross Barrels'] = pd.to_numeric(period_df['Gross Barrels'], errors='coerce')
                                        st.bar_chart(period_df.set_index('Period'))
                                except Exception as e:
                                    st.warning(f"Could not generate chart: {str(e)}")
                        else:
                            st.error("No tables found in the response")
                            st.text("Raw HTML Results (No Tables Found):")
                            st.code(html_content[:1000] + "..." if len(html_content) > 1000 else html_content)
                    except ImportError:
                        st.error("Missing optional dependency 'lxml'. Install using: pip install lxml")
                        # Fallback to html5lib
                        try:
                            tables = pd.read_html(html_content, flavor='html5lib')
                            if tables:
                                df = tables[0]
                                st.success("Data retrieved successfully (using html5lib fallback)!")
                                st.dataframe(df)
                            else:
                                st.error("No tables found in the response")
                                st.text("Raw HTML Results (No Tables Found):")
                                st.code(html_content[:1000] + "..." if len(html_content) > 1000 else html_content)
                        except Exception as e:
                            st.error(f"Failed to parse HTML table: {str(e)}")
                            st.text("Raw HTML Results (Parsing Error):")
                            st.code(html_content[:1000] + "..." if len(html_content) > 1000 else html_content)
                    except Exception as e:
                        st.error(f"Failed to parse HTML table: {str(e)}")
                        st.text("Raw HTML Results (Parsing Error):")
                        st.code(html_content[:1000] + "..." if len(html_content) > 1000 else html_content)
                
                except Exception as parse_error:
                    logger.error(f"Error parsing HTML table: {parse_error}")
                    st.error(f"Successfully retrieved HTML, but failed to parse the data table: {parse_error}")
                    # Show raw HTML on parsing error too
                    st.subheader("Raw HTML Results (Parsing Error):")
                    st.text_area("HTML Output", html_content, height=300)

            else:
                st.error("An unknown error occurred. No data or error message returned.")