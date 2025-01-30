from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session, Response, render_template_string
import pickle
import numpy as np
import google.generativeai as genai
import os
from dotenv import load_dotenv
import grpc
from jinja2 import Environment

# Load environment variables
load_dotenv()

# Load pickled data files
popular_df = pickle.load(open('popular.pkl', 'rb'))
pt = pickle.load(open('pt.pkl', 'rb'))
books = pickle.load(open('books.pkl', 'rb'))
similarity_scores = pickle.load(open('similarity_score.pkl', 'rb'))

jinja_env = Environment()
jinja_env.globals.update(enumerate=enumerate)

app = Flask(__name__)
app.jinja_env.globals.update(enumerate=enumerate)

@app.route('/')
def index():
    return render_template('index.html',
                           book_name=list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['Image-URL-M'].values),
                           votes=list(popular_df['num_ratings'].values),
                           ratings=list(popular_df['avg_rating'].values))

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

@app.route('/recommend_books', methods=['POST'])
def recommend():
    user_input = request.form.get('user_input')
    index = np.where(pt.index == user_input)[0][0]
    similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:9]

    data = []
    for i in similar_items:
        item = []
        temp_df = books[books['Book-Title'] == pt.index[i[0]]]
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

        data.append(item)
    
    return render_template('recommend.html', data=data)

@app.route('/generate_mcq', methods=['GET', 'POST'])
def generate_mcq():
    if request.method == 'POST':
        topic = request.form.get('topic')
        num_questions = int(request.form.get('num_questions'))
        mcqs = generate_mcq(topic, num_questions=num_questions)

        if mcqs:
            return render_template('mcq.html', mcqs=mcqs)
        else:
            flash('Failed to generate MCQs. Please try again.')
            return redirect(url_for('generate_mcq'))

    return render_template('generate_mcq.html')

def generate_mcq(topic, num_questions=5, api_key=None):
    """Generates multiple-choice questions on a given topic using the Google Generative AI."""
    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError("No API key found. Set GOOGLE_API_KEY environment variable or pass it as a parameter.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")

    prompt = f"""
    Generate {num_questions} multiple-choice questions about {topic}. 
    Each question should have 4 options (A, B, C, D).
    Indicate the correct option with the text "Correct Answer:" after question.
    Format as follows:
        Q1. Question text
        A. Option A
        B. Option B
        C. Option C
        D. Option D
    """

    try:
        response = model.generate_content(prompt)
        if response.text is None:
            raise ValueError("No text received from the model")

        raw_mcq_text = response.text
        mcqs = parse_mcq_text(raw_mcq_text)
        return mcqs
    except grpc.RpcError as e:
        print(f"gRPC Error: {e}")
        return []
    except Exception as e:
        print(f"Error generating MCQs: {e}")
        return []

def parse_mcq_text(raw_mcq_text):
    """Parses the raw text output from Google Generative AI into a list of MCQs."""
    mcqs = []
    lines = raw_mcq_text.strip().split("\n")

    i = 0
    while i < len(lines):
        if lines[i].startswith("Q"):
            question_line = lines[i]
            options = {"A": "", "B": "", "C": "", "D": ""}
            correct_answer = None

            for j in range(1, 6):
                if (i + j) < len(lines):
                    if lines[i + j].startswith("A. "):
                        options["A"] = lines[i + j][3:].strip()
                    elif lines[i + j].startswith("B. "):
                        options["B"] = lines[i + j][3:].strip()
                    elif lines[i + j].startswith("C. "):
                        options["C"] = lines[i + j][3:].strip()
                    elif lines[i + j].startswith("D. "):
                        options["D"] = lines[i + j][3:].strip()
                    elif lines[i + j].startswith("Correct Answer:"):
                        correct_answer = lines[i + j].split("Correct Answer:")[1].strip()

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

if __name__ == '__main__':
    app.secret_key = 'your_secret_key'
    app.run(debug=True)
