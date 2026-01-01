"""Pydantic models for resume analysis data structures."""

from typing import Optional
from pydantic import BaseModel, Field


class ScoreResult(BaseModel):
    """Multi-criteria scoring result."""
    clarity: int = Field(ge=1, le=10, description="Grammar, readability, conciseness")
    impact: int = Field(ge=1, le=10, description="Action verbs, quantified achievements")
    relevance: int = Field(ge=1, le=10, description="Industry keywords, role alignment")
    completeness: int = Field(ge=1, le=10, description="All sections present, no gaps")
    ats_score: int = Field(ge=1, le=10, description="ATS compatibility and formatting")
    
    @property
    def overall(self) -> float:
        """Calculate weighted overall score."""
        weights = {
            "clarity": 0.20,
            "impact": 0.25,
            "relevance": 0.20,
            "completeness": 0.15,
            "ats_score": 0.20
        }
        return round(
            self.clarity * weights["clarity"] +
            self.impact * weights["impact"] +
            self.relevance * weights["relevance"] +
            self.completeness * weights["completeness"] +
            self.ats_score * weights["ats_score"],
            1
        )
    
    @property
    def grade(self) -> str:
        """Return letter grade based on overall score."""
        score = self.overall
        if score >= 9:
            return "A+"
        elif score >= 8:
            return "A"
        elif score >= 7:
            return "B"
        elif score >= 6:
            return "C"
        elif score >= 5:
            return "D"
        else:
            return "F"


class SectionFeedback(BaseModel):
    """Feedback for a specific resume section."""
    section_name: str
    content_found: bool = True
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    missing_elements: list[str] = Field(default_factory=list)


class RewriteSuggestion(BaseModel):
    """A single bullet point rewrite suggestion."""
    original: str
    improved: str
    explanation: str


class ResumeSection(BaseModel):
    """A detected section of the resume."""
    name: str
    content: str
    start_index: int = 0
    end_index: int = 0


class ResumeData(BaseModel):
    """Parsed resume data."""
    raw_text: str
    file_name: str
    file_type: str
    sections: list[ResumeSection] = Field(default_factory=list)
    word_count: int = 0
    
    def model_post_init(self, __context) -> None:
        """Calculate word count after initialization."""
        if self.raw_text and self.word_count == 0:
            self.word_count = len(self.raw_text.split())


class AnalysisResult(BaseModel):
    """Complete analysis result."""
    resume: ResumeData
    scores: ScoreResult
    section_feedback: list[SectionFeedback] = Field(default_factory=list)
    rewrite_suggestions: list[RewriteSuggestion] = Field(default_factory=list)
    overall_summary: str = ""
    
    @property
    def formatted_report(self) -> str:
        """Generate a formatted text report."""
        lines = [
            "=" * 60,
            "📄 RESUME ANALYSIS REPORT",
            "=" * 60,
            f"\nFile: {self.resume.file_name}",
            f"Word Count: {self.resume.word_count}",
            f"\n{'─' * 40}",
            "📊 SCORES",
            f"{'─' * 40}",
            f"  Overall: {self.scores.overall}/10 ({self.scores.grade})",
            f"  • Clarity:      {self.scores.clarity}/10",
            f"  • Impact:       {self.scores.impact}/10",
            f"  • Relevance:    {self.scores.relevance}/10",
            f"  • Completeness: {self.scores.completeness}/10",
            f"  • ATS Score:    {self.scores.ats_score}/10",
        ]
        
        if self.overall_summary:
            lines.extend([
                f"\n{'─' * 40}",
                "💡 SUMMARY",
                f"{'─' * 40}",
                self.overall_summary
            ])
        
        if self.section_feedback:
            lines.extend([
                f"\n{'─' * 40}",
                "📝 SECTION FEEDBACK",
                f"{'─' * 40}",
            ])
            for fb in self.section_feedback:
                lines.append(f"\n▸ {fb.section_name.upper()}")
                if fb.strengths:
                    lines.append("  ✅ Strengths:")
                    for s in fb.strengths:
                        lines.append(f"     • {s}")
                if fb.improvements:
                    lines.append("  🔧 Improvements:")
                    for i in fb.improvements:
                        lines.append(f"     • {i}")
                if fb.missing_elements:
                    lines.append("  ⚠️ Missing:")
                    for m in fb.missing_elements:
                        lines.append(f"     • {m}")
        
        if self.rewrite_suggestions:
            lines.extend([
                f"\n{'─' * 40}",
                "✨ REWRITE SUGGESTIONS",
                f"{'─' * 40}",
            ])
            for i, rw in enumerate(self.rewrite_suggestions, 1):
                lines.extend([
                    f"\n{i}. Original:",
                    f"   \"{rw.original}\"",
                    f"   Improved:",
                    f"   \"{rw.improved}\"",
                    f"   Why: {rw.explanation}"
                ])
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
