import os
from typing import List
import PyPDF2

'''
###### KEEPING THIS ONLY FOR REFERENCE

class TextFileLoader:
    def __init__(self, path: str, encoding: str = "utf-8"):
        self.documents = []
        self.path = path
        self.encoding = encoding

    def load(self):
        if os.path.isdir(self.path):
            self.load_directory()
        elif os.path.isfile(self.path) and self.path.endswith(".txt"):
            self.load_file()
        else:
            raise ValueError(
                "Provided path is neither a valid directory nor a .txt file."
            )

    def load_file(self):
        with open(self.path, "r", encoding=self.encoding) as f:
            self.documents.append(f.read())

    def load_directory(self):
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.endswith(".txt"):
                    with open(
                        os.path.join(root, file), "r", encoding=self.encoding
                    ) as f:
                        self.documents.append(f.read())

    def load_documents(self):
        self.load()
        return self.documents
'''

class DocumentLoader:
    """
    Enhanced document loader that supports both text and PDF files.
    """
    def __init__(self, path: str, encoding: str = "utf-8"):
        self.documents = []
        self.path = path
        self.encoding = encoding
        self.supported_extensions = [".txt", ".pdf"]

    def load(self):
        if os.path.isdir(self.path):
            self.load_directory()
        elif os.path.isfile(self.path):
            if self.path.endswith(".txt"):
                self.load_text_file()
            elif self.path.endswith(".pdf"):
                self.load_pdf_file()
            else:
                raise ValueError(
                    f"Unsupported file type. Supported types: {self.supported_extensions}"
                )
        else:
            raise ValueError(
                "Provided path is neither a valid directory nor a supported file type."
            )

    def load_text_file(self):
        with open(self.path, "r", encoding=self.encoding) as f:
            self.documents.append(f.read())

    def load_pdf_file(self):
        try:
            with open(self.path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                self.documents.append(text.strip())
        except Exception as e:
            raise ValueError(f"Error reading PDF file {self.path}: {str(e)}")

    def load_directory(self):
        for root, _, files in os.walk(self.path):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith(".txt"):
                    try:
                        with open(file_path, "r", encoding=self.encoding) as f:
                            self.documents.append(f.read())
                    except Exception as e:
                        print(f"Warning: Error reading text file {file_path}: {str(e)}")
                        continue
                elif file.endswith(".pdf"):
                    try:
                        with open(file_path, "rb") as f:
                            pdf_reader = PyPDF2.PdfReader(f)
                            text = ""
                            for page in pdf_reader.pages:
                                text += page.extract_text() + "\n"
                            self.documents.append(text.strip())
                    except Exception as e:
                        print(f"Warning: Error reading PDF file {file_path}: {str(e)}")
                        continue

    def load_documents(self):
        self.load()
        return self.documents

    def get_supported_extensions(self):
        return self.supported_extensions


class CharacterTextSplitter:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        assert (
            chunk_size > chunk_overlap
        ), "Chunk size must be greater than chunk overlap"

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> List[str]:
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunks.append(text[i : i + self.chunk_size])
        return chunks

    def split_texts(self, texts: List[str]) -> List[str]:
        chunks = []
        for text in texts:
            chunks.extend(self.split(text))
        return chunks


if __name__ == "__main__":
    # Test with text file
    # loader = TextFileLoader("data/PMarcaBlogs.txt")
    # loader.load()
    # print(f"Loaded {len(loader.documents)} text documents")
    
    # Test with DocumentLoader (enhanced version)
    doc_loader = DocumentLoader("data/PMarcaBlogs.txt")
    docs = doc_loader.load_documents()
    print(f"DocumentLoader loaded {len(docs)} documents")
    print(f"Supported extensions: {doc_loader.get_supported_extensions()}")
    
    splitter = CharacterTextSplitter()
    chunks = splitter.split_texts(docs)
    print(f"Split into {len(chunks)} chunks")
    print("First chunk preview:")
    if chunks:
        print(chunks[0][:200] + "...")
