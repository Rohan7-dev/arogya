import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from deep_translator import GoogleTranslator  # pyright: ignore[reportMissingImports]
import json
import os
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Arogya | Smart Health Triage",
    page_icon="🩺",
    layout="centered"
)
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #0f1117;
    }
    
    /* Card-like containers */
    .stChatMessage {
        background-color: #1e2130;
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 8px;
    }
    
    /* Title styling */
    h1 {
        color: #4CAF50;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #161822;
    }
    
    /* Progress bar color */
    .stProgress > div > div {
        background-color: #4CAF50;
    }
    
    /* Input box */
    .stChatInput input {
        background-color: #1e2130;
        color: white;
        border-radius: 20px;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
# Initialize Gemini API securely using Streamlit Secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Using gemini-1.5-flash as it is faster and natively supports JSON output
model = genai.GenerativeModel('gemini-pro')

# --- SIDEBAR: SETTINGS & DISCLAIMER ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Language Selector mapped to deep_translator language codes
    language_map = {
        "English": "en",
        "Malayalam": "ml",
        "Hindi": "hi"
    }
    
    selected_language = st.selectbox(
        "Choose your preferred language:",
        options=list(language_map.keys())
    )
    target_lang_code = language_map[selected_language]
    
    st.divider()
    
    # Mandatory Medical Disclaimer
    st.warning(
        "⚠️ **Disclaimer:** Arogya provides preliminary triage guidance "
        "and basic first-aid suggestions using AI. It is NOT a substitute "
        "for professional medical diagnosis or treatment. Always consult "
        "a doctor for medical emergencies."
    )

# --- MAIN UI: AROGYA ---
st.title("🩺 Arogya")
st.subheader("Your multilingual AI health assistant.")

st.write("Describe your symptoms below, and Arogya will help you understand the urgency, suggest basic first-aid, and recommend the right specialist.")

if "messages" not in st.session_state:
    st.session_state.messages = []


CRITICAL_SYMPTOMS = [
    "chest pain",
    "chest tightness",
    "shortness of breath",
    "breathing difficulty",
    "difficulty breathing",
    "stroke",
    "slurred speech",
    "face drooping",
    "one-sided weakness",
    "severe bleeding",
    "unconscious",
    "loss of consciousness",
    "seizure",
    "anaphylaxis",
    "blue lips",
    "severe allergic",
]

MODERATE_SYMPTOMS = [
    "fever",
    "vomiting",
    "diarrhea",
    "headache",
    "dizziness",
    "rash",
    "abdominal pain",
    "persistent pain",
    "cough",
    "wheezing",
    "high fever",
]

URGENCY_RANK = {
    "Low": 0,
    "Medium": 1,
    "High": 2,
}


UI_TEXT = {
    "en": {
        "urgency_label": "Urgency Level",
        "specialist_label": "Recommended Specialist",
        "first_aid_label": "Immediate First-Aid",
        "dos_donts_label": "Do's and Don'ts",
        "reported_symptoms_label": "Reported Symptoms",
        "ai_triage_urgency_label": "AI Triage Urgency",
        "target_specialist_label": "Target Specialist",
        "clinic_summary_title": "Take to Clinic Summary Card (Show to Doctor)",
        "download_pdf": "Download PDF Report",
        "pdf_title": "Arogya Triage Report",
        "pdf_generated": "Generated",
        "pdf_section": "Clinic Summary",
        "pdf_note": "This report provides preliminary AI-supported triage guidance and does not replace professional medical diagnosis.",
    },
    "ml": {
        "urgency_label": "അവസരതാ നില",
        "specialist_label": "ശുപാർശ ചെയ്യുന്ന വിദഗ്ധൻ",
        "first_aid_label": "ഉടൻ ചെയ്യേണ്ട പ്രാഥമിക ശുശ്രൂഷ",
        "dos_donts_label": "ചെയ്യേണ്ടതും ചെയ്യരുതാത്തതും",
        "reported_symptoms_label": "റിപ്പോർട്ട് ചെയ്ത ലക്ഷണങ്ങൾ",
        "ai_triage_urgency_label": "AI ട്രിയാജ് അടിയന്തിരത",
        "target_specialist_label": "ലക്ഷ്യ വിദഗ്ധൻ",
        "clinic_summary_title": "ഡോക്ടറെ കാണിക്കാൻ ക്ലിനിക് സംഗ്രഹ കാർഡ്",
        "download_pdf": "PDF റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്യുക",
        "pdf_title": "ആരോഗ്യ ട്രിയാജ് റിപ്പോർട്ട്",
        "pdf_generated": "സൃഷ്ടിച്ച സമയം",
        "pdf_section": "ക്ലിനിക് സംഗ്രഹം",
        "pdf_note": "ഈ റിപ്പോർട്ട് പ്രാഥമിക AI പിന്തുണയുള്ള ട്രിയാജ് മാർഗ്ഗനിർദ്ദേശമാണ്; ഇത് പ്രൊഫഷണൽ മെഡിക്കൽ നിർണയത്തിനോ ചികിത്സയ്ക്കോ പകരമല്ല.",
    },
    "hi": {
        "urgency_label": "तत्कालता स्तर",
        "specialist_label": "सुझाया गया विशेषज्ञ",
        "first_aid_label": "तुरंत प्राथमिक उपचार",
        "dos_donts_label": "क्या करें और क्या न करें",
        "reported_symptoms_label": "बताए गए लक्षण",
        "ai_triage_urgency_label": "AI ट्रायाज तत्कालता",
        "target_specialist_label": "लक्षित विशेषज्ञ",
        "clinic_summary_title": "डॉक्टर को दिखाने हेतु क्लिनिक सारांश कार्ड",
        "download_pdf": "PDF रिपोर्ट डाउनलोड करें",
        "pdf_title": "आरोग्य ट्रायाज रिपोर्ट",
        "pdf_generated": "जनरेटेड",
        "pdf_section": "क्लिनिक सारांश",
        "pdf_note": "यह रिपोर्ट प्रारंभिक AI-सहायता प्राप्त ट्रायाज मार्गदर्शन देती है और पेशेवर चिकित्सा निदान का विकल्प नहीं है।",
    },
}


def ui_text(key: str) -> str:
    lang_pack = UI_TEXT.get(target_lang_code, UI_TEXT["en"])
    return lang_pack.get(key, UI_TEXT["en"][key])


def to_english_text(text: str) -> str:
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception:
        return text


def display_text_for_user(text: str) -> str:
    if target_lang_code == 'en':
        return text
    return safe_translate_text(text, GoogleTranslator(source='auto', target=target_lang_code))


def find_unicode_font_path() -> str | None:
    candidates = [
        "C:/Windows/Fonts/Nirmala.ttf",
        "C:/Windows/Fonts/arialuni.ttf",
        "C:/Windows/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansMalayalam-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]

    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def detect_safety_urgency(symptoms_text: str) -> str:
    symptoms_lower = symptoms_text.lower()

    if any(term in symptoms_lower for term in CRITICAL_SYMPTOMS):
        return "High"

    if any(term in symptoms_lower for term in MODERATE_SYMPTOMS):
        return "Medium"

    return "Low"


def strongest_urgency(*levels: str) -> str:
    return max(levels, key=lambda level: URGENCY_RANK.get(level, 0))


def safe_translate_text(text: str, translator: GoogleTranslator) -> str:
    try:
        return translator.translate(text)
    except Exception:
        return text


def build_triage_response(user_symptoms: str) -> tuple[str, str, str]:
    english_symptoms = to_english_text(user_symptoms)
    localized_symptoms = display_text_for_user(user_symptoms)

    safety_urgency = detect_safety_urgency(english_symptoms)

    prompt = f"""
    You are a highly capable medical triage assistant. Analyze the following patient symptoms: "{english_symptoms}".
    Strict safety rule: If symptoms include chest pain, breathing difficulty/shortness of breath, stroke signs, severe bleeding, loss of consciousness, seizures, or anaphylaxis, you MUST classify urgency as "High" and must not downplay risk.
    If symptoms are concerning but not immediately life-threatening, prefer "Medium" over "Low".
    Provide a preliminary triage assessment. You must return exactly this JSON structure:
    {{
        "Urgency_Level": "Low, Medium, or High",
        "Recommended_Specialist": "Specific type of doctor to see",
        "Immediate_First_Aid": "1-2 brief, actionable steps to take immediately while waiting for a doctor",
        "Dos_and_Donts": "Exactly 2 do's and 2 don'ts for the condition"
    }}
    """

    try:
        response = model.generate_content(
            prompt,
        )

        triage_results = json.loads(response.text)

        # Normalize model output to avoid KeyError in non-English translation flows.
        triage_results.setdefault("Urgency_Level", "Low")
        triage_results.setdefault("Recommended_Specialist", "General physician")
        triage_results.setdefault("Immediate_First_Aid", "Rest, hydrate, and seek care if symptoms worsen.")
        triage_results.setdefault(
            "Dos_and_Donts",
            "Do: rest and hydrate; Do: monitor symptoms; Don't: ignore warning signs; Don't: self-medicate randomly.",
        )

        translated_results = triage_results.copy()

        model_urgency = triage_results.get("Urgency_Level", "Low")
        final_urgency = strongest_urgency(model_urgency, safety_urgency)

        if safety_urgency == "High":
            triage_results["Urgency_Level"] = "High"
            triage_results["Recommended_Specialist"] = "Emergency medicine doctor / emergency department"
            triage_results["Immediate_First_Aid"] = (
                "Call emergency services immediately. Do not drive yourself. Keep the person still and monitor breathing until help arrives."
            )
            triage_results["Dos_and_Donts"] = (
                "Do: call emergency services now; Do: keep the person calm and still; Don't: give food or drink; Don't: delay medical care."
            )
        elif safety_urgency == "Medium" and final_urgency == "Low":
            triage_results["Urgency_Level"] = "Medium"
        else:
            triage_results["Urgency_Level"] = final_urgency

        if target_lang_code != 'en':
            output_translator = GoogleTranslator(source='en', target=target_lang_code)
            translated_results["Urgency_Level"] = safe_translate_text(triage_results["Urgency_Level"], output_translator)
            translated_results["Recommended_Specialist"] = safe_translate_text(triage_results["Recommended_Specialist"], output_translator)
            translated_results["Immediate_First_Aid"] = safe_translate_text(triage_results["Immediate_First_Aid"], output_translator)
            translated_results["Dos_and_Donts"] = safe_translate_text(triage_results["Dos_and_Donts"], output_translator)

        urgency_check = triage_results["Urgency_Level"].lower()
        if "high" in urgency_check:
            urgency_tag = "error"
        elif "medium" in urgency_check:
            urgency_tag = "warning"
        else:
            urgency_tag = "success"

        assistant_message = (
            f"**{ui_text('urgency_label')}:** {translated_results['Urgency_Level']}\n\n"
            f"**👨‍⚕️ {ui_text('specialist_label')}:** {translated_results['Recommended_Specialist']}\n\n"
            f"**🚑 {ui_text('first_aid_label')}:** {translated_results['Immediate_First_Aid']}\n\n"
            f"**✅ {ui_text('dos_donts_label')}:** {translated_results['Dos_and_Donts']}"
        )

        summary_message = (
            f"**{ui_text('reported_symptoms_label')}:** {localized_symptoms}\n"
            f"**{ui_text('ai_triage_urgency_label')}:** {translated_results['Urgency_Level']}\n"
            f"**{ui_text('target_specialist_label')}:** {translated_results['Recommended_Specialist']}\n"
            f"**{ui_text('dos_donts_label')}:** {translated_results['Dos_and_Donts']}"
        )

        return assistant_message, summary_message, urgency_tag

    except (ResourceExhausted, Exception):
        return fallback_triage_response(english_symptoms)


def fallback_triage_response(english_symptoms: str) -> tuple[str, str, str]:
    safety_urgency = detect_safety_urgency(english_symptoms)

    if safety_urgency == "High":
        urgency_level = "High"
        specialist = "Emergency medicine doctor / emergency department"
        first_aid = "Call emergency services immediately. Do not drive yourself. Keep the person still and monitor breathing while waiting for help."
        dos_and_donts = "Do: call emergency services now; Do: keep the person calm and still; Don't: give food or drink; Don't: delay medical care."
        urgency_tag = "error"
    elif safety_urgency == "Medium":
        urgency_level = "Medium"
        specialist = "General physician"
        first_aid = "Rest, stay hydrated, and monitor symptoms closely. Seek medical care if symptoms worsen or do not improve."
        dos_and_donts = "Do: rest and drink fluids; Do: monitor symptoms; Don't: ignore worsening signs; Don't: self-medicate with random drugs."
        urgency_tag = "warning"
    else:
        urgency_level = "Low"
        specialist = "General physician"
        first_aid = "Rest, drink water, and observe symptoms. Book a routine appointment if they do not improve."
        dos_and_donts = "Do: rest and hydrate; Do: track symptoms; Don't: overexert yourself; Don't: ignore persistent symptoms."
        urgency_tag = "success"

    translated_urgency = urgency_level
    translated_specialist = specialist
    translated_first_aid = first_aid
    translated_dos_and_donts = dos_and_donts
    localized_symptoms = display_text_for_user(english_symptoms)

    if target_lang_code != 'en':
        output_translator = GoogleTranslator(source='en', target=target_lang_code)
        translated_urgency = safe_translate_text(urgency_level, output_translator)
        translated_specialist = safe_translate_text(specialist, output_translator)
        translated_first_aid = safe_translate_text(first_aid, output_translator)
        translated_dos_and_donts = safe_translate_text(dos_and_donts, output_translator)

    assistant_message = (
        f"**{ui_text('urgency_label')}:** {translated_urgency}\n\n"
        f"**👨‍⚕️ {ui_text('specialist_label')}:** {translated_specialist}\n\n"
        f"**🚑 {ui_text('first_aid_label')}:** {translated_first_aid}\n\n"
        f"**✅ {ui_text('dos_donts_label')}:** {translated_dos_and_donts}"
    )

    summary_message = (
        f"**{ui_text('reported_symptoms_label')}:** {localized_symptoms}\n"
        f"**{ui_text('ai_triage_urgency_label')}:** {translated_urgency}\n"
        f"**{ui_text('target_specialist_label')}:** {translated_specialist}\n"
        f"**{ui_text('dos_donts_label')}:** {translated_dos_and_donts}"
    )

    return assistant_message, summary_message, urgency_tag


def create_pdf(summary_text: str) -> bytes:
    try:
        from fpdf import FPDF
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PDF export is unavailable in the current Python environment. "
            "Install it with: python -m pip install fpdf"
        ) from exc

    safe_text = summary_text.replace("**", "")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    unicode_font_path = find_unicode_font_path()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    if unicode_font_path:
        pdf.add_font("ArogyaUnicode", "", unicode_font_path, uni=True)
        pdf.set_font("ArogyaUnicode", "", 16)
    else:
        pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, ui_text("pdf_title"), ln=True)

    if unicode_font_path:
        pdf.set_font("ArogyaUnicode", "", 10)
    else:
        pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 6, f"{ui_text('pdf_generated')}: {generated_at}", ln=True)
    pdf.set_text_color(0, 0, 0)

    pdf.ln(2)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)

    if unicode_font_path:
        pdf.set_font("ArogyaUnicode", "", 12)
    else:
        pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, ui_text("pdf_section"), ln=True)
    if unicode_font_path:
        pdf.set_font("ArogyaUnicode", "", 11)
    else:
        pdf.set_font("Helvetica", "", 11)

    for raw_line in safe_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" in line:
            label, value = line.split(":", 1)
            if unicode_font_path:
                pdf.set_font("ArogyaUnicode", "", 11)
            else:
                pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, f"{label.strip()}:", ln=True)
            if unicode_font_path:
                pdf.set_font("ArogyaUnicode", "", 11)
            else:
                pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 7, value.strip())
        else:
            pdf.multi_cell(0, 7, line)
        pdf.ln(1)

    pdf.ln(4)
    if unicode_font_path:
        pdf.set_font("ArogyaUnicode", "", 9)
    else:
        pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(110, 110, 110)
    pdf.multi_cell(
        0,
        5,
        ui_text("pdf_note"),
    )

    output = pdf.output(dest="S")
    return output.encode("latin-1") if isinstance(output, str) else bytes(output)


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("summary"):
            with st.expander(f"📄 {ui_text('clinic_summary_title')}"):
                st.write(message["summary"])

user_symptoms = st.chat_input("Describe your symptoms here...")

if user_symptoms:
    st.session_state.messages.append({"role": "user", "content": user_symptoms})
    with st.chat_message("user"):
        st.markdown(user_symptoms)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing your symptoms..."):
            try:
                assistant_message, summary_message, urgency_tag = build_triage_response(user_symptoms)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_message,
                        "summary": summary_message,
                        "urgency_tag": urgency_tag,
                    }
                )

                if urgency_tag == "error":
                    st.progress(1.0, text="Critical Urgency")
                    st.error(assistant_message)
                elif urgency_tag == "warning":
                    st.progress(0.6, text="Moderate Urgency")
                    st.warning(assistant_message)
                else:
                    st.progress(0.2, text="Low Urgency")
                    st.success(assistant_message)

                with st.expander(f"📄 {ui_text('clinic_summary_title')}"):
                    st.write(summary_message)
                    try:
                        pdf_data = create_pdf(summary_message)
                        st.download_button(
                            ui_text("download_pdf"),
                            data=pdf_data,
                            file_name="arogya_report.pdf",
                            mime="application/pdf",
                        )
                    except RuntimeError as pdf_error:
                        st.info(str(pdf_error))

            except ResourceExhausted:
                st.error(
                    "Gemini quota is exhausted for this API key right now. "
                    "Your secret is loading correctly, but the model call is being blocked by usage limits. "
                    "Try again later, switch to a key with available quota, or upgrade the Gemini API plan."
                )
            except Exception as e:
                error_message = f"An error occurred while processing your request: {e}"
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                st.error(error_message)

# --- EMERGENCY SECTION ---
st.divider()
st.subheader("🚨 Emergency Helplines")
col1, col2, col3 = st.columns(3)
col1.metric("National Emergency", "112")
col2.metric("Ambulance", "108")
col3.markdown("[🏥 Find Nearby Hospitals](https://www.google.com/maps/search/hospitals+clinics+near+me)", help="Opens Google Maps to search for nearby clinics")