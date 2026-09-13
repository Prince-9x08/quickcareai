from flask import Flask, render_template, request
from deep_translator import GoogleTranslator
from datetime import datetime
from difflib import get_close_matches
import os
import re

app = Flask(__name__)

SYMPTOM_RULES = {
    "chest pain": {
        "urgency": "Red",
        "causes": ["Heart-related emergency", "Severe lung issue", "Muscle strain (less likely if severe)"],
        "reasoning": "Chest pain can signal a life-threatening cardiac or respiratory emergency and should never be ignored.",
        "next_steps": ["Seek emergency care immediately", "Keep the person calm and seated upright", "Do not let them exert themselves"],
        "warning_signs": ["Pain spreads to arm, jaw, or back", "Shortness of breath", "Sweating or dizziness"]
    },
    "breathing difficulty": {
        "urgency": "Red",
        "causes": ["Asthma attack", "Severe allergic reaction", "Respiratory infection"],
        "reasoning": "Difficulty breathing can rapidly become life-threatening and requires immediate attention.",
        "next_steps": ["Seek emergency care immediately", "Loosen tight clothing", "Keep the person upright, not lying flat"],
        "warning_signs": ["Lips or face turning blue", "Unable to speak full sentences", "Loss of consciousness"]
    },
    "bleeding": {
        "urgency": "Red",
        "causes": ["Deep wound or injury", "Internal bleeding (if no visible wound)"],
        "reasoning": "Uncontrolled bleeding can lead to shock if not managed quickly.",
        "next_steps": ["Apply firm pressure with a clean cloth", "Keep the injured area elevated if possible", "Seek immediate care if bleeding doesn't stop"],
        "warning_signs": ["Bleeding won't stop after 10 minutes of pressure", "Person becomes pale or faint", "Large or deep wound"]
    },
    "snake bite": {
        "urgency": "Red",
        "causes": ["Venomous snake bite"],
        "reasoning": "Snake venom can spread quickly through the body and requires emergency treatment.",
        "next_steps": ["Keep the person still and calm", "Do not cut or suck the wound", "Seek emergency care immediately"],
        "warning_signs": ["Swelling spreading quickly", "Difficulty breathing", "Blurred vision or drowsiness"]
    },
    "high fever": {
        "urgency": "Yellow",
        "causes": ["Viral infection", "Bacterial infection", "Heat-related illness"],
        "reasoning": "High fever can indicate the body is fighting a significant infection.",
        "next_steps": ["Give fluids", "Use a cool cloth on the forehead", "Monitor temperature regularly"],
        "warning_signs": ["Fever persists beyond a day", "Confusion or difficulty waking", "Rash accompanying fever"]
    },
    "fever": {
        "urgency": "Yellow",
        "causes": ["Viral infection", "Flu-like illness", "Other common infections"],
        "reasoning": "Fever can occur with several conditions. More information is needed to determine the likely cause.",
        "next_steps": ["Rest and stay hydrated", "Monitor your temperature", "Monitor whether symptoms worsen"],
        "warning_signs": ["Fever becomes severe or persistent", "You develop difficulty breathing", "Your condition rapidly worsens"]
    },
    "stomach pain": {
        "urgency": "Yellow",
        "causes": ["Indigestion", "Food poisoning", "Stomach infection"],
        "reasoning": "Stomach pain has many possible causes ranging from mild to serious.",
        "next_steps": ["Rest and avoid solid food temporarily", "Stay hydrated", "Monitor pain intensity"],
        "warning_signs": ["Pain is severe or worsening", "Pain concentrated in one area", "Fever accompanies the pain"]
    },
    "injury": {
        "urgency": "Yellow",
        "causes": ["Cut or wound", "Sprain or bruise", "Possible fracture"],
        "reasoning": "Injuries need cleaning and assessment to rule out deeper damage.",
        "next_steps": ["Clean the wound", "Apply a bandage", "Rest the affected area"],
        "warning_signs": ["Swelling or deformity", "Unable to move the area normally", "Signs of infection"]
    },
    "cough": {
        "urgency": "Green",
        "causes": ["Common cold", "Mild throat irritation", "Seasonal allergy"],
        "reasoning": "Most coughs are mild and resolve on their own within a week or two.",
        "next_steps": ["Stay hydrated", "Rest", "Use warm fluids to soothe throat"],
        "warning_signs": ["Cough persists more than a week", "Blood in mucus", "Accompanied by high fever"]
    },
    "headache": {
        "urgency": "Green",
        "causes": ["Tension or stress", "Dehydration", "Mild fatigue"],
        "reasoning": "Most headaches are mild and related to everyday factors like stress or dehydration.",
        "next_steps": ["Rest in a quiet, dark room", "Stay hydrated", "Avoid screen strain"],
        "warning_signs": ["Sudden, severe headache", "Headache with vision changes", "Persistent beyond 2 days"]
    },
        "difficulty breathing": {
        "urgency": "Red",
        "causes": ["Asthma attack", "Severe allergic reaction", "Respiratory infection"],
        "reasoning": "Difficulty breathing can rapidly become life-threatening and requires immediate attention.",
        "next_steps": ["Seek emergency care immediately", "Loosen tight clothing", "Keep the person upright, not lying flat"],
        "warning_signs": ["Lips or face turning blue", "Unable to speak full sentences", "Loss of consciousness"]
    },
    "heavy bleeding": {
        "urgency": "Red",
        "causes": ["Deep wound or injury", "Internal bleeding"],
        "reasoning": "Heavy bleeding can lead to shock quickly and needs urgent control.",
        "next_steps": ["Apply firm pressure with a clean cloth", "Keep the injured area elevated if possible", "Seek immediate care"],
        "warning_signs": ["Bleeding won't stop after 10 minutes of pressure", "Person becomes pale or faint", "Rapid breathing or weakness"]
    },
    "pregnancy complication": {
        "urgency": "Red",
        "causes": ["Pregnancy-related emergency", "Complication requiring immediate evaluation"],
        "reasoning": "Pregnancy complications can affect both mother and baby and need urgent medical evaluation.",
        "next_steps": ["Seek immediate medical attention", "Keep the person calm and lying on their side", "Do not delay transport to a facility"],
        "warning_signs": ["Severe abdominal pain", "Heavy bleeding", "Severe headache or vision changes"]
    },
    "unconscious": {
        "urgency": "Red",
        "causes": ["Fainting", "Head injury", "Severe underlying illness"],
        "reasoning": "Unconsciousness can indicate a serious underlying issue and requires immediate evaluation.",
        "next_steps": ["Check breathing", "Keep the person on their side", "Seek emergency care immediately"],
        "warning_signs": ["Person doesn't wake up after a minute", "Irregular or no breathing", "Repeated episodes"]
    },
    "unconsciousness": {
        "urgency": "Red",
        "causes": ["Fainting", "Head injury", "Severe underlying illness"],
        "reasoning": "Unconsciousness can indicate a serious underlying issue and requires immediate evaluation.",
        "next_steps": ["Check breathing", "Keep the person on their side", "Seek emergency care immediately"],
        "warning_signs": ["Person doesn't wake up after a minute", "Irregular or no breathing", "Repeated episodes"]
    },
    "seizure": {
        "urgency": "Red",
        "causes": ["Epilepsy", "High fever (in children)", "Head injury"],
        "reasoning": "Seizures can be dangerous, especially if prolonged or repeated, and need medical evaluation.",
        "next_steps": ["Do not restrain the person", "Clear the area of hard objects", "Seek emergency care after the seizure stops"],
        "warning_signs": ["Seizure lasts more than 5 minutes", "Person doesn't regain consciousness", "Repeated seizures without recovery"]
    },
    "severe burn": {
        "urgency": "Red",
        "causes": ["Thermal burn", "Chemical burn", "Electrical burn"],
        "reasoning": "Severe burns can lead to infection and shock, requiring prompt professional care.",
        "next_steps": ["Cool the burn with running water for 20 minutes", "Do not apply ice or ointments", "Seek emergency care"],
        "warning_signs": ["Burn covers a large area", "Skin appears white, charred, or leathery", "Signs of shock"]
    },
    "poisoning": {
        "urgency": "Red",
        "causes": ["Accidental ingestion", "Chemical exposure", "Food or drug poisoning"],
        "reasoning": "Poisoning can rapidly affect vital organs and needs urgent evaluation.",
        "next_steps": ["Do not induce vomiting unless told to", "Seek emergency care immediately", "Bring the substance container if possible"],
        "warning_signs": ["Difficulty breathing", "Loss of consciousness", "Seizures"]
    },
    "fracture": {
        "urgency": "Red",
        "causes": ["Fall or trauma", "Sports injury", "Direct impact"],
        "reasoning": "A suspected fracture needs immobilization and imaging to confirm and treat properly.",
        "next_steps": ["Do not move the injured area", "Support and immobilize it", "Seek emergency care immediately"],
        "warning_signs": ["Visible deformity", "Bone protruding through skin", "Severe swelling or numbness"]
    },
    "abdominal pain": {
        "urgency": "Yellow",
        "causes": ["Indigestion", "Infection", "Appendicitis (if severe and localized)"],
        "reasoning": "Abdominal pain has many possible causes ranging from mild to serious.",
        "next_steps": ["Rest and avoid solid food temporarily", "Stay hydrated", "Monitor pain intensity and location"],
        "warning_signs": ["Pain is severe or worsening", "Pain concentrated in lower right abdomen", "Fever accompanies the pain"]
    },
    "vomiting": {
        "urgency": "Yellow",
        "causes": ["Food poisoning", "Viral infection", "Motion sickness or indigestion"],
        "reasoning": "Vomiting can lead to dehydration if it continues, especially in children and elderly.",
        "next_steps": ["Sip small amounts of water frequently", "Avoid solid food temporarily", "Rest"],
        "warning_signs": ["Vomiting persists beyond a day", "Blood in vomit", "Signs of dehydration"]
    },
    "diarrhea": {
        "urgency": "Yellow",
        "causes": ["Food or water contamination", "Viral or bacterial infection", "Food intolerance"],
        "reasoning": "Diarrhea can quickly cause dehydration, particularly in children and the elderly.",
        "next_steps": ["Drink oral rehydration solution (ORS) or salted water", "Rest", "Avoid oily or spicy food"],
        "warning_signs": ["Persists beyond 2 days", "Blood in stool", "Signs of severe dehydration"]
    },
    "dehydration": {
        "urgency": "Yellow",
        "causes": ["Insufficient fluid intake", "Excessive sweating", "Diarrhea or vomiting"],
        "reasoning": "Dehydration affects the body's basic functions and needs prompt fluid replacement.",
        "next_steps": ["Drink ORS or water with a pinch of salt and sugar", "Rest in a cool place", "Monitor urine output"],
        "warning_signs": ["Confusion or extreme fatigue", "Little or no urination", "Rapid heartbeat"]
    },
    "body ache": {
        "urgency": "Yellow",
        "causes": ["Viral infection", "Overexertion", "Flu-like illness"],
        "reasoning": "Body aches often accompany infections or physical strain and usually resolve with rest.",
        "next_steps": ["Rest and stay hydrated", "Consider a warm compress", "Monitor for other symptoms"],
        "warning_signs": ["Pain is severe or localized", "Accompanied by high fever", "Persists beyond a few days"]
    },
    "dizziness": {
        "urgency": "Yellow",
        "causes": ["Low blood pressure", "Dehydration", "Inner ear issue"],
        "reasoning": "Dizziness can have several causes, some requiring prompt attention if recurrent.",
        "next_steps": ["Sit or lie down immediately", "Stay hydrated", "Avoid sudden movements"],
        "warning_signs": ["Fainting", "Chest pain accompanying dizziness", "Persistent or recurring episodes"]
    },
    "eye infection": {
        "urgency": "Yellow",
        "causes": ["Bacterial conjunctivitis", "Viral infection", "Allergic reaction"],
        "reasoning": "Eye infections can spread or worsen without proper care and hygiene.",
        "next_steps": ["Avoid touching or rubbing the eye", "Keep it clean", "Avoid sharing towels or pillows"],
        "warning_signs": ["Vision changes", "Severe pain or swelling", "Symptoms worsen after 2-3 days"]
    },
    "skin rash": {
        "urgency": "Yellow",
        "causes": ["Allergic reaction", "Skin infection", "Contact irritation"],
        "reasoning": "Skin rashes vary widely in cause and generally improve with basic care.",
        "next_steps": ["Avoid scratching", "Keep the area clean and dry", "Avoid known irritants"],
        "warning_signs": ["Rash spreads rapidly", "Accompanied by fever or difficulty breathing", "Blistering or open sores"]
    },
    "cold": {
        "urgency": "Green",
        "causes": ["Common viral cold", "Seasonal allergy", "Mild upper respiratory infection"],
        "reasoning": "Most colds are mild and resolve on their own within a week.",
        "next_steps": ["Rest and stay hydrated", "Warm fluids may help", "Get adequate sleep"],
        "warning_signs": ["Symptoms worsen after a week", "High fever develops", "Difficulty breathing"]
    },
    "sore throat": {
        "urgency": "Green",
        "causes": ["Viral infection", "Mild irritation", "Dry air or overuse of voice"],
        "reasoning": "Sore throats are usually mild and improve with basic home care.",
        "next_steps": ["Warm salt water gargle", "Stay hydrated", "Rest the voice"],
        "warning_signs": ["Persists more than a few days", "Difficulty swallowing", "High fever develops"]
    },
    "mild fatigue": {
        "urgency": "Green",
        "causes": ["Lack of sleep", "Overexertion", "Mild nutritional gaps"],
        "reasoning": "Mild fatigue is common and usually resolves with rest and proper nutrition.",
        "next_steps": ["Ensure adequate sleep", "Eat balanced meals", "Reduce physical strain temporarily"],
        "warning_signs": ["Fatigue is persistent or severe", "Accompanied by other symptoms", "Interferes with daily activities"]
    },
    "minor cut": {
        "urgency": "Green",
        "causes": ["Minor accidental injury"],
        "reasoning": "Minor cuts typically heal well with basic first aid.",
        "next_steps": ["Clean with water", "Apply a bandage", "Keep the area dry"],
        "warning_signs": ["Signs of infection (redness, pus)", "Wound doesn't heal after a week", "Deep or gaping wound"]
    },
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
    best_data = None
    best_rank = 0
    
    symptom_keys = list(SYMPTOM_RULES.keys())
    
    for symptom in symptom_keys:
        pattern = r'\b' + re.escape(symptom) + r'\b'
        if re.search(pattern, text_lower):
            data = SYMPTOM_RULES[symptom]
            rank = urgency_rank[data["urgency"]]
            if rank > best_rank:
                best_rank = rank
                best_match = symptom
                best_data = data
    
    if not best_match:
        words = text_lower.split()
        for word in words:
            close = get_close_matches(word, symptom_keys, n=1, cutoff=0.75)
            if close:
                symptom = close[0]
                data = SYMPTOM_RULES[symptom]
                rank = urgency_rank[data["urgency"]]
                if rank > best_rank:
                    best_rank = rank
                    best_match = symptom
                    best_data = data
    
    if best_match:
        return best_match, best_data
    return None, {
        "urgency": "Unknown",
        "causes": ["Not enough information to determine possible causes"],
        "reasoning": "This symptom description wasn't recognized by the system.",
        "next_steps": ["Consult a health worker directly for proper assessment"],
        "warning_signs": ["Any worsening of symptoms"]
    }

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    patient_name = request.form.get('patient_name', '').strip() or 'Not provided'
    patient_age_raw = request.form.get('patient_age', '').strip()
    
    # Validate age
    try:
        age_value = int(patient_age_raw)
        if age_value < 0 or age_value > 100:
            patient_age = "Invalid age"
        else:
            patient_age = age_value
    except (ValueError, TypeError):
        patient_age = "Not provided"
    
    user_text = request.form.get('symptom_text')
    
    translated_text = translate_to_english(user_text)
    matched_symptom, data = classify_symptom(translated_text)
    
    timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")
    
    urgency_labels = {"Red": "HIGH RISK", "Yellow": "MODERATE RISK", "Green": "LOW RISK", "Unknown": "UNCLASSIFIED"}
    
    return render_template(
        'result.html',
        patient_name=patient_name,
        patient_age=patient_age,
        original_text=user_text,
        translated_text=translated_text,
        matched_symptom=matched_symptom,
        urgency=data["urgency"],
        urgency_label=urgency_labels.get(data["urgency"], "UNCLASSIFIED"),
        causes=data["causes"],
        reasoning=data["reasoning"],
        next_steps=data["next_steps"],
        warning_signs=data["warning_signs"],
        timestamp=timestamp,
        advice=", ".join(data["next_steps"]),
        is_hindi=False
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)