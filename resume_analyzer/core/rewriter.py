"""Resume rewriting module for improving bullet points."""

import json
from typing import Optional

from openai import OpenAI

from models.schemas import ResumeData, RewriteSuggestion
from prompts.templates import REWRITE_SYSTEM_PROMPT, get_rewrite_user_prompt
from utils.helpers import extract_bullet_points


class ResumeRewriter:
    """Rewriter for improving resume bullet points and content."""
    
    def __init__(self, client: OpenAI, model: str = "gpt-4o"):
        """Initialize the rewriter.
        
        Args:
            client: OpenAI client instance
            model: Model to use for rewriting
        """
        self.client = client
        self.model = model
    
    def extract_and_rewrite(self, resume: ResumeData, max_bullets: int = 8) -> list[RewriteSuggestion]:
        """Extract bullet points from resume and generate improvements.
        
        Args:
            resume: ResumeData object
            max_bullets: Maximum number of bullets to rewrite
            
        Returns:
            List of RewriteSuggestion objects
        """
        # Extract bullet points from the resume
        bullets = extract_bullet_points(resume.raw_text, max_bullets=max_bullets)
        
        if not bullets:
            # If no bullets found, try to extract from experience section
            for section in resume.sections:
                if section.name.lower() in ['experience', 'work', 'employment']:
                    bullets = extract_bullet_points(section.content, max_bullets=max_bullets)
                    break
        
        if not bullets:
            return []
        
        return self.rewrite_bullets(bullets)
    
    def rewrite_bullets(self, bullet_points: list[str]) -> list[RewriteSuggestion]:
        """Rewrite a list of bullet points.
        
        Args:
            bullet_points: List of original bullet point strings
            
        Returns:
            List of RewriteSuggestion objects
        """
        if not bullet_points:
            return []
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                    {"role": "user", "content": get_rewrite_user_prompt(bullet_points)}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            rewrite_data = json.loads(response.choices[0].message.content)
            
            suggestions = []
            for rewrite in rewrite_data.get("rewrites", []):
                suggestions.append(RewriteSuggestion(
                    original=rewrite.get("original", ""),
                    improved=rewrite.get("improved", ""),
                    explanation=rewrite.get("explanation", "")
                ))
            
            return suggestions
            
        except Exception as e:
            return []
    
    def rewrite_single(self, text: str, context: str = "") -> RewriteSuggestion:
        """Rewrite a single piece of text.
        
        Args:
            text: Text to rewrite
            context: Optional context (e.g., "summary", "bullet point")
            
        Returns:
            RewriteSuggestion object
        """
        try:
            context_note = f" (This is a {context})" if context else ""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Please improve this text{context_note}:\n\n{text}"}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            rewrite_data = json.loads(response.choices[0].message.content)
            rewrites = rewrite_data.get("rewrites", [{}])
            
            if rewrites:
                return RewriteSuggestion(
                    original=text,
                    improved=rewrites[0].get("improved", text),
                    explanation=rewrites[0].get("explanation", "")
                )
            
            return RewriteSuggestion(original=text, improved=text, explanation="No changes needed")
            
        except Exception as e:
            return RewriteSuggestion(
                original=text,
                improved=text,
                explanation=f"Rewrite failed: {str(e)}"
            )
    
    def format_rewrites_display(self, suggestions: list[RewriteSuggestion]) -> str:
        """Format rewrite suggestions for display.
        
        Args:
            suggestions: List of RewriteSuggestion objects
            
        Returns:
            Formatted markdown string
        """
        if not suggestions:
            return "No bullet points found to improve. Try adding more content to your experience section."
        
        lines = ["## ✨ Improved Bullet Points\n"]
        
        for i, suggestion in enumerate(suggestions, 1):
            lines.extend([
                f"### {i}. Improvement",
                "",
                "**Original:**",
                f"> {suggestion.original}",
                "",
                "**Improved:**",
                f"> {suggestion.improved}",
                "",
                f"💡 *{suggestion.explanation}*",
                "",
                "---",
                ""
            ])
        
        return "\n".join(lines)
