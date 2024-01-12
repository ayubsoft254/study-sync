from flask import Flask, render_template

app = Flask(__name__)

# Define a route for the home page
@app.route('/')
def home():
    return render_template('index.html', message='Welcome to StudySync!')

if __name__ == '__main__':
    app.run(debug=True)
