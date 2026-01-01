"""Resume analysis module for section detection and feedback generation."""

import json
from typing import Optional

from openai import OpenAI

from models.schemas import ResumeData, SectionFeedback, ResumeSection
from prompts.templates import (
    ANALYSIS_SYSTEM_PROMPT,
    SECTION_DETECTION_PROMPT,
    get_analysis_user_prompt,
)
from utils.helpers import truncate_text


class ResumeAnalyzer:
    """Analyzer for detecting sections and generating feedback."""
    
    def __init__(self, client: OpenAI, model: str = "gpt-4o"):
        """Initialize the analyzer.
        
        Args:
            client: OpenAI client instance
            model: Model to use for analysis
        """
        self.client = client
        self.model = model
    
    def detect_sections(self, resume: ResumeData) -> ResumeData:
        """Detect and extract sections from resume text.
        
        Args:
            resume: ResumeData with raw_text populated
            
        Returns:
            ResumeData with sections populated
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SECTION_DETECTION_PROMPT},
                    {"role": "user", "content": truncate_text(resume.raw_text)}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            sections_data = json.loads(response.choices[0].message.content)
            
            sections = []
            for section_name, content in sections_data.items():
                if content and content != "null":
                    sections.append(ResumeSection(
                        name=section_name,
                        content=content
                    ))
            
            resume.sections = sections
            return resume
            
        except Exception as e:
            # If section detection fails, create a single "full" section
            resume.sections = [ResumeSection(
                name="full_resume",
                content=resume.raw_text
            )]
            return resume
    
    def analyze(self, resume: ResumeData) -> tuple[list[SectionFeedback], str]:
        """Generate empathetic feedback for the resume.
        
        Args:
            resume: ResumeData object (with or without sections)
            
        Returns:
            Tuple of (list of SectionFeedback, overall_summary string)
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": get_analysis_user_prompt(
                        truncate_text(resume.raw_text)
                    )}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            analysis_data = json.loads(response.choices[0].message.content)
            
            # Parse section feedback
            section_feedback = []
            for section_data in analysis_data.get("sections", []):
                feedback = SectionFeedback(
                    section_name=section_data.get("section_name", "Unknown"),
                    content_found=section_data.get("content_found", True),
                    strengths=section_data.get("strengths", []),
                    improvements=section_data.get("improvements", []),
                    missing_elements=section_data.get("missing_elements", [])
                )
                section_feedback.append(feedback)
            
            overall_summary = analysis_data.get("overall_summary", "")
            
            return section_feedback, overall_summary
            
        except Exception as e:
            # Return minimal feedback on error
            return [SectionFeedback(
                section_name="Error",
                content_found=False,
                strengths=[],
                improvements=[f"Analysis failed: {str(e)}"],
                missing_elements=[]
            )], "Unable to generate analysis. Please try again."
    
    def get_quick_summary(self, resume: ResumeData) -> str:
        """Generate a quick one-paragraph summary of the resume.
        
        Args:
            resume: ResumeData object
            
        Returns:
            Brief summary string
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful career advisor. Provide a brief, encouraging 2-3 sentence summary of this resume's overall impression."},
                    {"role": "user", "content": truncate_text(resume.raw_text, max_chars=5000)}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Unable to generate summary: {str(e)}"
