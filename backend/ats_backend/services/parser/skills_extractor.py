import re

from fuzzywuzzy import fuzz

from .nlp import get_nlp, get_skill_phrase_matcher

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
    text = (text or "").lower()
    found = set()

    nlp = get_nlp()
    matcher = get_skill_phrase_matcher()
    if nlp is not None and matcher is not None:
        doc = nlp(text)
        matches = matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            found.add(span.text.lower())

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
    if not found:
        words = text.split()
        max_windows = min(len(words), 250)
        for i in range(max_windows):
            for j in range(i + 1, min(i + 5, max_windows + 1)):
                phrase = " ".join(words[i:j])
                for skill in SKILLS:
                    if skill not in found and fuzz.ratio(skill, phrase) > 80:
                        found.add(skill)

    return sorted(found)
