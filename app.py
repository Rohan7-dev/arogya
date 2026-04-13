import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from deep_translator import GoogleTranslator  # pyright: ignore[reportMissingImports]
import json
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


def build_triage_response(user_symptoms: str) -> tuple[str, str, str]:
    if target_lang_code != 'en':
        english_symptoms = GoogleTranslator(source='auto', target='en').translate(user_symptoms)
    else:
        english_symptoms = user_symptoms

    prompt = f"""
    You are a highly capable medical triage assistant. Analyze the following patient symptoms: "{english_symptoms}".
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
        translated_results = triage_results.copy()

        if target_lang_code != 'en':
            output_translator = GoogleTranslator(source='en', target=target_lang_code)
            translated_results["Urgency_Level"] = output_translator.translate(triage_results["Urgency_Level"])
            translated_results["Recommended_Specialist"] = output_translator.translate(triage_results["Recommended_Specialist"])
            translated_results["Immediate_First_Aid"] = output_translator.translate(triage_results["Immediate_First_Aid"])
            translated_results["Dos_and_Donts"] = output_translator.translate(triage_results["Dos_and_Donts"])

        urgency_check = triage_results["Urgency_Level"].lower()
        if "high" in urgency_check:
            urgency_tag = "error"
        elif "medium" in urgency_check:
            urgency_tag = "warning"
        else:
            urgency_tag = "success"

        assistant_message = (
            f"**Urgency Level:** {translated_results['Urgency_Level']}\n\n"
            f"**👨‍⚕️ Recommended Specialist:** {translated_results['Recommended_Specialist']}\n\n"
            f"**🚑 Immediate First-Aid:** {translated_results['Immediate_First_Aid']}\n\n"
            f"**✅ Do's and Don'ts:** {translated_results['Dos_and_Donts']}"
        )

        summary_message = (
            f"**Reported Symptoms:** {english_symptoms}\n"
            f"**AI Triage Urgency:** {triage_results['Urgency_Level']}\n"
            f"**Target Specialist:** {triage_results['Recommended_Specialist']}\n"
            f"**Do's and Don'ts:** {triage_results['Dos_and_Donts']}"
        )

        return assistant_message, summary_message, urgency_tag

    except (ResourceExhausted, Exception):
        return fallback_triage_response(english_symptoms)


def fallback_triage_response(english_symptoms: str) -> tuple[str, str, str]:
    symptoms_lower = english_symptoms.lower()

    high_risk_terms = [
        "chest pain",
        "shortness of breath",
        "difficulty breathing",
        "unconscious",
        "fainting",
        "severe bleeding",
        "stroke",
        "seizure",
        "suicidal",
        "confusion",
    ]
    medium_risk_terms = [
        "fever",
        "vomiting",
        "diarrhea",
        "headache",
        "dizziness",
        "rash",
        "abdominal pain",
        "pain",
        "cough",
    ]

    if any(term in symptoms_lower for term in high_risk_terms):
        urgency_level = "High"
        specialist = "Emergency medicine doctor"
        first_aid = "Call emergency services immediately. Keep the person still and monitor breathing while waiting for help."
        dos_and_donts = "Do: call emergency services right away; Do: keep the person calm and still; Don't: give food or drink; Don't: delay medical help."
        urgency_tag = "error"
    elif any(term in symptoms_lower for term in medium_risk_terms):
        urgency_level = "Medium"
        specialist = "General physician"
        first_aid = "Rest, stay hydrated, and monitor symptoms closely. Seek medical care if symptoms worsen."
        dos_and_donts = "Do: rest and drink fluids; Do: monitor symptoms; Don't: ignore worsening signs; Don't: self-medicate with random drugs."
        urgency_tag = "warning"
    else:
        urgency_level = "Low"
        specialist = "General physician"
        first_aid = "Rest, drink water, and observe symptoms. Book a routine appointment if they do not improve."
        dos_and_donts = "Do: rest and hydrate; Do: track symptoms; Don't: overexert yourself; Don't: ignore persistent symptoms."
        urgency_tag = "success"

    assistant_message = (
        f"**Urgency Level:** {urgency_level}\n\n"
        f"**👨‍⚕️ Recommended Specialist:** {specialist}\n\n"
        f"**🚑 Immediate First-Aid:** {first_aid}\n\n"
        f"**✅ Do's and Don'ts:** {dos_and_donts}"
    )

    summary_message = (
        f"**Reported Symptoms:** {english_symptoms}\n"
        f"**AI Triage Urgency:** {urgency_level}\n"
        f"**Target Specialist:** {specialist}\n"
        f"**Do's and Don'ts:** {dos_and_donts}"
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

    safe_text = summary_text.replace("**", "").encode("latin-1", errors="replace").decode("latin-1")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Arogya Triage Report", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 6, f"Generated: {generated_at}", ln=True)
    pdf.set_text_color(0, 0, 0)

    pdf.ln(2)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Clinic Summary", ln=True)
    pdf.set_font("Helvetica", "", 11)

    for raw_line in safe_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" in line:
            label, value = line.split(":", 1)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, f"{label.strip()}:", ln=True)
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 7, value.strip())
        else:
            pdf.multi_cell(0, 7, line)
        pdf.ln(1)

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(110, 110, 110)
    pdf.multi_cell(
        0,
        5,
        "This report provides preliminary AI-supported triage guidance and does not replace professional medical diagnosis.",
    )

    return pdf.output(dest="S").encode("latin-1")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("summary"):
            with st.expander("📄 Take to Clinic Summary Card (Show to Doctor)"):
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

                with st.expander("📄 Take to Clinic Summary Card (Show to Doctor)"):
                    st.write(summary_message)
                    try:
                        pdf_data = create_pdf(summary_message)
                        st.download_button(
                            "Download PDF Report",
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