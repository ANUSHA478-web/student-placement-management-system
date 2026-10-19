
import os
from flask import Flask, Response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "templates", "index.html")

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "static"))

@app.route("/")
def home():
    with open(HTML_PATH, "r", encoding="utf-8") as file:
        return Response(file.read(), mimetype="text/html")

if __name__ == "__main__":
    print("RUNNING NEW WEB APP FILE")
    print("HTML path:", HTML_PATH)
    print("File exists:", os.path.isfile(HTML_PATH))
    app.run(debug=False, use_reloader=False)
