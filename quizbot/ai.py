import os
import json
from openai import OpenAI

def get_client():
    """
    Returns an OpenAI client instance if the API key is available.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def generate_question(topic_name, difficulty):
    """
    Generates a question using OpenAI.
    Returns a dict with 'question', 'options', and 'answer'.
    """
    client = get_client()
    
    if not client:
        # Fallback for when API key is missing
        print("Warning: OPENAI_API_KEY not found. Using fallback question.")
        return {
            "question": f"Sample question about {topic_name} at difficulty {difficulty} (Key missing)?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A"
        }

    prompt = (
        f"Generate a multiple choice question about '{topic_name}' "
        f"with difficulty level {difficulty} (out of 5). "
        "Return the response in JSON format with exactly three keys: "
        "'question' (string), 'options' (list of 4 strings), and 'answer' (the correct string from the options)."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful quiz bot. You output JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        data = json.loads(response.choices[0].message.content)
        return data
    except Exception as e:
        print(f"Error generating question: {e}")
        return {
            "question": f"Sample question about {topic_name} at difficulty {difficulty}?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A"
        }

def evaluate_answer(correct_answer, user_answer):
    """
    Simple string comparison for multiple choice.
    """
    return correct_answer.strip().lower() == user_answer.strip().lower()
