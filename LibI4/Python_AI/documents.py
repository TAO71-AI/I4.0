# Import libraries
from weasyprint import HTML
from html2docx import html2docx as convert_html2docx
from io import BytesIO
import pandas as pd
import PyPDF2 as PDFReader

def __check_html__(Code: str) -> str:
    """
    Check the HTML code to prevent errors.
    """
    # Check <html> tag
    if ("<html" not in Code.lower().replace(" ", "")):
        Code = f"<html>{Code}</html>"
    
    # Check <head> tag
    if ("<head" not in Code.lower().replace(" ", "")):
        Code = f"{Code[:Code.index('>') + 1]}<head><meta charset = 'UTF-8'></head>{Code[Code.index('>') + 1:]}"
    
    # Check <body> tag
    if ("<body" not in Code.lower().replace(" ", "")):
        Code = Code.replace("</head>", "</head><body>").replace("</html>", "</body></html>")
    
    # Return the code
    return Code

def HTML2PDF(Code: str) -> bytes:
    """
    Creates a PDF document from a HTML code.
    """
    # Check the code
    Code = __check_html__(Code)

    # Create buffer and html object
    outputBuffer = BytesIO()
    html = HTML(string = Code)

    # Write the HTML to PDF and get the bytes of the file
    html.write_pdf(outputBuffer)
    output = outputBuffer.getvalue()

    # Check output bytes
    if (len(output) == 0):
        raise RuntimeError("Error creating document. Probably the syntax is wrong?")

    # Close the buffer and return the bytes
    outputBuffer.close()
    return output

def HTML2DOCX(Code: str) -> bytes:
    """
    Creates a DOCX document from a HTML code.
    """
    # Check the code
    Code = __check_html__(Code)

    # Convert HTML to DOCX and get the bytes of the file
    outputBuffer = convert_html2docx(Code, "")
    output = outputBuffer.getvalue()

    # Check output bytes
    if (len(output) == 0):
        raise RuntimeError("Error creating document. Probably the syntax is wrong?")

    # Close the buffer and return the bytes
    outputBuffer.close()
    return output

def CSV2XLSX(Code: str) -> bytes:
    """
    Creates a XLSX document from a CSV code.
    """
    # Create buffer
    buffer = BytesIO(Code.encode("utf-8"))

    # Convert CSV to XLSX and get the bytes of the file
    pd.read_csv(buffer).to_excel(buffer, index = False, engine = "openpyxl")
    output = buffer.getvalue()

    # Check output bytes
    if (len(output) == 0):
        raise RuntimeError("Error creating document. Probably the syntax is wrong?")

    # Close the buffer and return the bytes
    buffer.close()
    return output

def XLSX2CSV(Document: bytes | BytesIO | str) -> str:
    """
    Converts a XLSX document to a CSV format and returns the content as a string.
    """
    # Create variables
    closeBuffer = False

    # Check document type
    if (isinstance(Document, bytes)):
        # Convert to BytesIO
        Document = BytesIO(Document)
        closeBuffer = True
    elif (isinstance(Document, str)):
        # Convert to BytesIO
        with open(Document, "rb") as f:
            Document = BytesIO(f.read())

        closeBuffer = True
    elif (not isinstance(BytesIO)):
        # Raise an exception
        raise ValueError("INTERNAL SERVER ERROR; DOCUMENTS READER: Document type not valid.")

    # Create buffer
    buffer = BytesIO()

    # Convert XLSX to CSV and get the bytes of the file
    pd.read_excel(Document, engine = "openpyxl").to_csv(buffer, index = False)
    output = buffer.getvalue().decode("utf-8")

    # Close the buffers
    if (closeBuffer):
        Document.close()
    
    buffer.close()

    # Return the output
    return output

def PDF2PLAINTEXT(Document: bytes | BytesIO | str) -> list[str]:
    """
    Extracts the text from a PDF document and returns it as a list of strings, one for each page.
    """
    # Create variables
    closeBuffer = False

    # Check document type
    if (isinstance(Document, bytes)):
        # Convert to BytesIO
        Document = BytesIO(Document)
        closeBuffer = True
    elif (isinstance(Document, str)):
        # Convert to BytesIO
        with open(Document, "rb") as f:
            Document = BytesIO(f.read())

        closeBuffer = True
    elif (not isinstance(BytesIO)):
        # Raise an exception
        raise ValueError("INTERNAL SERVER ERROR; DOCUMENTS READER: Document type not valid.")
    
    # Create reader and pages list
    reader = PDFReader.PdfReader(Document)
    pagesText = []

    # For each page
    for page in reader.pages:
        # Extract the text from the page and append it to the list
        pagesText.append(page.extract_text())
    
    # Close the buffer if needed
    if (closeBuffer):
        Document.close()
    
    # Return the pages text
    return pagesText