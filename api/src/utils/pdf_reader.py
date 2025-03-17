from llmsherpa.readers import LayoutPDFReader
import os
from dotenv import load_dotenv

load_dotenv()


def get_pdf_reader():
    return LayoutPDFReader(os.getenv("LLMSHERPA_API_URL"))
