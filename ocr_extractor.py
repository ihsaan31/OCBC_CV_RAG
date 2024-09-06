from paddleocr import PaddleOCR
import os
import fitz

# ==================== EXTRACT TEXT FROM PDF ====================
def extract_text_and_images_from_page(doc, page, ocr, treshold):
    text = page.get_text()
    image_text = ""
    image_list = page.get_images(full=True)
    # Iterate through all images found on the page
    for image_info in image_list:
        xref = image_info[0]
        image_dict = doc.extract_image(xref)
        image_bytes = image_dict['image']

        if image_bytes is not None:
            # Use PaddleOCR to extract text from the image
            ocr_result = ocr.ocr(image_bytes)
            # Check if OCR result is valid before processing
            if ocr_result and ocr_result != [None]:
                for result in ocr_result:
                    for res in result:
                        text_tuple = res[1]
                        text_string = text_tuple[0]
                        # For confidence threshold
                        text_confidence = text_tuple[1]
                        if text_confidence > treshold:
                            image_text += text_string + '\n'
    # Combine page text and image text
    return text + "\n" + image_text


def extract_text_from_pdf(uploaded_file, ocr, treshold):
    # Load the PDF file
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    # text = ""
    text = ""
    # Iterate through all pages in the PDF
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Extract text and images from the page
        page_text = extract_text_and_images_from_page(doc, page, ocr, treshold)
        text += page_text + "\n"
        # text += f"page={page_num + 1}\n====================\n{page_text}\n====================\n"
        
    return text