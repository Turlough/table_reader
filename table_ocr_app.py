import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                             QScrollArea, QMessageBox, QPushButton, QVBoxLayout,
                             QFileDialog)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

try:
    from google.cloud import vision
except ImportError:
    print("Error: google-cloud-vision library not found.")
    print("Please install it using: pip install google-cloud-vision")
    sys.exit(1)

def analyze_document_layout(response):
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


def get_table_data_from_image(image_path):
    """Detects document text in an image using Google Cloud Vision."""
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")

    try:
        client = vision.ImageAnnotatorClient()
        with open(image_path, "rb") as image_file:
            content = image_file.read()
        image = vision.Image(content=content)

        response = client.document_text_detection(image=image)

        if response.error.message:
            raise Exception(
                f"Vision API Error: {response.error.message}"
            )

        header, data = analyze_document_layout(response)
        return header, data

    except Exception as e:
        print(f"Error calling Google Cloud Vision API or processing response: {e}")
        raise # Reraise the exception


class TableOCRApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_path = None
        self.setWindowTitle("Handwritten Table OCR")
        self.setGeometry(100, 100, 1200, 750)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Left Panel: Image Display and Load Button ---
        left_panel_widget = QWidget()
        left_layout = QVBoxLayout(left_panel_widget)

        # --- Button Row ---
        button_layout = QHBoxLayout()

        # Load Image Button
        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.open_image_dialog)
        button_layout.addWidget(self.load_button)

        # New Buttons
        self.straighten_button = QPushButton("Straighten")
        # self.straighten_button.clicked.connect(self.straighten_image) # Placeholder
        button_layout.addWidget(self.straighten_button)

        self.crop_button = QPushButton("Crop")
        # self.crop_button.clicked.connect(self.crop_image) # Placeholder
        button_layout.addWidget(self.crop_button)

        self.ocr_button = QPushButton("OCR")
        self.ocr_button.clicked.connect(self.load_ocr_data) # Connect to existing OCR function
        button_layout.addWidget(self.ocr_button)

        button_layout.addStretch() # Pushes buttons to the left
        left_layout.addLayout(button_layout) # Add the button row layout

        # Image Display Area
        self.image_label = QLabel("Please load an image.")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid lightgrey; min-height: 500px;")

        # Scroll Area for Image
        scroll_area_left = QScrollArea()
        scroll_area_left.setWidgetResizable(True)
        scroll_area_left.setWidget(self.image_label)
        scroll_area_left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(scroll_area_left, 1)

        main_layout.addWidget(left_panel_widget, 1)

        # --- Right Panel: Table Display ---
        self.table_widget = QTableWidget()
        self.table_widget.setStyleSheet("QTableWidget { border: 1px solid lightgrey; }")
        main_layout.addWidget(self.table_widget, 1)

        # Initial empty table setup
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels([f"Column {i+1}" for i in range(4)])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def open_image_dialog(self):
        """Opens a file dialog to select an image and processes it."""
        initial_dir = r"C:\_PV\tables"
        if not os.path.isdir(initial_dir):
             initial_dir = os.path.expanduser("~")

        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            initial_dir,
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff);;All Files (*)"
        )
        if file_name:
            self.image_path = file_name
            self.display_image()
            # if self.image_path: # Removed automatic OCR call
            #      self.load_ocr_data()

    def display_image(self):
        """Loads and displays the selected image."""
        if not self.image_path:
            self.image_label.setText("No image selected.")
            return

        pixmap = QPixmap(self.image_path)
        if pixmap.isNull():
            error_msg = f"Could not load image: {self.image_path}"
            QMessageBox.warning(self, "Error", error_msg)
            self.image_label.setText(error_msg)
            self.image_path = None
            self.table_widget.clear()
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
            return

        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        if scaled_pixmap.width() > 600 or scaled_pixmap.height() > 600:
             scaled_pixmap = pixmap.scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())

    def load_ocr_data(self):
        """Loads OCR data from the currently set image_path."""
        if not self.image_path:
             QMessageBox.information(self, "Info", "Please load an image first.")
             self.table_widget.clear()
             self.table_widget.setRowCount(0)
             self.table_widget.setColumnCount(0)
             return
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
             QMessageBox.critical(self, "Configuration Error",
                                   "GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.\n"
                                   "Cannot perform OCR.")
             self.table_widget.clear()
             self.table_widget.setRowCount(0)
             self.table_widget.setColumnCount(0)
             return

        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.table_widget.clear()
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)

            header, data = get_table_data_from_image(self.image_path)

            if not data and not header:
                QMessageBox.information(self, "OCR Result", "No table data could be extracted from the image.")
                num_cols = 4
                self.table_widget.setColumnCount(num_cols)
                self.table_widget.setHorizontalHeaderLabels([f"Column {i+1}" for i in range(num_cols)])
                self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                QApplication.restoreOverrideCursor()
                return

            num_rows = len(data)
            num_cols = len(header) if header else (len(data[0]) if data else 4)

            self.table_widget.setRowCount(num_rows)
            self.table_widget.setColumnCount(num_cols)

            if header:
                self.table_widget.setHorizontalHeaderLabels(header)
            else:
                self.table_widget.setHorizontalHeaderLabels([f"Column {i+1}" for i in range(num_cols)])

            for row_idx, row_data in enumerate(data):
                current_cols = len(row_data)
                if current_cols < num_cols:
                    row_data.extend([""] * (num_cols - current_cols))
                elif current_cols > num_cols:
                    row_data = row_data[:num_cols]

                for col_idx, cell_data in enumerate(row_data):
                    self.table_widget.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))

            self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.table_widget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            QApplication.restoreOverrideCursor()

        except EnvironmentError as e:
             QApplication.restoreOverrideCursor()
             QMessageBox.critical(self, "Configuration Error", f"{e}\nPlease set the GOOGLE_APPLICATION_CREDENTIALS environment variable.")
             print(f"Configuration Error: {e}")
             self.table_widget.clear()
             self.table_widget.setRowCount(0)
             self.table_widget.setColumnCount(0)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "OCR Error", f"Failed to process image with OCR: {e}")
            print(f"Error during OCR processing: {e}")
            self.table_widget.clear()
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)


def main():
    app = QApplication(sys.argv)
    main_window = TableOCRApp()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 