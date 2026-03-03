import re
import fitz 
from loguru import logger
from config import AppConfig

config = AppConfig()


class TextProcessor:
    """
    Responsible for:
        Extracting text from PDF or raw string
        Cleaning the text
        Splitting into overlapping chunks for RAG
    """

    def __init__(self):
        self.chunk_size = config.CHUNK_SIZE
        self.chunk_overlap = config.CHUNK_OVERLAP
        logger.info(f"TextProcessor ready | chunk_size={self.chunk_size} | overlap={self.chunk_overlap}")


    #Extract 

    def extract_from_pdf(self, pdf_path: str) -> str:
        """Read all text from a PDF file."""
        logger.info(f"Extracting text from PDF: {pdf_path}")
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            for page_num, page in enumerate(doc):
                text = page.get_text()
                full_text += f"\n{text}"
                logger.debug(f"  Page {page_num + 1} extracted ({len(text)} chars)")
            doc.close()
            logger.success(f"PDF extracted — total {len(full_text)} characters")
            return full_text
        except Exception as e:
            logger.error(f"Failed to read PDF: {e}")
            raise

    def extract_from_string(self, text: str) -> str:
        """Accept raw pasted text directly."""
        logger.info(f"Raw text received — {len(text)} characters")
        return text

    #Clean 

    def clean_text(self, text: str) -> str:
        """
        Clean extracted text:
            Remove excessive whitespace
            Remove special characters that break tokenization
            Normalize Arabic and English text
        """
        logger.info("Cleaning text...")


        text = re.sub(r'[^\x20-\x7E\u0600-\u06FF\n]', ' ', text) 
        text = re.sub(r' +', ' ', text) 
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip() 

        logger.success(f"Text cleaned — {len(text)} characters remaining")
        return text
 
    #CHUNKING

    def chunk_text(self, text: str) -> list[dict]:
        """
        Split text into overlapping chunks.
        Each chunk is a dict with:
           chunk_id   : int
           text       : str
           char_start : int
           char_end   : int
        """

        logger.info("Chunking text...")
        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = start + self.chunk_size
            if end < len(text):
                boundary = self._find_sentence_boundary(text, end)
                end = boundary if boundary != -1 else end

            chunk_text = text[start:end].strip()

            if len(chunk_text) > 50:  # skip tiny leftover chunks
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "char_start": start,
                    "char_end": end,
                })
                chunk_id += 1
 
            start = end - self.chunk_overlap

        logger.success(f"Chunking done — {len(chunks)} chunks created")
        return chunks

    def _find_sentence_boundary(self, text: str, position: int) -> int:
        """
        Look backwards from position to find the nearest sentence end.
        Returns -1 if none found within 100 chars.
        """
        search_start = max(0, position - 100)
        window = text[search_start:position]
 
        for i in range(len(window) - 1, -1, -1):
            if window[i] in ".!?":
                return search_start + i + 1

        return -1
 
    #Full pipeline

    def process_pdf(self, pdf_path: str) -> list[dict]:
        """Full pipeline: PDF → clean → chunks."""
        raw = self.extract_from_pdf(pdf_path)
        clean = self.clean_text(raw)
        chunks = self.chunk_text(clean)
        return chunks

    def process_text(self, text: str) -> list[dict]:
        """Full pipeline: raw text → clean → chunks."""
        clean = self.clean_text(text)
        chunks = self.chunk_text(clean)
        return chunks