# Import libraries
from weasyprint import HTML
from html2docx import html2docx as convert_html2docx
from io import BytesIO

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

    # Close the buffer and return the bytes
    outputBuffer.close()
    return output