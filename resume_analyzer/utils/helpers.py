"""Utility functions for text processing and helpers."""

import re


def clean_text(text: str) -> str:
    """Clean extracted text from PDF/DOCX.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text with normalized whitespace
    """
    if not text:
        return ""
    
    # Replace multiple newlines with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Remove leading/trailing whitespace from entire text
    text = text.strip()
    
    return text


def extract_bullet_points(text: str, max_bullets: int = 10) -> list[str]:
    """Extract bullet points from resume text.
    
    Args:
        text: Resume text content
        max_bullets: Maximum number of bullets to extract
        
    Returns:
        List of bullet point strings
    """
    bullets = []
    
    # Common bullet point patterns - expanded for better detection
    patterns = [
        r'^[\•\-\*\→\►\●\○\◦\▪\▸]\s*(.+)$',  # Actual bullet characters
        r'^\d+\.\s*(.+)$',              # Numbered lists
        r'^[a-z]\)\s*(.+)$',            # Lettered lists
    ]
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        for pattern in patterns:
            match = re.match(pattern, line, re.MULTILINE)
            if match:
                bullet_text = match.group(1).strip()
                if len(bullet_text) > 20:  # Filter out very short bullets
                    bullets.append(bullet_text)
                break
        
        if len(bullets) >= max_bullets:
            break
    
    # If no bullets found with patterns, look for lines that look like achievements
    if not bullets:
        for line in text.split('\n'):
            line = line.strip()
            # Lines starting with action verbs are likely bullet points
            action_verbs = ['led', 'managed', 'developed', 'created', 'implemented',
                          'increased', 'decreased', 'improved', 'designed', 'built',
                          'achieved', 'delivered', 'launched', 'established', 'generated',
                          'reduced', 'streamlined', 'coordinated', 'executed', 'analyzed',
                          'spearheaded', 'orchestrated', 'optimized', 'collaborated',
                          'drove', 'facilitated', 'mentored', 'supervised', 'oversaw',
                          'authored', 'crafted', 'engineered', 'architected', 'pioneered',
                          'transformed', 'revamped', 'modernized', 'automated', 'integrated',
                          'negotiated', 'secured', 'acquired', 'retained', 'resolved',
                          'responsible', 'worked', 'assisted', 'helped', 'supported']
            
            first_word = line.split()[0].lower().rstrip('ed') if line.split() else ''
            first_word_full = line.split()[0].lower() if line.split() else ''
            if (first_word_full in action_verbs or first_word in action_verbs) and len(line) > 25:
                bullets.append(line)
            
            if len(bullets) >= max_bullets:
                break
    
    return bullets


def truncate_text(text: str, max_chars: int = 15000) -> str:
    """Truncate text to fit within token limits.
    
    Args:
        text: Text to truncate
        max_chars: Maximum characters (rough proxy for tokens)
        
    Returns:
        Truncated text with indicator if truncated
    """
    if len(text) <= max_chars:
        return text
    
    truncated = text[:max_chars]
    # Try to end at a sentence or paragraph
    last_period = truncated.rfind('.')
    last_newline = truncated.rfind('\n')
    
    cut_point = max(last_period, last_newline)
    if cut_point > max_chars * 0.8:  # Only use if we're not losing too much
        truncated = truncated[:cut_point + 1]
    
    return truncated + "\n\n[Content truncated for length...]"


def format_score_bar(score: int, max_score: int = 10, bar_length: int = 20) -> str:
    """Create a visual score bar.
    
    Args:
        score: Current score
        max_score: Maximum possible score
        bar_length: Length of the bar in characters
        
    Returns:
        Visual bar string like [████████░░] 8/10
    """
    filled = int((score / max_score) * bar_length)
    empty = bar_length - filled
    bar = '█' * filled + '░' * empty
    return f"[{bar}] {score}/{max_score}"


def get_score_color(score: int) -> str:
    """Get a color indicator for a score.
    
    Args:
        score: Score from 1-10
        
    Returns:
        Color emoji indicator
    """
    if score >= 8:
        return "🟢"  # Green
    elif score >= 6:
        return "🟡"  # Yellow
    elif score >= 4:
        return "🟠"  # Orange
    else:
        return "🔴"  # Red


def estimate_tokens(text: str) -> int:
    """Rough estimate of token count.
    
    Args:
        text: Text to estimate
        
    Returns:
        Estimated token count (roughly 4 chars per token)
    """
    return len(text) // 4
