from flask import Flask, render_template, request

app = Flask(__name__)

# Symptom rulebook: keyword -> (urgency, first-aid advice)
SYMPTOM_RULES = {
    "chest pain": ("Red", "Seek emergency care immediately. Keep the person calm and seated upright."),
    "breathing difficulty": ("Red", "Seek emergency care immediately. Loosen tight clothing, keep person upright."),
    "bleeding": ("Red", "Apply firm pressure to the wound with a clean cloth. Seek immediate care if bleeding doesn't stop."),
    "snake bite": ("Red", "Keep the person still and calm. Do not cut or suck the wound. Seek emergency care immediately."),
    "pregnancy": ("Red", "Seek immediate medical attention for any pregnancy complications."),
    "high fever": ("Yellow", "Give fluids, use a cool cloth on forehead. See a doctor if fever persists beyond a day."),
    "fever": ("Yellow", "Rest, stay hydrated, monitor temperature. See a doctor if it worsens."),
    "stomach pain": ("Yellow", "Rest, avoid solid food temporarily, stay hydrated. See a doctor if pain is severe or persistent."),
    "injury": ("Yellow", "Clean the wound, apply a bandage. See a doctor if there's swelling or you suspect a fracture."),
    "cough": ("Green", "Stay hydrated, rest. See a doctor if cough persists more than a week."),
    "headache": ("Green", "Rest in a quiet, dark room. Stay hydrated. See a doctor if severe or persistent."),
}

def classify_symptom(text):
    text_lower = text.lower()
    for symptom, (urgency, advice) in SYMPTOM_RULES.items():
        if symptom in text_lower:
            return symptom, urgency, advice
    return None, "Unknown", "Symptom not recognized. Please consult a health worker directly."

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    user_text = request.form.get('symptom_text')
    matched_symptom, urgency, advice = classify_symptom(user_text)
    
    return render_template(
        'result.html',
        original_text=user_text,
        matched_symptom=matched_symptom,
        urgency=urgency,
        advice=advice
    )

if __name__ == '__main__':
    app.run(debug=True)