from django.test import TestCase
from .resume_parser import parse_resume
from .skills_extractor import extract_skills
from .experience_extractor import extract_experience
from .project_extractor import extract_projects


class ParserTestCase(TestCase):

    def test_extract_skills_basic(self):
        """Test basic skill extraction"""
        text = "Python developer with experience in Django and machine learning"
        skills = extract_skills(text)
        self.assertIn("python", skills)
        self.assertIn("django", skills)
        self.assertIn("machine learning", skills)

    def test_extract_experience_years(self):
        """Test experience extraction with years"""
        text = "3.5 years of experience in software development"
        experience = extract_experience(text)
        self.assertEqual(experience, 3.5)

    def test_extract_experience_alternative(self):
        """Test experience extraction with alternative phrasing"""
        text = "Software developer with experience of 4 years"
        experience = extract_experience(text)
        self.assertEqual(experience, 4.0)

    def test_extract_projects(self):
        """Test project extraction"""
        text = "Worked on Django e-commerce website. Developed machine learning system."
        projects = extract_projects(text)
        self.assertTrue(len(projects) > 0)
        self.assertIn("django e-commerce website", projects)

    def test_parse_resume_text_file(self):
        """Test parsing plain text resume"""
        test_text = b"Python developer with 2 years experience working on Django projects and machine learning"
        result = parse_resume(test_text, 'text/plain')
        self.assertIn("skills", result)
        self.assertIn("experience", result)
        self.assertIn("projects", result)
        self.assertIsInstance(result["experience"], float)
        self.assertIn("python", result["skills"])
        self.assertIn("django", result["skills"])
