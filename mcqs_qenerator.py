import google.generativeai as genai
import os
from dotenv import load_dotenv
import grpc

# Load environment variables
load_dotenv()

def generate_mcq(topic, num_questions=5, api_key=None):
    """Generates multiple-choice questions on a given topic using the Gemini API.

    Args:
        topic: The topic to generate questions for.
        num_questions: The number of questions to generate.
        api_key: Google API key.

    Returns:
        A list of dictionaries, where each dictionary represents a question
        and contains the question text, options, and the correct answer.
    """

    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError("No API key found. Set GOOGLE_API_KEY environment variable or pass it as a parameter.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")

    prompt = f"""
    Generate {num_questions} multiple-choice questions about {topic}. 
    Each question should have 4 options (A, B, C, D).
    Indicate the correct option with the text  "Correct Answer:" after question.
    Format as follows:
        Q1. Question text
        A. Option A
        B. Option B
        C. Option C
        D. Option D
        Correct Answer: (A or B or C or D)
    """

    try:
        response = model.generate_content(prompt)
        
        if response.text is None:
           raise ValueError("No text received from the model")

        raw_mcq_text = response.text
        
        # Parse the response
        mcqs = parse_mcq_text(raw_mcq_text)

        return mcqs
    except grpc.RpcError as e:
        print(f"gRPC Error: {e}")
        return []
    except Exception as e:
        print(f"Error generating MCQs: {e}")
        return []

def parse_mcq_text(raw_mcq_text):
    """Parses the raw text output from Gemini into a list of MCQs."""
    mcqs = []
    lines = raw_mcq_text.strip().split("\n")
    
    i = 0
    while i < len(lines):
        if lines[i].startswith("Q"):
            question_line = lines[i]
            options = {}
            
            if (i+1) < len(lines):
                if lines[i+1].startswith("A."):
                  options["A"] = lines[i+1].split("A.")[1].strip()
                else:
                  i += 1
                  continue 
            else:
               i += 1
               continue
            
            if (i+2) < len(lines):
                if lines[i+2].startswith("B."):
                  options["B"] = lines[i+2].split("B.")[1].strip()
                else:
                  i += 1
                  continue
            else:
               i += 1
               continue

            if (i+3) < len(lines):
                if lines[i+3].startswith("C."):
                   options["C"] = lines[i+3].split("C.")[1].strip()
                else:
                  i += 1
                  continue
            else:
               i += 1
               continue
               
            if (i+4) < len(lines):
                if lines[i+4].startswith("D."):
                   options["D"] = lines[i+4].split("D.")[1].strip()
                else:
                   i+=1
                   continue
            else:
               i+=1
               continue
               
            if (i+5) < len(lines):
                if lines[i+5].startswith("Correct Answer:"):
                    correct_answer = lines[i+5].split("Correct Answer:")[1].strip()
                else:
                    correct_answer = None
            else:
                correct_answer = None
                
            mcq = {
                "question": question_line.split(". ", 1)[1],
                "options": options,
                "correct_answer": correct_answer,
            }
            mcqs.append(mcq)
            
            i += 6
        else:
            i += 1

    return mcqs

def display_mcqs(mcqs):
    """Displays the MCQs in a user-friendly format."""
    if not mcqs:
        print("No MCQs to display.")
        return

    for i, mcq in enumerate(mcqs):
        print(f"\nQ{i + 1}. {mcq['question']}")
        for key, value in mcq["options"].items():
            print(f"   {key}. {value}")
        print(f"   Correct Answer: {mcq['correct_answer']}")

def get_user_answer(mcq_index, mcq):
    """Gets the user's answer for a given question."""
    while True:
        user_answer = input(f"Your answer for Q{mcq_index + 1} (A, B, C, or D): ").upper()
        if user_answer in mcq["options"].keys():
           return user_answer
        else:
           print("Invalid option. Please choose A, B, C, or D.")
           
def evaluate_quiz(mcqs):
     """Evaluates the user's answers and provides a score."""
     score = 0
     for i, mcq in enumerate(mcqs):
          user_answer = get_user_answer(i, mcq)
          if user_answer == mcq["correct_answer"]:
             score += 1
             print("Correct!")
          else:
            print(f"Incorrect. The correct answer is {mcq['correct_answer']}")
     print(f"\nQuiz finished. Your score: {score}/{len(mcqs)}")

if __name__ == "__main__":
    topic = input("Enter the topic for the MCQ questions: ")
    num_questions = int(input("Enter the number of questions you want to generate: "))
    
    mcqs = generate_mcq(topic, num_questions=num_questions)

    if mcqs:
        display_mcqs(mcqs)
        
        # Option to take quiz
        take_quiz = input("Do you want to take the quiz? (yes/no): ").lower()
        if take_quiz == "yes":
            evaluate_quiz(mcqs)
