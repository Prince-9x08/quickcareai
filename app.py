from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    user_text = request.form.get('symptom_text')
    result = f"You entered: {user_text}"
    return render_template('result.html', result=result, original_text=user_text)

if __name__ == '__main__':
    app.run(debug=True)