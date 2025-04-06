import os
import json
from datetime import datetime, timezone
import anthropic
import openai
from openai import OpenAI
from dotenv import load_dotenv
from podcast_analyzer import PodcastAnalyzer

def test_apis():
    """Test all three APIs with a single episode"""
    load_dotenv()
    
    # Initialize clients
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    deepseek_client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com/v1"
    )
    
    # Test episode
    test_audio = "the_grant_williams_p_the_end_game_ep_55_f.mp3"
    test_title = "The End Game Ep 55 - Fred Hickey"
    
    print("\n=== Testing APIs ===")
    
    try:
        # 1. Test DeepSeek V3
        print("\n1. Testing DeepSeek V3...")
        test_text = "This is a test message from Grant Williams. I'm here with my guest Fred Hickey to discuss technology and markets."
        deepseek_response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are an expert at identifying speakers in podcast transcripts."},
                {"role": "user", "content": test_text}
            ],
            max_tokens=1000
        )
        print("DeepSeek V3 test successful!")
        print("Sample output:")
        print(deepseek_response.choices[0].message.content)
        
        # 2. Test Claude 3 Sonnet
        print("\n2. Testing Claude 3 Sonnet...")
        claude_response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": "This is a test message. Please analyze this brief text and respond with a short summary."
            }]
        )
        print("Claude 3 Sonnet test successful!")
        print("Sample output:")
        print(claude_response.content[0].text)
        
        # 3. Test GPT-3.5-turbo (fallback)
        print("\n3. Testing GPT-3.5-turbo (fallback)...")
        gpt_response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "This is a test message. Please respond with a short acknowledgment."}
            ],
            max_tokens=100
        )
        print("GPT-3.5-turbo test successful!")
        print("Sample output:")
        print(gpt_response.choices[0].message.content)
        
        print("\nAll API tests completed successfully!")
        
    except Exception as e:
        print(f"\nError during API testing: {str(e)}")
        raise

if __name__ == "__main__":
    test_apis() 