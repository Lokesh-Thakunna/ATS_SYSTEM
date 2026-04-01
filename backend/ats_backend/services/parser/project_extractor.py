import re
import spacy

def extract_projects(text):
    """
    Extract project names from resume text using improved patterns and NLP
    """
    text = text.lower()
    projects = set()

    # Improved regex patterns for different resume formats
    patterns = [
        r'project[s]?:?\s*([^.\n]+)',
        r'worked on\s+([^.\n]+)',
        r'developed\s+([^.\n]+)',
        r'built\s+([^.\n]+)',
        r'created\s+([^.\n]+)',
        r'implemented\s+([^.\n]+)',
        r'designed\s+([^.\n]+)',
        r'led\s+([^.\n]+)',
        r'managed\s+([^.\n]+)',
        r'contributed to\s+([^.\n]+)',
        r'accomplishments?:?\s*([^.\n]+)',
        r'achievements?:?\s*([^.\n]+)',
        r'portfolio.*?\s*([^.\n]+)',
        r'key projects?:?\s*([^.\n]+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            projects.add(match.strip())

    try:
        # Load spaCy model
        nlp = spacy.load("en_core_web_sm")
        
        # Use spaCy to find sentences with project keywords and extract noun phrases
        doc = nlp(text)
        project_keywords = ["project", "developed", "built", "created", "implemented", "designed", "worked", "led", "managed", "contributed"]

        for sent in doc.sents:
            sent_text = sent.text.lower()
            if any(keyword in sent_text for keyword in project_keywords):
                # Extract compound nouns and proper nouns that are likely project names
                for chunk in sent.noun_chunks:
                    chunk_text = chunk.text.lower()
                    if len(chunk_text) > 5 and not any(stop in chunk_text for stop in ["experience", "skills", "education", "work", "company", "team", "years", "month"]):
                        projects.add(chunk_text)
    except OSError:
        # Fallback if spaCy not available
        pass

    # Clean up the results
    cleaned_projects = []
    for project in projects:
        project = re.sub(r'[^\w\s]', '', project).strip()  # Remove punctuation
        if len(project) > 5 and len(project.split()) <= 5:  # Reasonable length
            cleaned_projects.append(project)

    return list(set(cleaned_projects))