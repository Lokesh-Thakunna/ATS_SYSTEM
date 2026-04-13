import re

def extract_experience(text):
    """
    Extract years of experience from resume text with enhanced patterns
    """
    text_lower = text.lower()

    # Primary patterns for different resume formats
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:\+?\s*)?(?:years?|yrs?|year)\s*(?:of\s*)?experience',
        r'experience\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*(?:\+?\s*)?(?:years?|yrs?|year)',
        r'(\d+(?:\.\d+)?)\s*(?:\+?\s*)?(?:years?|yrs?|year)\s*(?:of\s*)?experience',
        r'total experience\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*(?:\+?\s*)?(?:years?|yrs?|year)',
        r'professional experience\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*(?:\+?\s*)?(?:years?|yrs?|year)',
        r'work experience\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*(?:\+?\s*)?(?:years?|yrs?|year)',
        r'(\d+(?:\.\d+)?)\s*(?:\+?\s*)?years?\s*(?:of\s*)?professional experience',
        r'over\s*(\d+(?:\.\d+)?)\s*(?:\+?\s*)?(?:years?|yrs?|year)',
        r'more than\s*(\d+(?:\.\d+)?)\s*(?:\+?\s*)?(?:years?|yrs?|year)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                years = float(match.group(1))
                # Validate reasonable range
                if 0 <= years <= 50:
                    return years
            except ValueError:
                continue

    # If no direct experience mention, try to estimate from work history
    # Look for date ranges and calculate approximate experience
    date_patterns = [
        r'(\d{4})\s*-\s*(\d{4})',  # 2015-2020
        r'(\d{4})\s*-\s*present',   # 2015-present
        r'(\d{4})\s*-\s*current',   # 2015-current
    ]

    total_years = 0
    for pattern in date_patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if isinstance(match, tuple):
                start_year = int(match[0])
                end_year = 2026 if match[1].lower() in ['present', 'current'] else int(match[1])
                if end_year > start_year:
                    total_years += (end_year - start_year)

    if total_years > 0 and total_years <= 50:
        return float(total_years)

    return 0.0
