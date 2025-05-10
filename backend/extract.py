import os
import mimetypes
import pypdf
import docx2txt
import re

def detect_mimetype(filename_with_extension: str) -> str:
    """
    Detect the MIME type of a file using its filename (expected to have an extension).
    
    Args:
        filename_with_extension: The original name of the file, including its extension.
        
    Returns:
        MIME type string, or "application/octet-stream" if undetectable.
    """
    mime_type, _ = mimetypes.guess_type(filename_with_extension)
    
    if mime_type is None:
        # If type cannot be determined from filename, default to a generic binary type
        return "application/octet-stream" 
        
    return mime_type

def clean_text(text: str) -> str:
    """
    Clean extracted text to remove binary content and non-readable characters.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Remove non-printable characters but keep basic punctuation and whitespace
    text = re.sub(r'[^\x20-\x7E\n\r\t]', ' ', text)
    
    # Remove common PDF structural elements that might be mistakenly extracted as text
    text = re.sub(r'(?:endobj|endstream|obj|stream|\/Type|\/FontDescriptor|\/XYZ|\/Page[s]?|\/Catalog|\/Outlines|\/StructTreeRoot|\/MarkInfo|\/Metadata|\/PieceInfo|\/LastModified|\/Creator|\/Producer|\/CreationDate|\/ModDate|\/OpenAction|\/AcroForm|\/Filter|\/Subtype|\/Length\d*|\/Width|\/Height|\/ColorSpace|\/BitsPerComponent|\/Filter|\/DecodeParms|\/ASCIIHexDecode|\/FlateDecode|\/DCTDecode|\/JPXDecode|\/CCITTFaxDecode|\/JBIG2Decode|xref|trailer|startxref|%%EOF)', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\<\<.*?\>\>', ' ', text) # Remove dictionaries <</.../>>
    text = re.sub(r'\s+', ' ', text) # Consolidate multiple spaces
    
    return text.strip()

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    try:
        with open(file_path, "rb") as f:
            pdf = pypdf.PdfReader(f)
            
            if not pdf.pages:
                 return "[Warning: PDF has no pages or is encrypted and cannot be read.]"

            for page_num, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as e:
                    # Log or handle page-specific extraction errors if needed
                    text += f"[Warning: Could not extract text from page {page_num + 1}: {str(e)}]\n"
            
            text = clean_text(text)
            
            if not text.strip() or len(text.strip()) < 50 : # Check if cleaned text is too short or empty
                 # Attempt an alternative extraction if the primary one yields little or no text
                alternative_text = ""
                for page in pdf.pages:
                    try:
                        # pypdf's visitor functions can sometimes get more text
                        parts = []
                        def visitor_text(text, cm, tm, fontDict, fontSize):
                            parts.append(text)
                        page.extract_text(visitor_text=visitor_text)
                        if parts:
                            alternative_text += "".join(parts) + "\n"
                    except:
                        pass # Ignore errors in alternative method
                
                cleaned_alternative_text = clean_text(alternative_text)
                if len(cleaned_alternative_text.strip()) > len(text.strip()):
                    text = cleaned_alternative_text

            if not text.strip() or len(text.strip()) < 50:
                text = "[Warning: Limited text could be extracted from this PDF. It may contain mostly images, be scanned, or have complex formatting.]"
    
    except pypdf.errors.PdfReadError as e:
        return f"[Error: Could not read PDF. It might be corrupted or encrypted: {str(e)}]"
    except Exception as e:
        return f"[Error extracting text from PDF: {str(e)}]"
    
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        return docx2txt.process(file_path)
    except Exception as e:
        return f"[Error extracting text from DOCX: {str(e)}]"

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from a text file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text_content = f.read()
        return clean_text(text_content) # Clean even plain text for consistency
    except Exception as e:
        return f"[Error extracting text from TXT: {str(e)}]"

def extract_text(file_path: str, original_filename: str) -> str:
    """
    Extract text from a file based on its MIME type, determined from original_filename.
    
    Args:
        file_path: Path to the temporary file content.
        original_filename: The original name of the file, used for MIME type detection.
        
    Returns:
        Extracted text as string
    """
    mime_type = detect_mimetype(original_filename)
    
    if mime_type == "application/pdf":
        return extract_text_from_pdf(file_path)
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file_path)
    elif mime_type.startswith("text/"):
        return extract_text_from_txt(file_path)
    elif mime_type == "application/octet-stream": # Handle our new default for unknown
        # Attempt to read as text as a last resort for octet-stream
        extracted = extract_text_from_txt(file_path)
        if not extracted.startswith("[Error"):
            return extracted
        else: # If text extraction fails, return a specific message for octet-stream
             return f"[Warning: File type is generic ('{mime_type}'), and text extraction failed. Content might be binary or an unsupported format.]"
    else:
        return f"[Error: Cannot extract text from file with MIME type {mime_type}. Unsupported format.]" 