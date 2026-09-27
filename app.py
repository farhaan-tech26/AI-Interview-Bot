from flask import Flask, render_template, request, session, redirect
from dotenv import load_dotenv

load_dotenv()

from services.ai_service import evaluate_answer, extract_score
from database.database import create_tables, get_connection

app = Flask(__name__)

app.secret_key = "ai-interview-bot-secret-key"

create_tables()


# Interview questions
questions = {

    "Python": {

        "Easy": [
            "What is Python?",
            "What is a variable in Python?",
            "What are lists in Python?",
            "What is a loop?",
            "What is a function?"
        ],

        "Medium": [
            "What is the difference between a list and a tuple?",
            "What is the difference between == and is in Python?",
            "What are Python dictionaries?",
            "What is exception handling in Python?",
            "What is inheritance in Python?"
        ],

        "Hard": [
            "What are decorators in Python and why are they used?",
            "Explain Python generators and the yield keyword.",
            "What is the Global Interpreter Lock (GIL)?",
            "Explain shallow copy vs deep copy in Python.",
            "How does memory management work in Python?"
        ]
    },


    "Java": {

        "Easy": [
            "What is Java?",
            "What is a class in Java?",
            "What is an object?",
            "What is a variable?",
            "What is a method?"
        ],

        "Medium": [
            "What is inheritance in Java?",
            "What is polymorphism?",
            "What is method overloading?",
            "What is method overriding?",
            "What is exception handling?"
        ],

        "Hard": [
            "Explain the Java Virtual Machine (JVM).",
            "What is multithreading in Java?",
            "Explain the difference between HashMap and Hashtable.",
            "What is garbage collection in Java?",
            "Explain abstraction and interfaces in Java."
        ]
    },


    "DBMS": {

        "Easy": [
            "What is a database?",
            "What is DBMS?",
            "What is a table?",
            "What is a primary key?",
            "What is SQL?"
        ],

        "Medium": [
            "What is normalization?",
            "What is a foreign key?",
            "What are SQL joins?",
            "What is a transaction?",
            "What is ACID?"
        ],

        "Hard": [
            "Explain database indexing and its advantages.",
            "What is query optimization?",
            "Explain database concurrency control.",
            "What is deadlock in a database?",
            "Explain different types of database normalization."
        ]
    },


    "Computer Networks": {

        "Easy": [
            "What is a computer network?",
            "What is an IP address?",
            "What is a router?",
            "What is a switch?",
            "What is HTTP?"
        ],

        "Medium": [
            "What is the difference between TCP and UDP?",
            "What is DNS?",
            "What is the OSI model?",
            "What is subnetting?",
            "What is DHCP?"
        ],

        "Hard": [
            "Explain the TCP three-way handshake.",
            "How does DNS resolution work?",
            "Explain congestion control in TCP.",
            "What is network address translation (NAT)?",
            "Explain how routing protocols work."
        ]
    },


    "Web Development": {

        "Easy": [
            "What is HTML?",
            "What is CSS?",
            "What is JavaScript?",
            "What is a webpage?",
            "What is a hyperlink?"
        ],

        "Medium": [
            "What is the DOM?",
            "What is responsive web design?",
            "What is an API?",
            "What is HTTP?",
            "What is a REST API?"
        ],

        "Hard": [
            "Explain the difference between REST and SOAP.",
            "What is CORS and why is it required?",
            "Explain how JWT authentication works.",
            "What is server-side rendering?",
            "Explain web application security practices."
        ]
    },


    "HR Interview": {

        "Easy": [
            "Tell me about yourself.",
            "What are your hobbies?",
            "What are your strengths?",
            "What are your career goals?",
            "Why did you choose your degree?"
        ],

        "Medium": [
            "What are your weaknesses?",
            "Why should we hire you?",
            "Describe a challenging situation you faced.",
            "How do you handle teamwork?",
            "How do you handle deadlines?"
        ],

        "Hard": [
            "Tell me about a time you failed and what you learned from it.",
            "How would you handle a conflict with your manager?",
            "Describe a situation where you demonstrated leadership.",
            "How would you handle multiple high-priority tasks?",
            "Why should we choose you over other candidates?"
        ]
    }
}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():

    category = request.form.get("category")
    difficulty = request.form.get("difficulty")


    # Create database connection
    from database.database import get_connection

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        INSERT INTO interviews
        (category, difficulty)
        VALUES (?, ?)
    """, (category, difficulty))


    interview_id = cursor.lastrowid

    connection.commit()

    connection.close()


    # Store interview information
    session["interview_id"] = interview_id
    session["category"] = category
    session["difficulty"] = difficulty
    session["question_number"] = 0
    session["answers"] = []


    return redirect("/interview")

@app.route("/interview")
def interview():

    category = session.get("category")
    question_number = session.get("question_number", 0)

    question_list = questions.get(category, {}).get(
    session.get("difficulty"), []
)

    # Check whether interview is completed
    if question_number >= len(question_list):
        return redirect("/result")

    question = question_list[question_number]

    return render_template(
        "interview.html",
        category=category,
        difficulty=session.get("difficulty"),
        question_number=question_number + 1,
        total_questions=len(question_list),
        question=question
    )


@app.route("/answer", methods=["POST"])
def answer():

    answer_text = request.form.get("answer")

    category = session.get("category")
    difficulty = session.get("difficulty")

    question_number = session.get("question_number", 0)

    question_list = questions.get(category, {}).get(
        difficulty, []
    )

    question = question_list[question_number]

    # Send answer to Gemini
    feedback = evaluate_answer(
        question,
        answer_text,
        category,
        difficulty
    )

    # Extract AI score
    score = extract_score(feedback)

    # Check if Gemini evaluation failed
    if score is None:

        return """
        <html>
        <head>
            <title>AI Service Error</title>
        </head>

        <body>

            <h1>⚠️ AI Evaluation Temporarily Unavailable</h1>

            <p>
                Your answer was received, but Gemini AI could not
                evaluate it because the AI service is temporarily
                unavailable or the API quota has been reached.
            </p>

            <p>
                Please wait and try the interview again.
            </p>

            <br>

            <a href="/">
                <button>Go Home</button>
            </a>

        </body>
        </html>
        """

    # Save answer in database
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO answers
        (interview_id, question, answer, feedback, score)
        VALUES (?, ?, ?, ?, ?)
    """, (
        session.get("interview_id"),
        question,
        answer_text,
        feedback,
        score
    ))

    connection.commit()

    # Move to next question
    session["question_number"] += 1

    # Check if interview is completed
    if session["question_number"] >= len(question_list):

        cursor.execute("""
            SELECT SUM(score) AS total
            FROM answers
            WHERE interview_id = ?
        """, (
            session.get("interview_id"),
        ))

        result = cursor.fetchone()

        total_score = result["total"] or 0

        print("TOTAL SCORE:", total_score)

        # Save total score
        cursor.execute("""
            UPDATE interviews
            SET total_score = ?
            WHERE id = ?
        """, (
            total_score,
            session.get("interview_id")
        ))

        connection.commit()

        connection.close()

        return redirect("/result")

    connection.close()

    return redirect("/interview")
    
@app.route("/result")
def result():

    from database.database import get_connection

    connection = get_connection()

    cursor = connection.cursor()


    interview_id = session.get("interview_id")


    cursor.execute("""
        SELECT *
        FROM interviews
        WHERE id = ?
    """, (interview_id,))


    interview = cursor.fetchone()


    cursor.execute("""
        SELECT *
        FROM answers
        WHERE interview_id = ?
        ORDER BY id
    """, (interview_id,))


    answers = cursor.fetchall()


    connection.close()


    total_score = sum(
        answer["score"] for answer in answers
    )


    max_score = len(answers) * 10


    percentage = 0

    if max_score > 0:
        percentage = round(
            (total_score / max_score) * 100,
            2
        )


    return render_template(
        "result.html",

        category=interview["category"],

        difficulty=interview["difficulty"],

        answers=answers,

        total_score=total_score,

        max_score=max_score,

        percentage=percentage
    )

@app.route("/dashboard")
def dashboard():

    from database.database import get_connection

    connection = get_connection()
    cursor = connection.cursor()

    # Total interviews
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM interviews
    """)

    total_interviews = cursor.fetchone()["total"]


    # Total questions answered
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM answers
    """)

    total_questions = cursor.fetchone()["total"]


    # Average score
    cursor.execute("""
        SELECT AVG(
            (total_score * 100.0) /
            (SELECT COUNT(*)
             FROM answers
             WHERE answers.interview_id = interviews.id) / 10
        ) AS average
        FROM interviews
        WHERE total_score > 0
    """)

    result = cursor.fetchone()

    average_score = result["average"] or 0

    average_score = round(average_score, 2)


    # Recent interviews
    cursor.execute("""
        SELECT
            interviews.*,
            ROUND(
                (
                    total_score * 100.0
                    /
                    (
                        SELECT COUNT(*)
                        FROM answers
                        WHERE answers.interview_id = interviews.id
                    ) / 10
                ), 2
            ) AS percentage

        FROM interviews

        ORDER BY created_at DESC

        LIMIT 10
    """)

    interviews = cursor.fetchall()

    connection.close()


    return render_template(
        "dashboard.html",
        total_interviews=total_interviews,
        total_questions=total_questions,
        average_score=average_score,
        interviews=interviews
    )

if __name__ == "__main__":
    app.run(debug=True)