from fuzzywuzzy import fuzz
import spacy
from spacy.matcher import PhraseMatcher
import re

SKILLS = [
    "python", "java", "c", "c++", "c#", "javascript", "typescript", "ruby", "php", "go", "rust", "kotlin", "swift", "scala", "perl",
    "django", "flask", "fastapi", "spring", "hibernate", "react", "angular", "vue", "node.js", "express", "jquery", "bootstrap", "tailwind", "sass", "less",
    "machine learning", "deep learning", "artificial intelligence", "ai", "data science", "big data", "nlp", "computer vision", "reinforcement learning",
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "oracle", "sqlite", "cassandra", "neo4j",
    "html", "css", "xml", "json", "rest", "graphql", "soap", "api development",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible", "jenkins", "ci/cd", "git", "svn", "mercurial",
    "linux", "bash", "powershell", "windows", "macos",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "opencv", "matplotlib", "seaborn", "keras", "xgboost", "lightgbm",
    "apache spark", "hadoop", "kafka", "rabbitmq", "nginx", "apache",
    "agile", "scrum", "kanban", "jira", "confluence", "slack", "trello",
    "testing", "unit testing", "integration testing", "selenium", "pytest", "junit", "mocha", "jest",
    "security", "encryption", "oauth", "jwt", "ssl", "penetration testing",
    "blockchain", "ethereum", "solidity", "web3",
    "iot", "embedded systems", "arduino", "raspberry pi",
    "mobile development", "android", "ios", "flutter", "react native", "xamarin"
]

def extract_skills(text):
    """
    Extract skills from text with better accuracy using spaCy matcher and fuzzy matching
    """
    text = text.lower()
    found = set()

    try:
        # Load spaCy model
        nlp = spacy.load("en_core_web_sm")
        
        # Create phrase matcher
        matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        patterns = [nlp.make_doc(skill) for skill in SKILLS]
        matcher.add("SKILLS", patterns)

        doc = nlp(text)
        matches = matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            found.add(span.text.lower())
    except OSError:
        # Fallback to simple matching if spaCy model not available
        pass

    # Enhanced exact matching with better patterns
    for skill in SKILLS:
        # Check for whole word matches
        if f" {skill} " in f" {text} " or text.startswith(f"{skill} ") or text.endswith(f" {skill}"):
            found.add(skill)

        # Check for skill sections and contextual mentions
        skill_patterns = [
            rf'skills?:.*?\b{re.escape(skill)}\b',
            rf'technical skills?:.*?\b{re.escape(skill)}\b',
            rf'competencies?:.*?\b{re.escape(skill)}\b',
            rf'expertise.*?\b{re.escape(skill)}\b',
            rf'proficient in.*?\b{re.escape(skill)}\b',
            rf'experience with.*?\b{re.escape(skill)}\b',
            rf'knowledge of.*?\b{re.escape(skill)}\b',
            rf'familiar with.*?\b{re.escape(skill)}\b'
        ]
        for pattern in skill_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found.add(skill)

    # Additional fuzzy matching for skills not caught
    words = text.split()
    for i in range(len(words)):
        for j in range(i+1, min(i+5, len(words)+1)):  # phrases up to 4 words
            phrase = " ".join(words[i:j])
            for skill in SKILLS:
                if skill not in found and fuzz.ratio(skill, phrase) > 80:  # Lower threshold
                    found.add(skill)

    return list(found)