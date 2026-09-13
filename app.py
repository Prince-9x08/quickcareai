from flask import Flask, render_template, request
from deep_translator import GoogleTranslator
from datetime import datetime
from difflib import get_close_matches
import os
import re

app = Flask(__name__)

SYMPTOM_RULES = {
    # RED — emergency
    "chest pain": ("Red", "Seek emergency care immediately. Keep the person calm and seated upright."),
    "breathing difficulty": ("Red", "Seek emergency care immediately. Loosen tight clothing, keep person upright."),
    "difficulty breathing": ("Red", "Seek emergency care immediately. Loosen tight clothing, keep person upright."),
    "bleeding": ("Red", "Apply firm pressure to the wound with a clean cloth. Seek immediate care if bleeding doesn't stop."),
    "heavy bleeding": ("Red", "Apply firm pressure to the wound with a clean cloth. Seek immediate care if bleeding doesn't stop."),
    "snake bite": ("Red", "Keep the person still and calm. Do not cut or suck the wound. Seek emergency care immediately."),
    "pregnancy complication": ("Red", "Seek immediate medical attention for any pregnancy complications."),
    "unconscious": ("Red", "Check breathing. Keep the person on their side. Seek emergency care immediately."),
    "unconsciousness": ("Red", "Check breathing. Keep the person on their side. Seek emergency care immediately."),
    "seizure": ("Red", "Do not restrain the person. Clear the area of hard objects. Seek emergency care after the seizure stops."),
    "severe burn": ("Red", "Cool the burn with running water for 20 minutes. Do not apply ice or ointments. Seek emergency care."),
    "poisoning": ("Red", "Do not induce vomiting unless told to. Seek emergency care immediately with the substance container if possible."),
    "fracture": ("Red", "Do not move the injured area. Support and immobilize it. Seek emergency care immediately."),

    # YELLOW — needs attention soon
    "high fever": ("Yellow", "Give fluids, use a cool cloth on forehead. See a doctor if fever persists beyond a day."),
    "fever": ("Yellow", "Rest, stay hydrated, monitor temperature. See a doctor if it worsens."),
    "stomach pain": ("Yellow", "Rest, avoid solid food temporarily, stay hydrated. See a doctor if pain is severe or persistent."),
    "abdominal pain": ("Yellow", "Rest, avoid solid food temporarily, stay hydrated. See a doctor if pain is severe or persistent."),
    "injury": ("Yellow", "Clean the wound, apply a bandage. See a doctor if there's swelling or you suspect a fracture."),
    "vomiting": ("Yellow", "Sip small amounts of water frequently. See a doctor if vomiting persists beyond a day."),
    "diarrhea": ("Yellow", "Drink oral rehydration solution (ORS) or salted water. See a doctor if it persists beyond 2 days."),
    "dehydration": ("Yellow", "Drink ORS or water with a pinch of salt and sugar. See a doctor if symptoms worsen."),
    "body ache": ("Yellow", "Rest and stay hydrated. See a doctor if pain is severe or accompanied by fever."),
    "dizziness": ("Yellow", "Sit or lie down immediately. Stay hydrated. See a doctor if it persists or recurs."),
    "eye infection": ("Yellow", "Avoid touching or rubbing the eye. Keep it clean. See a doctor if redness or pain worsens."),
    "skin rash": ("Yellow", "Avoid scratching. Keep the area clean and dry. See a doctor if it spreads or worsens."),

    # GREEN — mild, routine
    "cough": ("Green", "Stay hydrated, rest. See a doctor if cough persists more than a week."),
    "headache": ("Green", "Rest in a quiet, dark room. Stay hydrated. See a doctor if severe or persistent."),
    "cold": ("Green", "Rest, stay hydrated, warm fluids may help. See a doctor if symptoms worsen or persist."),
    "sore throat": ("Green", "Warm salt water gargle, stay hydrated. See a doctor if it persists more than a few days."),
    "mild fatigue": ("Green", "Rest and ensure adequate sleep and nutrition. See a doctor if fatigue is persistent or severe."),
    "minor cut": ("Green", "Clean with water, apply a bandage. See a doctor if it doesn't heal or shows signs of infection."),
}

HINDI_TO_ENGLISH_SYMPTOMS = {
    # Red
    "सीने में दर्द": "chest pain",
    "छाती में दर्द": "chest pain",
    "सांस लेने में तकलीफ": "breathing difficulty",
    "सांस फूलना": "breathing difficulty",
    "खून बह रहा है": "bleeding",
    "बहुत खून बह रहा है": "heavy bleeding",
    "सांप ने काटा": "snake bite",
    "बेहोश": "unconscious",
    "बेहोशी": "unconsciousness",
    "दौरा पड़ना": "seizure",
    "गंभीर जलना": "severe burn",
    "जहर खा लिया": "poisoning",
    "हड्डी टूटना": "fracture",

    # Yellow
    "तेज बुखार": "high fever",
    "बुखार": "fever",
    "पेट दर्द": "stomach pain",
    "पेट में दर्द": "abdominal pain",
    "चोट": "injury",
    "उल्टी": "vomiting",
    "दस्त": "diarrhea",
    "पानी की कमी": "dehydration",
    "शरीर में दर्द": "body ache",
    "चक्कर आना": "dizziness",
    "आंख में संक्रमण": "eye infection",
    "त्वचा पर चकत्ते": "skin rash",

    # Green
    "खांसी": "cough",
    "सिर दर्द": "headache",
    "जुकाम": "cold",
    "गले में खराश": "sore throat",
    "हल्की थकान": "mild fatigue",
    "छोटा घाव": "minor cut",
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
    except Exception:
        # Any translation failure (rate limit, network, etc.) - just use original text
        return text

def classify_symptom(text):
    text_lower = text.lower()
    urgency_rank = {"Red": 3, "Yellow": 2, "Green": 1}
    
    best_match = None
    best_urgency = None
    best_advice = None
    best_rank = 0
    
    symptom_keys = list(SYMPTOM_RULES.keys())
    
    # Exact match with word boundaries (handles multi-word symptoms too)
    for symptom in symptom_keys:
        pattern = r'\b' + re.escape(symptom) + r'\b'
        if re.search(pattern, text_lower):
            urgency, advice = SYMPTOM_RULES[symptom]
            rank = urgency_rank[urgency]
            if rank > best_rank:
                best_rank = rank
                best_match = symptom
                best_urgency = urgency
                best_advice = advice
    
    # Fuzzy match fallback, only if no exact match found
    if not best_match:
        words = text_lower.split()
        for word in words:
            close = get_close_matches(word, symptom_keys, n=1, cutoff=0.75)
            if close:
                symptom = close[0]
                urgency, advice = SYMPTOM_RULES[symptom]
                rank = urgency_rank[urgency]
                if rank > best_rank:
                    best_rank = rank
                    best_match = symptom
                    best_urgency = urgency
                    best_advice = advice
    
    if best_match:
        return best_match, best_urgency, best_advice
    return None, "Unknown", "Symptom not recognized. Please consult a health worker directly."
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
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)