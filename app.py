
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "Student API is running!"})

@app.route("/student")
def student():
    return jsonify({
        "student_id": "24-00118",
        "name": "Lawrence Armada",
        "program": "BSIT",
        "year": 3,
        "section": "A-Hamilton"
    })

@app.route("/hello")
def hello():
    name = request.args.get("name", "Student")
    return jsonify({
        "message": f"Hello, {name}! Welcome to my API."
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
