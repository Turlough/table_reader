import os
import sys
from PyQt6.QtCore import QObject, pyqtSignal

try:
    from google.cloud import vision
except ImportError:
    print("Error: google-cloud-vision library not found.")
    print("Please install it using: pip install google-cloud-vision")
    sys.exit(1)

class OCR(QObject):
    # Define signals
    ocr_completed = pyqtSignal(list, list)  # Signal (header, data)
    ocr_error = pyqtSignal(str)  # Signal for errors
    ocr_started = pyqtSignal()  # Signal when OCR begins
    ocr_no_results = pyqtSignal()  # Signal when OCR finds no data

    def __init__(self, parent=None):
        """Initialize the OCR class that uses Google Cloud Vision API."""
        super().__init__(parent)
        # Check for credentials environment variable
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            print("Warning: GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
            print("You will need to set this before performing OCR operations.")

    def process_image(self, image_path):
        """Detects document text in an image using Google Cloud Vision."""
        self.ocr_started.emit()  # Signal the start of OCR processing
        
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            error_msg = "GOOGLE_APPLICATION_CREDENTIALS environment variable is not set."
            self.ocr_error.emit(error_msg)
            raise EnvironmentError(error_msg)

        try:
            client = vision.ImageAnnotatorClient()
            with open(image_path, "rb") as image_file:
                content = image_file.read()
            image = vision.Image(content=content)

            response = client.document_text_detection(image=image)

            if response.error.message:
                error_msg = f"Vision API Error: {response.error.message}"
                self.ocr_error.emit(error_msg)
                raise Exception(error_msg)

            header, data = self._analyze_document_layout(response)
            
            if not data and not header:
                self.ocr_no_results.emit()
            else:
                self.ocr_completed.emit(header, data)

        except Exception as e:
            error_msg = f"Error calling Google Cloud Vision API or processing response: {e}"
            print(error_msg)
            self.ocr_error.emit(str(e))
            raise # Reraise the exception

    def _analyze_document_layout(self, response):
        """
        Analyzes the document structure from the Vision API response to infer table cells.
        This uses heuristics based on word coordinates and assumes 4 columns.
        """
        data = []
        header = []
        if not response.full_text_annotation.pages:
            return header, data # No text found

        page = response.full_text_annotation.pages[0]

        lines = {} # Dictionary to hold words per line {avg_y: [ (avg_x, word_text), ... ]}
        tolerance = 50 # Y-coordinate tolerance for grouping words into lines

        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = "".join([symbol.text for symbol in word.symbols])
                    if not word.bounding_box.vertices: continue # Skip if no bounding box

                    avg_y = sum(v.y for v in word.bounding_box.vertices) / 4
                    avg_x = sum(v.x for v in word.bounding_box.vertices) / 4

                    found_line = False
                    for line_y in lines.keys():
                        if abs(avg_y - line_y) < tolerance:
                            lines[line_y].append({'x': avg_x, 'text': word_text})
                            # Update line_y to be average of current words? Maybe later.
                            found_line = True
                            break
                    if not found_line:
                        lines[avg_y] = [{'x': avg_x, 'text': word_text}]

        if not lines:
            return header, data # No text grouped into lines

        # Sort lines by Y coordinate
        sorted_lines_y = sorted(lines.keys())

        # Determine rough column boundaries based on X-coordinates (assuming 4 columns)
        all_x_coords = [word['x'] for line_y in sorted_lines_y for word in lines[line_y]]
        if not all_x_coords: return header, data # No words found

        min_x, max_x = min(all_x_coords), max(all_x_coords)
        image_width = page.width # Use page width if available, otherwise use max_x
        # If min/max are very close, avoid division by zero
        effective_width = max(image_width, max_x) - min_x
        if effective_width <= 0: effective_width = 1 # Prevent division by zero

        # Estimate boundaries assuming 4 roughly equal columns within text area
        num_cols = 4
        col_width = effective_width / num_cols
        # Boundaries are between columns
        col_boundaries = [min_x + (i + 1) * col_width for i in range(num_cols - 1)]

        processed_data = []
        for line_y in sorted_lines_y:
            line_words = sorted(lines[line_y], key=lambda w: w['x']) # Sort words by X
            row = [""] * num_cols # Initialize row

            for word in line_words:
                col_idx = 0
                # Find which column the word belongs to based on its x-coordinate
                for i in range(num_cols - 1):
                    if word['x'] > col_boundaries[i]:
                        col_idx = i + 1
                    else:
                        break # Found the column
                row[col_idx] = (row[col_idx] + " " + word['text']).strip()

            # Add row only if it contains some text
            if any(cell.strip() for cell in row):
                 processed_data.append(row)

        # Basic Heuristic: Assume first non-empty row is header, rest is data
        if processed_data:
            header = processed_data[0]
            data = processed_data[1:]
        else:
            # Provide default header if no data rows found
            header = [f"Column {i+1}" for i in range(num_cols)]
            data = []

        return header, data 