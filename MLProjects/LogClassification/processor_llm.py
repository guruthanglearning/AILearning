from dotenv import load_dotenv
from groq import Groq
import json

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq()

def classify_with_LLM(logmessage):
    """
    Generate a response using the Llama model via Groq
    
    Args:
        prompt (str): The input prompt
        model (str): The model to use (default: llama2-70b-4096)
    
    Returns:
        str: The generated response
    """
    prompt = f'''Classify the log message: in one of the below categories 
             1.) Workflow error, 2.) Deprecation Warning. If you can't figure out a category, return "Unclassified".
             "Only return the category name. No preamble. Log message: {logmessage}'''
    model="llama-3.3-70b-versatile"

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return completion.choices[0].message.content
    
    except Exception as e:
        print(f"Error generating response: {e}")
        return None

# Example usage
if __name__ == "__main__":
    
    log_messages = [ "User User123 logged in.",
        "Backup started at 2023-10-01 12:00:00.",
        "test"]
    
    for log_message in log_messages:
        response = classify_with_LLM(log_message)
        print(f"Model: LLM Log: {log_message} => Category: {response}")
    
