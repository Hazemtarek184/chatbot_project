# rag/rag_pdf.py
import os
import faiss
import PyPDF2
import numpy as np
from typing import List
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain_sambanova import ChatSambaNovaCloud

class RAGPDF:
    def __init__(self, pdf_path: str):
        """تهيئة الكلاس مع مسار ملف PDF ونموذج اللغة"""
        self.pdf_path = pdf_path
        self.chunks = []  # لتخزين أجزاء النص
        self.embeddings = []  # لتخزين التمثيل العددي للنصوص
        self.index = None  # فهرس FAISS للبحث
        self.model = SentenceTransformer("all-MiniLM-L6-v2")  # نموذج تحويل النصوص إلى أرقام
        
        # تحميل متغيرات البيئة وتهيئة نموذج سامبانوفا
        load_dotenv()
        self.llm = ChatSambaNovaCloud(
            model="Meta-Llama-3.3-70B-Instruct",
            max_tokens=1024,
            temperature=0.7,
            top_p=0.01,
            api_key=os.getenv("SAMBANOVA_API_KEY"),
        )

    def load_pdf(self) -> str:
        """تحميل محتوى ملف PDF وإرجاعه كنص"""
        with open(self.pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    def split_text(self, text: str, max_chunk_size: int = 300):
        """تقسيم النص إلى أجزاء صغيرة لمعالجتها"""
        words = text.split()
        chunk = []
        for word in words:
            chunk.append(word)
            if len(chunk) >= max_chunk_size:
                self.chunks.append(' '.join(chunk))
                chunk = []
        if chunk:
            self.chunks.append(' '.join(chunk))

    def create_embeddings(self):
        """إنشاء تمثيل عددي للنصوص وحفظها في فهرس FAISS"""
        self.embeddings = self.model.encode(self.chunks, convert_to_numpy=True)
        dimension = self.embeddings.shape[1]  
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.embeddings)

    def search(self, query: str, top_k: int = 3) -> List[str]:
        """البحث عن الأجزاء الأكثر صلة بالسؤال"""
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_embedding, top_k)
        return [self.chunks[i] for i in indices[0]]

    def generate_answer(self, query: str) -> str:
        """إنشاء إجابة باستخدام الأجزاء الأكثر صلة"""
        relevant_chunks = self.search(query)
        context = "\n".join(relevant_chunks)
        prompt = f"""Answer the following question using the context below:
        
        Context:
        {context}
        
        Question: {query}
        
        Answer:"""
        
        response = self.llm.invoke(prompt)  # استخدام invoke بدلاً من generate
        
        # معالجة الاستجابة للحصول على النص
        if hasattr(response, 'content'):
            return response.content
        elif hasattr(response, 'generations'):
            return response.generations[0][0].text
        else:
            return str(response)

if __name__ == "__main__":
    print("=== Running RAGPDF test ===")
    
    # المسار إلى ملف PDF (تغييره لملفك الخاص)
    pdf_path = "../data/ancient_egypt_data.pdf"
    
    rag = RAGPDF(pdf_path)
    
    try:
        # 1. تحميل PDF
        text = rag.load_pdf()
        print(f"[✓] Loaded PDF with {len(text)} characters.")

        # 2. تقسيم النص
        rag.split_text(text)
        print(f"[✓] Split text into {len(rag.chunks)} chunks.")

        # 3. إنشاء تمثيل عددي
        rag.create_embeddings()
        print(f"[✓] Created FAISS index with {len(rag.embeddings)} embeddings.")

        # 4. طرح سؤال والحصول على إجابة
        question = "Tell me about Ramesses III"
        answer = rag.generate_answer(question)
        print(f"[✓] Answer:\n{answer}")

    except Exception as e:
        print(f"[✗] Error occurred: {e}")