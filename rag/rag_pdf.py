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
        """Initialize the class with the PDF file path and the language model."""
        self.pdf_path = pdf_path
        self.chunks = []        # To store text chunks
        self.embeddings = []    # To store numerical representations of text
        self.index = None       # FAISS index for similarity search
        self.model = SentenceTransformer("all-MiniLM-L6-v2")  # Text embedding model

        # Load environment variables and initialize the SambaNova model
        load_dotenv()
        self.llm = ChatSambaNovaCloud(
            model="Meta-Llama-3.3-70B-Instruct",
            max_tokens=1024,
            temperature=0.7,
            top_p=0.01,
            api_key="cc62771b-14e7-4f8e-a2b5-357297a2326e",
        )

    def load_pdf(self) -> str:
        """Load the content of the PDF file and return it as a string."""
        with open(self.pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    def split_text(self, text: str, max_chunk_size: int = 300):
        """Split the text into smaller chunks for easier processing."""
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
        """Generate vector embeddings for the text chunks and build the FAISS index."""
        self.embeddings = self.model.encode(self.chunks, convert_to_numpy=True)
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.embeddings)

    def search(self, query: str, top_k: int = 3) -> List[str]:
        """Search for the most relevant chunks based on the query."""
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_embedding, top_k)
        return [self.chunks[i] for i in indices[0]]

    def generate_answer(self, query: str) -> str:
        """Generate an answer using the most relevant chunks as context."""
        relevant_chunks = self.search(query)
        context = "\n".join(relevant_chunks)
        prompt = f"""Answer the following question using the context below:
        
        Context:
        {context}
        
        Question: {query}
        
        Answer:"""

        response = self.llm.invoke(prompt)  # Use invoke instead of generate

        # Process the response and extract the text
        if hasattr(response, 'content'):
            return response.content
        elif hasattr(response, 'generations'):
            return response.generations[0][0].text
        else:
            return str(response)

if __name__ == "__main__":
    print("=== Running RAGPDF test ===")

    # Path to the PDF file (replace with your own file)
    pdf_path = "../data/ancient_egypt_data.pdf"

    rag = RAGPDF(pdf_path)

    try:
        # 1. Load the PDF
        text = rag.load_pdf()
        print(f"[✓] Loaded PDF with {len(text)} characters.")

        # 2. Split the text into chunks
        rag.split_text(text)
        print(f"[✓] Split text into {len(rag.chunks)} chunks.")

        # 3. Create vector embeddings
        rag.create_embeddings()
        print(f"[✓] Created FAISS index with {len(rag.embeddings)} embeddings.")

        # 4. Ask a question and get an answer
        question = "Tell me about Ramesses III"
        answer = rag.generate_answer(question)
        print(f"[✓] Answer:\n{answer}")

    except Exception as e:
        print(f"[✗] Error occurred: {e}")
