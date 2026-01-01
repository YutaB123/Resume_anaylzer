# 📄 AI Resume Analyzer & Improver

An intelligent resume analysis tool that provides empathetic feedback, multi-criteria scoring, and AI-powered rewrite suggestions.

## ✨ Features

- **Resume Parsing**: Upload PDF, DOCX, or TXT files
- **Section Detection**: Automatically identifies Contact, Summary, Experience, Education, Skills
- **5-Criteria Scoring**: Clarity, Impact, Relevance, Completeness, ATS Compatibility
- **Empathetic Feedback**: Constructive, actionable suggestions per section
- **AI Rewrites**: Transform weak bullet points into impactful achievements
- **Export**: Download your analysis report

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd resume_analyzer
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-key-here
```

### 3. Run the App

```bash
python app.py
```

Open your browser to `http://localhost:7860`

## 📊 Scoring Criteria

| Criteria | Description | Weight |
|----------|-------------|--------|
| **Clarity** | Grammar, readability, conciseness | 20% |
| **Impact** | Action verbs, quantified achievements | 25% |
| **Relevance** | Industry keywords, role alignment | 20% |
| **Completeness** | All sections present, no unexplained gaps | 15% |
| **ATS Score** | Formatting, parsability by tracking systems | 20% |

## 🛠️ Project Structure

```
resume_analyzer/
├── app.py                 # Main Gradio application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
│
├── core/
│   ├── parser.py         # PDF/DOCX text extraction
│   ├── analyzer.py       # Section detection & analysis
│   ├── scorer.py         # Multi-criteria scoring
│   └── rewriter.py       # AI bullet point improvements
│
├── prompts/
│   └── templates.py      # LLM prompt templates
│
├── models/
│   └── schemas.py        # Pydantic data models
│
└── utils/
    └── helpers.py        # Utility functions
```

## 🔒 Privacy

- Resumes are processed in-memory only
- No data is stored on disk
- API calls go directly to OpenAI

## 📝 License

MIT License - Feel free to use and modify!
