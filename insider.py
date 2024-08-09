from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import openai

def scrape_transcript(youtube_url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get(youtube_url)
    time.sleep(5)
    
    try:
        # Handle consent popup if it appears
        consent_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Agree to the use of cookies and other data for the purposes described']"))
        )
        driver.execute_script("arguments[0].click();", consent_button)
        time.sleep(2)
    except:
        print("No consent popup found or unable to click it.")
    
    try:
        # Use JavaScript to click the expand button
        expand_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tp-yt-paper-button#expand'))
        )
        driver.execute_script("arguments[0].click();", expand_button)
        time.sleep(2)
    except Exception as e:
        print(f"Failed to expand description: {e}")
    
    try:
        # Wait for and click the "Show transcript" button
        transcript_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "yt-spec-button-shape-next") and contains(., "Show transcript")]'))
        )
        driver.execute_script("arguments[0].click();", transcript_button)
        time.sleep(2)
    except Exception as e:
        print(f"Failed to find 'Show transcript' button: {e}")
        driver.quit()
        return None

    try:
        segments = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ytd-transcript-segment-renderer'))
        )
        transcript = []
        for segment in segments:
            time_stamp = segment.find_element(By.CSS_SELECTOR, '.segment-timestamp').text.strip()
            text = segment.find_element(By.CSS_SELECTOR, '.segment-text').text.strip()
            transcript.append(f"{time_stamp} - {text}")
        
        driver.quit()
        return "\n".join(transcript)
        
    except Exception as e:
        print(f"Failed to scrape the transcript: {e}")
        driver.quit()
        return None

# Function to call OpenAI's API to get the highlights and summary
def analyze_transcript(transcript, user_input):
    openai.api_key = 'YOUR OPENAI API KEY'  # Replace with your OpenAI API key

    # Get highlights of the transcript
    highlight_response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": """You are a helpful assistant for our marketing team. 
             You will receive a transcript of a youtube video. 
             You need to highlight the key points of the transcript for our marketing team to digest well."""},
            {"role": "user", "content": f"""Here is a transcript: \n{transcript}\n 
             Can you highlight the key points?"""}
        ]
    )
    highlights = highlight_response['choices'][0]['message']['content']

    # Get summary based on user input
    summary_response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": """You are a helpful assistant for our marketing team. 
             You will receive a transcript of a youtube video and a user query. The query is a list of concepts or terms that the user is interested in.
             You need to find the most relevant parts of the transcript that are related to the user query and summarize them.
             Also add the exact timestamps of the transcript to refer to the exact parts of the video if you are using the transcript in your summary.
             """},
            {"role": "user", "content": f"""Here is a transcript: \n{transcript}\n 
             Can you summarize the ideas related to: {user_input}?"""}
        ]
    )
    summary = summary_response['choices'][0]['message']['content']

    return highlights, summary

# Main function to drive the tool
def main():
    youtube_url = input("Please enter the YouTube video URL: ")
    user_input = input("Please enter the terms or concepts you are interested in: ")

    # Scrape the transcript
    print("Scraping the transcript...")
    transcript = scrape_transcript(youtube_url)
    print("Transcript scraped successfully.")

    # Analyze the transcript
    print("Analyzing the transcript...")
    highlights, summary = analyze_transcript(transcript, user_input)
    
    # Display the results
    print("\n--- Highlights ---\n")
    print(highlights)
    print("\n--- Summary ---\n")
    print(summary)

if __name__ == "__main__":
    main()
