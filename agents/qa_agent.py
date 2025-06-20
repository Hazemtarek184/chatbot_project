from rag.rag_pdf import RAGPDF
from handlers.web_search import PharaohExpert
from langdetect import detect
from typing import Tuple

class QAAgent:
    def __init__(self, pdf_path: str):
        """
        Initialize with:
        - RAGPDF for PDF processing
        - PharaohExpert for web search
        """
        self.rag = RAGPDF(pdf_path)
        self.web_searcher = PharaohExpert()
        
        # Initialize PDF processing
        self._initialize_pdf()

    def _initialize_pdf(self):
        """Load and process the PDF automatically"""
        try:
            text = self.rag.load_pdf()
            self.rag.split_text(text)
            self.rag.create_embeddings()
            print("[✓] PDF processing completed successfully")
        except Exception as e:
            print(f"[✗] PDF initialization failed: {e}")

    def detect_language(self, text: str) -> str:
        """Detect input language with fallback to English"""
        try:
            lang = detect(text)
            return lang if lang in ['ar', 'en'] else 'en'
        except:
            return 'en'

    def get_answer(self, question: str) -> Tuple[str, str, str]:
        """
        Get answer from both sources:
        Returns tuple: (pdf_answer, web_answer1, web_answer2)
        """
        lang = self.detect_language(question)
        
        # 1. Get PDF answer
        pdf_answer = self.rag.generate_answer(question)
        
        # 2. Get web answers (always returns 3 answers)
        web_answers = self.web_searcher.get_pharaoh_info(question)
        
        # Format responses based on language
        if lang == 'ar':
            pdf_answer = pdf_answer or "لا توجد إجابة في المستند"
            return (pdf_answer, *web_answers[:2])
        else:
            pdf_answer = pdf_answer or "No answer found in document"
            return (pdf_answer, *web_answers[:2])

    def interactive_test(self):
        """Interactive testing mode"""
        print("\n" + "="*50)
        print("QAAgent Testing Mode")
        print("="*50)
        
        while True:
            question = input("\nEnter your question (or 'exit' to quit): ").strip()
            if question.lower() in ['exit', 'quit']:
                break
                
            answers = self.get_answer(question)
            
            print("\n[PDF Answer]:")
            print(answers[0])
            
            print("\n[Web Answer 1]:")
            print(answers[1])
            
            print("\n[Web Answer 2]:")
            print(answers[2])
