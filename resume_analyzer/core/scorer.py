"""Resume scoring module with multi-criteria evaluation."""

import json
from typing import Optional

from openai import OpenAI

from models.schemas import ResumeData, ScoreResult
from prompts.templates import SCORING_SYSTEM_PROMPT, get_scoring_user_prompt
from utils.helpers import truncate_text


class ResumeScorer:
    """Scorer for evaluating resumes on multiple criteria."""
    
    def __init__(self, client: OpenAI, model: str = "gpt-4o"):
        """Initialize the scorer.
        
        Args:
            client: OpenAI client instance
            model: Model to use for scoring
        """
        self.client = client
        self.model = model
        self._score_explanations: dict = {}
    
    def score(self, resume: ResumeData) -> ScoreResult:
        """Score a resume on 5 criteria.
        
        Args:
            resume: ResumeData object with raw_text
            
        Returns:
            ScoreResult with all criteria scores
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SCORING_SYSTEM_PROMPT},
                    {"role": "user", "content": get_scoring_user_prompt(
                        truncate_text(resume.raw_text)
                    )}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            score_data = json.loads(response.choices[0].message.content)
            
            # Store explanations for later access
            self._score_explanations = score_data.get("score_explanations", {})
            
            # Validate and clamp scores to 1-10 range
            def clamp_score(score: int) -> int:
                return max(1, min(10, int(score)))
            
            return ScoreResult(
                clarity=clamp_score(score_data.get("clarity", 5)),
                impact=clamp_score(score_data.get("impact", 5)),
                relevance=clamp_score(score_data.get("relevance", 5)),
                completeness=clamp_score(score_data.get("completeness", 5)),
                ats_score=clamp_score(score_data.get("ats_score", 5))
            )
            
        except Exception as e:
            # Return neutral scores on error
            return ScoreResult(
                clarity=5,
                impact=5,
                relevance=5,
                completeness=5,
                ats_score=5
            )
    
    @property
    def score_explanations(self) -> dict:
        """Get explanations for the most recent scores.
        
        Returns:
            Dictionary mapping criteria to explanations
        """
        return self._score_explanations
    
    def get_improvement_priority(self, scores: ScoreResult) -> list[str]:
        """Determine which areas to prioritize for improvement.
        
        Args:
            scores: ScoreResult object
            
        Returns:
            List of criteria names sorted by priority (lowest scores first)
        """
        score_dict = {
            "clarity": scores.clarity,
            "impact": scores.impact,
            "relevance": scores.relevance,
            "completeness": scores.completeness,
            "ats_score": scores.ats_score
        }
        
        # Sort by score ascending (lowest first = highest priority)
        sorted_criteria = sorted(score_dict.items(), key=lambda x: x[1])
        
        return [criteria for criteria, score in sorted_criteria]
    
    def format_scores_display(self, scores: ScoreResult) -> str:
        """Format scores for display with visual bars.
        
        Args:
            scores: ScoreResult object
            
        Returns:
            Formatted string with score visualization
        """
        from utils.helpers import format_score_bar, get_score_color
        
        lines = [
            f"📊 **Overall Score: {scores.overall}/10** ({scores.grade})",
            "",
            "**Breakdown:**",
            f"{get_score_color(scores.clarity)} Clarity: {format_score_bar(scores.clarity)}",
            f"{get_score_color(scores.impact)} Impact: {format_score_bar(scores.impact)}",
            f"{get_score_color(scores.relevance)} Relevance: {format_score_bar(scores.relevance)}",
            f"{get_score_color(scores.completeness)} Completeness: {format_score_bar(scores.completeness)}",
            f"{get_score_color(scores.ats_score)} ATS Score: {format_score_bar(scores.ats_score)}",
        ]
        
        # Add explanations if available
        if self._score_explanations:
            lines.append("\n**Score Details:**")
            for criteria, explanation in self._score_explanations.items():
                criteria_display = criteria.replace("_", " ").title()
                lines.append(f"• **{criteria_display}**: {explanation}")
        
        return "\n".join(lines)
