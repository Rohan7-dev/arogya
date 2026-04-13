 # 🩺 Arogya | Smart Health Triage

Arogya is a Streamlit-based, multilingual health triage assistant designed to help users describe their symptoms in plain language, receive a preliminary urgency assessment, and get practical next steps. 

Built with a modern conversational interface, Arogya bridges the gap between medical uncertainty and professional care by providing accessible, AI-driven guidance in multiple languages.

## ✨ Key Features
* **Multilingual Support:** Seamlessly process inputs and outputs in English, Malayalam, and Hindi.
* **Conversational UI:** A modern, persistent chat interface using Streamlit's session state.
* **AI-Powered Triage:** Uses Google's Gemini API to assess symptoms and output structured JSON data.
* **Comprehensive Guidance:** Provides Urgency Level (Low/Medium/High), Recommended Specialists, Immediate First-Aid, and Do's & Don'ts.
* **Visual Urgency Indicators:** Color-coded severity progress bars for quick comprehension.
* **Exportable Reports:** One-click PDF generation of the clinic summary to share with medical professionals.
* **Reliability Fallback:** Includes a local, rule-based triage engine to ensure the app remains fully functional even if the API hits rate limits.

## 🛠️ Tech Stack
* **Frontend:** Streamlit
* **AI Engine:** Google Generative AI (Gemini)
* **Translation:** deep-translator
* **Document Generation:** FPDF
* **Language:** Python 3.x

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/arogya.git](https://github.com/yourusername/arogya.git)
   cd arogya