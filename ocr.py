import os
import sys
import cv2
import numpy as np
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
    cell_processed = pyqtSignal(int, int, str)  # Signal (row, col, text) for each processed cell

    def __init__(self, parent=None):
        """Initialize the OCR class that uses Google Cloud Vision API."""
        super().__init__(parent)
        # Check for credentials environment variable
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            print("Warning: GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
            print("You will need to set this before performing OCR operations.")
        self.client = vision.ImageAnnotatorClient()

    def process_cell(self, image_path, cell_corners):
        """Process a single cell with perspective correction."""
        try:
            # Read the image
            img = cv2.imread(image_path)
            if img is None:
                raise Exception(f"Could not read image: {image_path}")

            # Convert corners to numpy array
            src_points = np.array(cell_corners, dtype=np.float32)
            
            # Calculate width and height of the cell
            width = max(
                np.linalg.norm(src_points[0] - src_points[1]),
                np.linalg.norm(src_points[2] - src_points[3])
            )
            height = max(
                np.linalg.norm(src_points[0] - src_points[3]),
                np.linalg.norm(src_points[1] - src_points[2])
            )
            
            # Define destination points for perspective transform
            dst_points = np.array([
                [0, 0],
                [width, 0],
                [width, height],
                [0, height]
            ], dtype=np.float32)
            
            # Get perspective transform matrix
            matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            
            # Apply perspective transform
            warped = cv2.warpPerspective(img, matrix, (int(width), int(height)))
            
            # Convert to bytes for Vision API
            _, buffer = cv2.imencode('.png', warped)
            content = buffer.tobytes()
            
            # Create Vision API image
            image = vision.Image(content=content)
            
            # Perform text detection
            response = self.client.document_text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Vision API Error: {response.error.message}")
            
            # Extract text from response
            text = response.full_text_annotation.text if response.full_text_annotation else ""
            return text.strip()
            
        except Exception as e:
            print(f"Error processing cell: {e}")
            return ""

    def process_image(self, image_path, grid_cells):
        """Process the entire image cell by cell."""
        self.ocr_started.emit()
        
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            error_msg = "GOOGLE_APPLICATION_CREDENTIALS environment variable is not set."
            self.ocr_error.emit(error_msg)
            raise EnvironmentError(error_msg)

        try:
            # Initialize empty table
            num_rows = len(grid_cells)
            num_cols = len(grid_cells[0]) if num_rows > 0 else 0
            table_data = [["" for _ in range(num_cols)] for _ in range(num_rows)]
            
            # Process each cell
            for row_idx, row in enumerate(grid_cells):
                for col_idx, cell in enumerate(row):
                    text = self.process_cell(image_path, cell.get_vertices())
                    table_data[row_idx][col_idx] = text
                    self.cell_processed.emit(row_idx, col_idx, text)
            
            # First row is header, rest is data
            header = table_data[0] if table_data else []
            data = table_data[1:] if len(table_data) > 1 else []
            
            if not any(any(cell.strip() for cell in row) for row in table_data):
                self.ocr_no_results.emit()
            else:
                self.ocr_completed.emit(header, data)
                
        except Exception as e:
            error_msg = f"Error processing image: {e}"
            print(error_msg)
            self.ocr_error.emit(str(e))
            raise 