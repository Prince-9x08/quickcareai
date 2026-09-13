from flask import Flask, render_template, request
from deep_translator import GoogleTranslator
from datetime import datetime

app = Flask(__name__)

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

HINDI_TO_ENGLISH_SYMPTOMS = {
    "सीने में दर्द": "chest pain",
    "बुखार": "fever",
    "तेज बुखार": "high fever",
    "खांसी": "cough",
    "सांस लेने में तकलीफ": "breathing difficulty",
    "खून बह रहा है": "bleeding",
    "सांप ने काटा": "snake bite",
    "पेट दर्द": "stomach pain",
    "सिर दर्द": "headache",
    "चोट": "injury",
}

def translate_to_english(text):
    text_stripped = text.strip()
    if text_stripped in HINDI_TO_ENGLISH_SYMPTOMS:
        return HINDI_TO_ENGLISH_SYMPTOMS[text_stripped]
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        error_indicators = ["Error 500", "Server Error", "That's an error"]
        if any(indicator in translated for indicator in error_indicators):
            return text
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text

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
    patient_name = request.form.get('patient_name', 'Not provided')
    patient_age = request.form.get('patient_age', 'Not provided')
    user_text = request.form.get('symptom_text')
    
    translated_text = translate_to_english(user_text)
    matched_symptom, urgency, advice = classify_symptom(translated_text)
    
    timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")
    
    return render_template(
        'result.html',
        patient_name=patient_name,
        patient_age=patient_age,
        original_text=user_text,
        translated_text=translated_text,
        matched_symptom=matched_symptom,
        urgency=urgency,
        advice=advice,
        timestamp=timestamp
    )

if __name__ == '__main__':
    app.run(debug=True)