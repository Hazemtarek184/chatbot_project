import os
import requests
from dotenv import load_dotenv
import re
import random
from typing import List, Tuple

load_dotenv()

class PharaohExpert:
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("Add SERPER_API_KEY to .env file")
        
        self.trusted_sites = [
            "en.wikipedia.org",
            "britishmuseum.org",
            "metmuseum.org",
            "worldhistory.org",
            "escholarship.org",
            "egymonuments.gov.eg",
            "griffith.ox.ac.uk",
            "louvre.fr",
            "digitalegypt.ucl.ac.uk",
            "nationalgeographic.com"
        ]

        self.search_url = "https://google.serper.dev/search"
        
        self.aspects = {
            "reign": "{name} reign period dynasty",
            "achievements": "{name} major accomplishments",
            "architecture": "{name} building projects architecture",
            "family": "{name} family lineage",
            "tomb": "{name} tomb discovery",
            "politics": "{name} political achievements",
            "religion": "{name} religious reforms",
            "military": "{name} military campaigns",
            "legacy": "{name} legacy historical impact" 
        }

    def get_pharaoh_info(self, name: str) -> Tuple[str, str, str]:
        """Returns 3 distinct detailed answers about the pharaoh"""
        answers = []
        
        # تعريف الجوانب لكل إجابة
        focus_sets = [
            ["reign", "achievements", "architecture"],
            ["family", "tomb", "religion"],
            ["politics", "military", "legacy"]
        ]
        
        for focus in focus_sets:
            answer = self._generate_answer(name, focus)
            answers.append(answer)
            
            # إذا لم نحصل على إجابة كافية، نجرب جوانب أخرى
            if len(answer.split('.')) < 5:
                backup_focus = random.sample(list(self.aspects.keys()), 3)
                answer = self._generate_answer(name, backup_focus)
                answers[-1] = answer  # استبدال الإجابة الضعيفة
            
        return tuple(answers[:3])

    def _generate_answer(self, name: str, focus_aspects: List[str]) -> str:
        """Generate one detailed answer focusing on specific aspects"""
        paragraphs = []
        
        # Introduction to the Pharaoh
        intro = self._get_pharaoh_intro(name)
        paragraphs.append(intro)
        
        # Information on required aspects
        for aspect in focus_aspects:
            if aspect in self.aspects:  # Confirm the key exists
                query = self.aspects[aspect].format(name=name)
                info = self._get_detailed_info(query)
                if info:
                    paragraphs.append(info)
        
        # If answer is short, we add more information
        while len(paragraphs) < 4:
            remaining_aspects = [a for a in self.aspects if a not in focus_aspects]
            if remaining_aspects:
                extra_aspect = random.choice(remaining_aspects)
                query = self.aspects[extra_aspect].format(name=name)
                info = self._get_detailed_info(query)
                if info:
                    paragraphs.append(info)
            else:
                break
        
        # Group paragraphs into one answer
        answer = ' '.join(paragraphs)
        return self._ensure_proper_length(answer)

    def _get_pharaoh_intro(self, name: str) -> str:
        """Get a proper introduction for the pharaoh"""
        query = f"{name} ancient Egypt pharaoh introduction"
        result = self._get_best_result(query)
        if result:
            return self._format_intro(name, result)
        return f"{name}, a prominent pharaoh of ancient Egypt."

    def _get_detailed_info(self, query: str) -> str:
        """Get detailed information about a specific aspect"""
        result = self._get_best_result(query)
        if result:
            return self._format_aspect(result)
        return ""

    def _get_best_result(self, query: str) -> str:
        """Get the best search result for a query"""
        try:
            response = requests.post(
                self.search_url,
                headers={"X-API-KEY": self.api_key},
                json={
                    "q": f"{query} site:{' OR site:'.join(self.trusted_sites)}",
                    "num": 5
                },
                timeout=15
            )
            response.raise_for_status()
            
            for result in response.json().get("organic", []):
                if self._is_trusted(result.get("link", "")):
                    snippet = result.get("snippet", "")
                    if snippet and len(snippet.split()) > 15:
                        return snippet
                        
        except Exception as e:
            print(f"Error in search: {e}")
        
        return ""

    def _ensure_proper_length(self, text: str) -> str:
        """Ensure the answer is 7-12 sentences long"""
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
        
        if len(sentences) < 7:
            # Add extra sentences if answer is short
            extra_query = random.choice(list(self.aspects.values())).format(name="Hatshepsut")
            extra_info = self._get_detailed_info(extra_query)
            if extra_info:
                extra_sentences = [s.strip() for s in re.split(r'[.!?]', extra_info) if s.strip()]
                sentences.extend(extra_sentences[:3])
        
        sentences = sentences[:12]  #Limit to 12 sentences maximum
        
        # Formatting sentences
        sentences = [s[0].upper() + s[1:] if s else s for s in sentences]
        answer = '. '.join(sentences) + '.' if sentences else ""
        
        return answer

    def _format_intro(self, name: str, text: str) -> str:
        """Format the introduction paragraph"""
        text = self._clean_content(text)
        if not text.startswith(name):
            text = f"{name}, {text[0].lower()}{text[1:]}"
        return self._capitalize_first(text)

    def _format_aspect(self, text: str) -> str:
        """Format an aspect paragraph"""
        text = self._clean_content(text)
        return self._capitalize_first(text)

    def _capitalize_first(self, text: str) -> str:
        """Capitalize first letter and ensure proper punctuation"""
        text = text.strip()
        if not text:
            return text
        if not text[-1] in '.!?':
            text += '.'
        return text[0].upper() + text[1:]

    def _clean_content(self, text: str) -> str:
        """Clean the content from unwanted characters"""
        text = re.sub(r'\[.*?\]|\(.*?\)|\b\d{4}\b|\.\.\.', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _is_trusted(self, url: str) -> bool:
        """Check if URL is from a trusted site"""
        url = url.lower()
        return any(source in url for source in self.trusted_sites)
