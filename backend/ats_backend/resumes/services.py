"""
Resume parsing and skill extraction service
"""

import logging
import re
from typing import Dict, List, Optional


from datetime import datetime


import pdfplumber
import docx
from io import BytesIO


import spacy

from django.core.files.uploadedfile import InMemoryUploadedFile


logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None

class ResumeParser:
    """Production-ready resume parsing with skill extraction"""

    def __init__(self):
        self.skill_keywords = self._load_skill_keywords()
        self.experience_patterns = self._load_experience_patterns()
        self.education_patterns = self._load_education_patterns()

    def parse_resume(self, file: InMemoryUploadedFile) -> Dict:
        """
        Parse resume file and extract structured information

        Args:
            file: Uploaded resume file (PDF, DOCX)

        Returns:
            Dict containing parsed resume data
        """
        try:
            # Extract text content
            text_content = self._extract_text(file)

            # Parse structured information
            parsed_data = {
                'text_content': text_content,
                'personal_info': self._extract_personal_info(text_content),
                'contact_info': self._extract_contact_info(text_content),
                'skills': self._extract_skills(text_content),
                'experience': self._extract_experience(text_content),
                'education': self._extract_education(text_content),
                'certifications': self._extract_certifications(text_content),
                'projects': self._extract_projects(text_content),
                'languages': self._extract_languages(text_content),
                'summary': self._extract_summary(text_content),
                'parsing_metadata': {
                    'file_name': file.name,
                    'file_size': file.size,
                    'content_type': file.content_type,
                    'parsed_at': datetime.now().isoformat(),
                    'parsing_version': '1.0'
                }
            }

            # Calculate quality metrics
            parsed_data['quality_metrics'] = self._calculate_quality_metrics(parsed_data)

            return parsed_data

        except Exception as e:
            logger.error(f"Resume parsing failed: {str(e)}")
            return self._get_error_response(str(e))

    def _extract_text(self, file: InMemoryUploadedFile) -> str:
        """Extract text from PDF or DOCX file"""
        try:
            if file.content_type == 'application/pdf':
                return self._extract_pdf_text(file)
            elif file.content_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                     'application/msword']:
                return self._extract_docx_text(file)
            else:
                raise ValueError(f"Unsupported file type: {file.content_type}")
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise

    def _extract_pdf_text(self, file: InMemoryUploadedFile) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with pdfplumber.open(BytesIO(file.read())) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"PDF text extraction failed: {str(e)}")
            raise
        return text

    def _extract_docx_text(self, file: InMemoryUploadedFile) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(BytesIO(file.read()))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            logger.error(f"DOCX text extraction failed: {str(e)}")
            raise
        return text

    def _extract_personal_info(self, text: str) -> Dict:
        """Extract personal information from resume text"""
        personal_info = {
            'name': self._extract_name(text),
            'headline': self._extract_headline(text),
            'location': self._extract_location(text),
            'portfolio_links': self._extract_portfolio_links(text)
        }
        return personal_info

    def _extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name from resume"""
        lines = text.split('\n')

        # Look for name in first few lines (usually at top)
        for line in lines[:5]:
            line = line.strip()
            if len(line.split()) >= 2 and len(line.split()) <= 4:
                # Check if it looks like a name (capitalized words)
                words = line.split()
                if all(word[0].isupper() for word in words if word.isalpha()):
                    return line

        return None

    def _extract_headline(self, text: str) -> Optional[str]:
        """Extract professional headline"""
        lines = text.split('\n')

        # Look for headline after name (usually in first 10 lines)
        for i, line in enumerate(lines[1:10]):
            line = line.strip()
            # Common headline patterns
            if any(keyword in line.lower() for keyword in [
                'engineer', 'developer', 'manager', 'analyst', 'designer',
                'specialist', 'consultant', 'director', 'coordinator'
            ]):
                return line

        return None

    def _extract_contact_info(self, text: str) -> Dict:
        """Extract contact information"""
        contact_info = {
            'email': self._extract_email(text),
            'phone': self._extract_phone(text),
            'linkedin': self._extract_linkedin(text),
            'github': self._extract_github(text),
            'website': self._extract_website(text)
        }
        return contact_info

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group() if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
        phone_patterns = [
            r'\+?1?-?\.?\s?\(?(\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
            r'\+?(\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # International
        ]

        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        return None

    def _extract_linkedin(self, text: str) -> Optional[str]:
        """Extract LinkedIn profile"""
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        match = re.search(linkedin_pattern, text, re.IGNORECASE)
        return f"https://www.{match.group()}" if match else None

    def _extract_github(self, text: str) -> Optional[str]:
        """Extract GitHub profile"""
        github_pattern = r'github\.com/[\w-]+'
        match = re.search(github_pattern, text, re.IGNORECASE)
        return f"https://www.{match.group()}" if match else None

    def _extract_website(self, text: str) -> Optional[str]:
        """Extract personal website"""
        website_pattern = r'https?://[^\s]+\.(com|org|net|io|dev|me)[^\s]*'
        matches = re.findall(website_pattern, text, re.IGNORECASE)

        # Return first non-linkedin/github website
        for match in matches:
            if not any(domain in match.lower() for domain in ['linkedin', 'github']):
                return match
        return None

    def _extract_portfolio_links(self, text: str) -> List[str]:
        """Extract portfolio and project links"""
        portfolio_patterns = [
            r'portfolio:\s*(https?://[^\s]+)',
            r'projects:\s*(https?://[^\s]+)',
            r'behance\.net/[^\s]+',
            r'dribbble\.com/[^\s]+',
            r'codepen\.io/[^\s]+'
        ]

        links = []
        for pattern in portfolio_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            links.extend(matches)

        return list(set(links))

    def _extract_skills(self, text: str) -> Dict:
        """Extract skills with categorization"""
        skills = {
            'technical_skills': [],
            'soft_skills': [],
            'tools': [],
            'languages': [],
            'certifications': [],
            'all_skills': []
        }

        # Technical skills extraction
        technical_skills = self._extract_technical_skills(text)
        skills['technical_skills'] = technical_skills

        # Soft skills extraction
        soft_skills = self._extract_soft_skills(text)
        skills['soft_skills'] = soft_skills

        # Tools extraction
        tools = self._extract_tools(text)
        skills['tools'] = tools

        # Languages extraction
        languages = self._extract_languages(text)
        skills['languages'] = languages

        # Certifications extraction
        certifications = self._extract_certifications(text)
        skills['certifications'] = certifications

        # Combine all skills
        skills['all_skills'] = list(set(
            technical_skills + soft_skills + tools + languages + certifications
        ))

        return skills

    def _extract_technical_skills(self, text: str) -> List[str]:
        """Extract technical skills using keyword matching"""
        technical_skills = []

        # Programming languages
        programming_langs = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby',
            'php', 'swift', 'kotlin', 'go', 'rust', 'scala', 'perl'
        ]

        # Frameworks and libraries
        frameworks = [
            'react', 'vue', 'angular', 'django', 'flask', 'spring', 'express',
            'node', 'dotnet', 'laravel', 'rails', 'bootstrap', 'tailwind'
        ]

        # Databases
        databases = [
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle',
            'sql server', 'sqlite', 'cassandra', 'dynamodb'
        ]

        # Cloud platforms
        cloud_platforms = [
            'aws', 'azure', 'google cloud', 'gcp', 'heroku', 'digitalocean',
            'vercel', 'netlify', 'firebase'
        ]

        # DevOps tools
        devops_tools = [
            'docker', 'kubernetes', 'jenkins', 'gitlab', 'github', 'bitbucket',
            'terraform', 'ansible', 'puppet', 'chef', 'circleci', 'travis'
        ]

        all_keywords = programming_langs + frameworks + databases + cloud_platforms + devops_tools

        # Extract skills using pattern matching
        text_lower = text.lower()
        for keyword in all_keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                technical_skills.append(keyword)

        return list(set(technical_skills))

    def _extract_soft_skills(self, text: str) -> List[str]:
        """Extract soft skills"""
        soft_skills_keywords = [
            'leadership', 'communication', 'teamwork', 'problem solving',
            'critical thinking', 'creativity', 'adaptability', 'time management',
            'project management', 'analytical thinking', 'collaboration',
            'presentation skills', 'negotiation', 'mentoring', 'decision making'
        ]

        soft_skills = []
        text_lower = text.lower()

        for skill in soft_skills_keywords:
            if skill in text_lower:
                soft_skills.append(skill)

        return list(set(soft_skills))

    def _extract_tools(self, text: str) -> List[str]:
        """Extract software tools"""
        tools_keywords = [
            'jira', 'slack', 'microsoft office', 'google workspace', 'figma',
            'sketch', 'adobe creative suite', 'visual studio code', 'intellij',
            'postman', 'swagger', 'git', 'svn', 'mercurial'
        ]

        tools = []
        text_lower = text.lower()

        for tool in tools_keywords:
            if tool in text_lower:
                tools.append(tool)

        return list(set(tools))

    def _extract_languages(self, text: str) -> List[str]:
        """Extract spoken languages"""
        language_keywords = [
            'english', 'spanish', 'french', 'german', 'chinese', 'japanese',
            'korean', 'portuguese', 'russian', 'arabic', 'hindi', 'italian'
        ]

        languages = []
        text_lower = text.lower()

        for lang in language_keywords:
            if lang in text_lower:
                languages.append(lang)

        return list(set(languages))

    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience"""
        experience = []

        if not nlp:
            return experience

        # Use spaCy for named entity recognition if needed for future enhancements
        if nlp:
            nlp(text)  # Process text for potential future NLP features

        # Look for experience patterns
        lines = text.split('\n')
        current_exp = None

        for line in lines:
            line = line.strip()

            # Check for company/organization patterns
            if self._is_company_line(line):
                if current_exp:
                    experience.append(current_exp)
                current_exp = {'company': line, 'positions': []}

            # Check for position/title patterns
            elif current_exp and self._is_position_line(line):
                position = self._parse_position_line(line)
                if position:
                    current_exp['positions'].append(position)

            # Check for date patterns
            elif current_exp and self._is_date_line(line):
                dates = self._parse_dates(line)
                if dates and current_exp['positions']:
                    current_exp['positions'][-1].update(dates)

        # Add last experience
        if current_exp:
            experience.append(current_exp)

        return self._enhance_experience_data(experience)

    def _is_company_line(self, line: str) -> bool:
        """Check if line contains company information"""
        company_indicators = ['Inc', 'LLC', 'Corp', 'Company', 'Technologies', 'Solutions']
        return any(indicator in line for indicator in company_indicators)

    def _is_position_line(self, line: str) -> bool:
        """Check if line contains position/title"""
        position_keywords = [
            'engineer', 'developer', 'manager', 'analyst', 'designer',
            'specialist', 'consultant', 'director', 'coordinator'
        ]
        return any(keyword in line.lower() for keyword in position_keywords)

    def _parse_position_line(self, line: str) -> Optional[Dict]:
        """Parse position information from line"""
        return {
            'title': line.strip(),
            'description': '',
            'start_date': None,
            'end_date': None,
            'current': False
        }

    def _is_date_line(self, line: str) -> bool:
        """Check if line contains date information"""
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}',  # Month YYYY
        ]

        return any(re.search(pattern, line) for pattern in date_patterns)

    def _parse_dates(self, line: str) -> Dict:
        """Parse date information from line"""
        # This is a simplified implementation
        # In production, you'd want more sophisticated date parsing
        return {
            'start_date': None,
            'end_date': None,
            'duration': None
        }

    def _enhance_experience_data(self, experience: List[Dict]) -> List[Dict]:
        """Enhance experience data with calculated metrics"""
        enhanced_experience = []

        for exp in experience:
            enhanced_exp = exp.copy()

            # Calculate total experience duration
            total_months = 0
            for position in exp.get('positions', []):
                # Simplified duration calculation
                duration = self._calculate_position_duration(position)
                total_months += duration

            enhanced_exp['total_duration_months'] = total_months
            enhanced_exp['total_duration_years'] = round(total_months / 12, 1)

            enhanced_experience.append(enhanced_exp)

        return enhanced_experience

    def _calculate_position_duration(self, position: Dict) -> int:
        """Calculate position duration in months"""
        # Simplified implementation
        # In production, you'd parse actual dates and calculate duration
        return 12  # Placeholder

    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education information"""
        education = []

        # Education degree patterns
        degree_patterns = [
            r'(Bachelor|Master|PhD|Associate|B\.S\.|M\.S\.|B\.A\.|M\.A\.)[^\n]*',
            r'(High School|GED|Diploma|Certificate)[^\n]*'
        ]

        for pattern in degree_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                education_info = self._parse_education_entry(match)
                if education_info:
                    education.append(education_info)

        return education

    def _parse_education_entry(self, entry: str) -> Optional[Dict]:
        """Parse individual education entry"""
        return {
            'degree': entry.strip(),
            'institution': None,
            'field_of_study': None,
            'graduation_year': None,
            'gpa': None
        }

    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        certification_patterns = [
            r'(Certified|Certificate|Certification)[^\n]*',
            r'(AWS|Azure|Google|PMP|Scrum|Agile)[^\n]*(Certified|Certificate|Certification)?'
        ]

        certifications = []
        for pattern in certification_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            certifications.extend(matches)

        return list(set(certifications))

    def _extract_projects(self, text: str) -> List[Dict]:
        """Extract project information"""
        projects = []

        # Look for project sections
        project_section_pattern = r'(?:Projects|Project Work|Personal Projects)[\s\S]*?(?=\n\n|\Z)'
        project_matches = re.findall(project_section_pattern, text, re.IGNORECASE | re.DOTALL)

        for match in project_matches:
            project_info = self._parse_project_section(match)
            if project_info:
                projects.append(project_info)

        return projects

    def _parse_project_section(self, section: str) -> Optional[Dict]:
        """Parse project section"""
        return {
            'name': '',
            'description': section.strip(),
            'technologies': self._extract_technical_skills(section),
            'duration': None,
            'url': None
        }

    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract professional summary/objective"""
        lines = text.split('\n')
        summary_lines = []

        # Look for summary in first few lines
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 50:  # Likely a summary line
                summary_lines.append(line)
            elif summary_lines:
                break  # Stop when we hit a short line after summary

        return ' '.join(summary_lines) if summary_lines else None

    def _calculate_quality_metrics(self, parsed_data: Dict) -> Dict:
        """Calculate resume quality metrics"""
        metrics = {
            'completeness_score': 0,
            'skill_count': len(parsed_data.get('skills', {}).get('all_skills', [])),
            'experience_count': len(parsed_data.get('experience', [])),
            'education_count': len(parsed_data.get('education', [])),
            'has_contact_info': bool(
                parsed_data.get('contact_info', {}).get('email') or
                parsed_data.get('contact_info', {}).get('phone')
            ),
            'text_length': len(parsed_data.get('text_content', '')),
            'parsing_confidence': 0.0
        }

        # Calculate completeness score
        completeness_factors = [
            metrics['has_contact_info'],
            metrics['skill_count'] > 0,
            metrics['experience_count'] > 0,
            metrics['education_count'] > 0,
            len(parsed_data.get('text_content', '')) > 500
        ]

        metrics['completeness_score'] = sum(completeness_factors) / len(completeness_factors) * 100

        # Calculate parsing confidence based on text structure
        confidence_score = 0.5  # Base confidence

        if metrics['has_contact_info']:
            confidence_score += 0.2
        if metrics['skill_count'] >= 5:
            confidence_score += 0.15
        if metrics['experience_count'] > 0:
            confidence_score += 0.1
        if metrics['education_count'] > 0:
            confidence_score += 0.05

        metrics['parsing_confidence'] = min(confidence_score, 1.0)

        return metrics

    def _load_skill_keywords(self) -> Dict:
        """Load skill keywords for matching"""
        # This would typically be loaded from a database or config file
        return {
            'programming': ['python', 'java', 'javascript', 'typescript', 'c++'],
            'frameworks': ['react', 'vue', 'angular', 'django', 'flask'],
            'databases': ['mysql', 'postgresql', 'mongodb', 'redis'],
            'cloud': ['aws', 'azure', 'google cloud', 'gcp'],
            'tools': ['docker', 'kubernetes', 'git', 'jenkins']
        }

    def _load_experience_patterns(self) -> List[str]:
        """Load experience extraction patterns"""
        return [
            r'(\d{1,2})\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
            r'(?:experience|exp)[:\s]*(\d{1,2})\s*(?:years?|yrs?)',
        ]

    def _load_education_patterns(self) -> List[str]:
        """Load education extraction patterns"""
        return [
            r'(Bachelor|Master|PhD|Associate|B\.S\.|M\.S\.|B\.A\.|M\.A\.)',
            r'(High School|GED|Diploma|Certificate)',
        ]

    def _get_error_response(self, error_message: str) -> Dict:
        """Return standardized error response"""
        return {
            'success': False,
            'error': error_message,
            'parsed_data': None,
            'quality_metrics': {
                'completeness_score': 0,
                'parsing_confidence': 0.0
            }
        }

# Global instance
resume_parser = ResumeParser()
