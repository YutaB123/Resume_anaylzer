"""
AI Resume Analyzer & Improver
A Gradio-based web application for analyzing and improving resumes.
"""

import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.parser import ResumeParser
from core.analyzer import ResumeAnalyzer
from core.scorer import ResumeScorer
from core.rewriter import ResumeRewriter
from models.schemas import AnalysisResult

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = None
parser = ResumeParser()


def get_client() -> OpenAI:
    """Get or create OpenAI client."""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set. Please create a .env file with your API key.")
        client = OpenAI(api_key=api_key)
    return client


def analyze_resume(file, progress=gr.Progress()) -> tuple[str, str, str, str, str]:
    """Main analysis function that processes the uploaded resume.
    
    Args:
        file: Uploaded file from Gradio
        progress: Gradio progress tracker
        
    Returns:
        Tuple of (summary, scores_display, feedback_display, rewrites_display, report)
    """
    if file is None:
        return (
            "⚠️ Please upload a resume file (PDF, DOCX, or TXT)",
            "",
            "",
            "",
            ""
        )
    
    try:
        # Get OpenAI client
        openai_client = get_client()
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        # Initialize components
        analyzer = ResumeAnalyzer(openai_client, model)
        scorer = ResumeScorer(openai_client, model)
        rewriter = ResumeRewriter(openai_client, model)
        
        # Parse the resume
        file_path = Path(file.name)
        with open(file.name, 'rb') as f:
            file_bytes = f.read()
        
        resume = parser.parse(file_bytes=file_bytes, file_name=file_path.name)
        
        if not resume.raw_text.strip():
            return (
                "⚠️ Could not extract text from the file. Please ensure the file contains readable text.",
                "",
                "",
                "",
                ""
            )
        
        # Detect sections
        progress(0.1, desc="📄 Parsing resume sections...")
        resume = analyzer.detect_sections(resume)
        
        # Generate scores
        progress(0.3, desc="📊 Scoring your resume...")
        scores = scorer.score(resume)
        scores_display = scorer.format_scores_display(scores)
        
        # Generate analysis feedback
        progress(0.5, desc="📝 Generating detailed feedback...")
        section_feedback, overall_summary = analyzer.analyze(resume)
        
        # Format feedback display
        feedback_lines = ["## 📝 Section-by-Section Feedback\n"]
        for fb in section_feedback:
            feedback_lines.append(f"### {fb.section_name.replace('_', ' ').title()}")
            
            if fb.strengths:
                feedback_lines.append("\n**✅ Strengths:**")
                for s in fb.strengths:
                    feedback_lines.append(f"- {s}")
            
            if fb.improvements:
                feedback_lines.append("\n**🔧 Areas for Improvement:**")
                for i in fb.improvements:
                    feedback_lines.append(f"- {i}")
            
            if fb.missing_elements:
                feedback_lines.append("\n**⚠️ Consider Adding:**")
                for m in fb.missing_elements:
                    feedback_lines.append(f"- {m}")
            
            feedback_lines.append("\n---\n")
        
        feedback_display = "\n".join(feedback_lines)
        
        # Generate rewrite suggestions
        progress(0.75, desc="✨ Creating improved bullet points...")
        rewrite_suggestions = rewriter.extract_and_rewrite(resume, max_bullets=6)
        
        # If no rewrites found, try direct extraction from raw text
        if not rewrite_suggestions:
            progress(0.8, desc="✨ Extracting content to improve...")
            # Try to find any substantial lines to rewrite
            lines = [line.strip() for line in resume.raw_text.split('\n') if len(line.strip()) > 40]
            # Filter to lines that look like work descriptions
            candidate_lines = [l for l in lines if not any(x in l.lower() for x in ['email', 'phone', '@', 'university', 'degree', 'bachelor', 'master'])]
            if candidate_lines:
                rewrite_suggestions = rewriter.rewrite_bullets(candidate_lines[:5])
        
        rewrites_display = rewriter.format_rewrites_display(rewrite_suggestions)
        
        # Create full analysis result for report
        progress(0.9, desc="📋 Generating final report...")
        analysis_result = AnalysisResult(
            resume=resume,
            scores=scores,
            section_feedback=section_feedback,
            rewrite_suggestions=rewrite_suggestions,
            overall_summary=overall_summary
        )
        
        # Summary with encouraging tone
        summary_display = f"""## 📄 Resume Analysis Complete!

**File:** {resume.file_name}  
**Word Count:** {resume.word_count} words  
**Sections Detected:** {len(resume.sections)}

---

### 💡 Overview

{overall_summary}

---

**Overall Grade: {scores.grade}** ({scores.overall}/10)

Use the tabs below to explore detailed feedback, scores, and improvement suggestions.
"""
        
        return (
            summary_display,
            scores_display,
            feedback_display,
            rewrites_display,
            analysis_result.formatted_report
        )
        
    except ValueError as e:
        return (
            f"⚠️ Configuration Error: {str(e)}",
            "",
            "",
            "",
            ""
        )
    except Exception as e:
        return (
            f"❌ Error analyzing resume: {str(e)}",
            "",
            "",
            "",
            ""
        )


def create_ui() -> gr.Blocks:
    """Create the Gradio interface."""
    
    # Custom CSS for better styling
    css = """
    .gradio-container {
        max-width: 1200px !important;
    }
    .score-box {
        padding: 20px;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .feedback-section {
        border-left: 4px solid #667eea;
        padding-left: 15px;
        margin: 10px 0;
    }
    """
    
    with gr.Blocks(
        title="AI Resume Analyzer",
    ) as app:
        
        # Header
        gr.Markdown("""
        # 📄 AI Resume Analyzer & Improver
        
        Upload your resume to get **instant AI-powered feedback**, **multi-criteria scoring**, 
        and **rewritten bullet points** to make your resume stand out.
        
        **Supported formats:** PDF, DOCX, TXT
        """)
        
        with gr.Row():
            # Left column - Upload
            with gr.Column(scale=1):
                file_input = gr.File(
                    label="📤 Upload Your Resume",
                    file_types=[".pdf", ".docx", ".doc", ".txt"],
                    type="filepath"
                )
                
                analyze_btn = gr.Button(
                    "🔍 Analyze Resume",
                    variant="primary",
                    size="lg"
                )
                
                gr.Markdown("""
                ---
                ### 🔒 Privacy Note
                Your resume is processed securely and not stored.
                Analysis is powered by OpenAI GPT-4.
                """)
            
            # Right column - Summary
            with gr.Column(scale=2):
                summary_output = gr.Markdown(
                    label="Summary",
                    value="*Upload a resume to see your analysis...*"
                )
        
        # Tabs for detailed results
        with gr.Tabs():
            with gr.TabItem("📊 Scores"):
                scores_output = gr.Markdown(
                    label="Scores",
                    value="*Scores will appear here after analysis...*"
                )
            
            with gr.TabItem("📝 Feedback"):
                feedback_output = gr.Markdown(
                    label="Feedback",
                    value="*Detailed feedback will appear here...*"
                )
            
            with gr.TabItem("✨ Rewrites"):
                rewrites_output = gr.Markdown(
                    label="Rewrites",
                    value="*Improved bullet points will appear here...*"
                )
            
            with gr.TabItem("📋 Full Report"):
                report_output = gr.Textbox(
                    label="Downloadable Report (Copy with Ctrl+A, Ctrl+C)",
                    lines=25,
                    value="*Full report will appear here for copying/downloading...*"
                )
        
        # Footer
        gr.Markdown("""
        ---
        ### 📈 Scoring Criteria
        
        | Criteria | What it measures |
        |----------|-----------------|
        | **Clarity** | Grammar, readability, and conciseness |
        | **Impact** | Action verbs and quantified achievements |
        | **Relevance** | Industry keywords and role alignment |
        | **Completeness** | All essential sections present |
        | **ATS Score** | Applicant Tracking System compatibility |
        
        ---
        *Built with ❤️ using Gradio and OpenAI*
        """)
        
        # Connect the analyze button
        analyze_btn.click(
            fn=analyze_resume,
            inputs=[file_input],
            outputs=[
                summary_output,
                scores_output,
                feedback_output,
                rewrites_output,
                report_output
            ]
        )
        
        # Also trigger on file upload
        file_input.change(
            fn=analyze_resume,
            inputs=[file_input],
            outputs=[
                summary_output,
                scores_output,
                feedback_output,
                rewrites_output,
                report_output
            ]
        )
    
    return app


# Main entry point
if __name__ == "__main__":
    app = create_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        share=False,
        show_error=True
    )
