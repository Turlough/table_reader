import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QLabel, QScrollArea, QMessageBox, QPushButton, QVBoxLayout,
                             QFileDialog)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

# Import the new classes
from ocr import OCR
from table_widget import TableWidget

class TableOCRApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_path = None
        self.setWindowTitle("Handwritten Table OCR")
        self.setGeometry(100, 100, 1200, 750)
        
        # Initialize OCR object
        self.ocr = OCR(self)  # Pass self as parent for proper cleanup
        
        # Connect OCR signals to slots
        self.ocr.ocr_started.connect(self.on_ocr_started)
        self.ocr.ocr_completed.connect(self.on_ocr_completed)
        self.ocr.ocr_error.connect(self.on_ocr_error)
        self.ocr.ocr_no_results.connect(self.on_ocr_no_results)

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
        self.ocr_button.clicked.connect(self.start_ocr)
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
        self.table_widget = TableWidget(self)
        main_layout.addWidget(self.table_widget, 1)

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
            self.table_widget.clear_table()
            return

        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        if scaled_pixmap.width() > 600 or scaled_pixmap.height() > 600:
             scaled_pixmap = pixmap.scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())

    # OCR-related methods
    def start_ocr(self):
        """Initiates OCR processing on the current image."""
        if not self.image_path:
            QMessageBox.information(self, "Info", "Please load an image first.")
            return
            
        # The OCR process will now happen asynchronously through signals
        try:
            # Start OCR processing - results will come through signals
            self.ocr.process_image(self.image_path)
        except Exception as e:
            # Handle any exceptions that weren't caught by the OCR signal system
            QMessageBox.critical(self, "OCR Error", f"Failed to start OCR processing: {e}")
            print(f"Error starting OCR: {e}")

    # Signal handlers (slots)
    def on_ocr_started(self):
        """Handles the start of OCR processing."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.table_widget.clear_table()
        
    def on_ocr_completed(self, header, data):
        """Handles successful OCR completion with data."""
        self.table_widget.display_data(header, data)
        QApplication.restoreOverrideCursor()
        
    def on_ocr_error(self, error_message):
        """Handles OCR processing errors."""
        QApplication.restoreOverrideCursor()
        QMessageBox.critical(self, "OCR Error", f"Failed to process image with OCR: {error_message}")
        print(f"Error during OCR processing: {error_message}")
        self.table_widget.clear_table()
        
    def on_ocr_no_results(self):
        """Handles the case when OCR completes but finds no data."""
        QApplication.restoreOverrideCursor()
        QMessageBox.information(self, "OCR Result", "No table data could be extracted from the image.")
        self.table_widget.setup_empty_table()


def main():
    app = QApplication(sys.argv)
    main_window = TableOCRApp()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 