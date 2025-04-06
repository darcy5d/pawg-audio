import os
from dotenv import load_dotenv
import openai

def test_openai_api():
    # Load environment variables
    load_dotenv()
    
    # Get and verify API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        return
    if not api_key.startswith("sk-"):
        print("❌ Error: API key format appears incorrect (should start with 'sk-')")
        return
    
    print("✅ API Key found and format looks correct")
    
    # Initialize the OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    try:
        print("Attempting to make API call...")
        # Make a simple API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! This is a test message."}
            ],
            max_tokens=50
        )
        
        print("\n✅ API Test Successful!")
        print("\nResponse:")
        print(response.choices[0].message.content)
        
    except openai.AuthenticationError as e:
        print("❌ Authentication Error!")
        print(f"Error: {str(e)}")
        print("\nPlease check your API key in the .env file")
    except openai.RateLimitError as e:
        print("❌ Rate Limit Error!")
        print(f"Error: {str(e)}")
        print("\nYou may have exceeded your quota. Check your OpenAI account usage.")
    except Exception as e:
        print("❌ API Test Failed!")
        print(f"Error: {str(e)}")
        print("\nPlease check your OpenAI account status and billing information.")

if __name__ == "__main__":
    test_openai_api() 