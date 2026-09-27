import os
import time
import re

from google import genai


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def evaluate_answer(question, answer, category, difficulty):

    prompt = f"""
You are an AI interviewer evaluating a college student's interview answer.

Interview Category:
{category}

Difficulty:
{difficulty}

Question:
{question}

Candidate Answer:
{answer}

Evaluate the candidate's answer.

IMPORTANT:
The first line of your response MUST be exactly:

SCORE: X/10

Where X is a number from 0 to 10.

Then provide:

RELEVANCE:
Explain whether the answer addresses the question.

CORRECTNESS:
Explain whether the answer is technically correct.

STRENGTHS:
Mention what the candidate did well.

IMPROVEMENTS:
Mention what the candidate should improve.

IDEAL ANSWER:
Give a concise and correct answer that the candidate can learn from.

Keep the feedback clear and suitable for a college student.
"""

    for attempt in range(5):

        try:

            response = client.models.generate_content(
                model="gemini-3.7-flash",
                contents=prompt
            )

            print("\n===== GEMINI FEEDBACK =====")
            print(response.text)
            print("===========================\n")

            return response.text

        except Exception as e:

            error_message = str(e)

            if "503" in error_message and attempt < 4:

                wait_time = 2 ** attempt

                print(
                    f"Gemini temporarily unavailable. "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

                continue

            print("\n===== GEMINI ERROR =====")
            print(error_message)
            print("========================\n")

            return """
AI_SERVICE_ERROR
"""


def extract_score(feedback):

    try:

        match = re.search(
            r"SCORE\s*:\s*(\d+(?:\.\d+)?)\s*/\s*10",
            feedback,
            re.IGNORECASE
        )

        if match:

            score = float(match.group(1))

            if 0 <= score <= 10:
                return score

        return None

    except Exception:

        return None