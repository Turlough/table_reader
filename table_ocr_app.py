import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QLabel, QScrollArea, QMessageBox, QPushButton, QVBoxLayout,
                             QFileDialog, QDialog, QSpinBox, QDialogButtonBox)
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt, QPoint, QLineF, QRectF

# Import the new classes
from ocr import OCR
from gridlines import Line, LineEndpoint, CustomLineWidget
from grid_dialog import GridDialog

class TableOCRApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_path = None
        self.horizontal_lines = None
        self.vertical_lines = None
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

        # Line Buttons
        self.draw_lines_button = QPushButton("Draw Lines")
        self.draw_lines_button.clicked.connect(self.show_line_dialog)
        self.draw_lines_button.setEnabled(False)
        button_layout.addWidget(self.draw_lines_button)

        self.lock_lines_button = QPushButton("Lock Lines")
        self.lock_lines_button.clicked.connect(self.toggle_lines_lock)
        self.lock_lines_button.setEnabled(False)
        button_layout.addWidget(self.lock_lines_button)

        # Other Buttons
        self.straighten_button = QPushButton("Straighten")
        button_layout.addWidget(self.straighten_button)

        self.ocr_button = QPushButton("OCR")
        self.ocr_button.clicked.connect(self.start_ocr)
        self.ocr_button.setEnabled(False)
        button_layout.addWidget(self.ocr_button)

        button_layout.addStretch() # Pushes buttons to the left
        left_layout.addLayout(button_layout) # Add the button row layout

        # Image display widget
        self.image_widget = CustomLineWidget()
        self.image_widget.setStyleSheet("border: 1px solid lightgrey; min-height: 500px;")

        # Scroll Area for Image
        scroll_area_left = QScrollArea()
        scroll_area_left.setWidgetResizable(True)
        scroll_area_left.setWidget(self.image_widget)
        scroll_area_left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(scroll_area_left, 1)

        main_layout.addWidget(left_panel_widget, 1)

        # --- Right Panel: OCR Results ---
        right_panel_widget = QWidget()
        right_layout = QVBoxLayout(right_panel_widget)
        
        # OCR Results display
        self.results_widget = CustomLineWidget()
        self.results_widget.setStyleSheet("border: 1px solid lightgrey; min-height: 500px;")
        
        # Scroll Area for Results
        scroll_area_right = QScrollArea()
        scroll_area_right.setWidgetResizable(True)
        scroll_area_right.setWidget(self.results_widget)
        scroll_area_right.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(scroll_area_right, 1)
        
        main_layout.addWidget(right_panel_widget, 1)

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
            return

        pixmap = QPixmap(self.image_path)
        if pixmap.isNull():
            error_msg = f"Could not load image: {self.image_path}"
            QMessageBox.warning(self, "Error", error_msg)
            self.image_path = None
            return

        scaled_pixmap = pixmap.scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_widget.set_image(scaled_pixmap)
        self.draw_lines_button.setEnabled(True)
        self.ocr_button.setEnabled(True)

    def show_line_dialog(self):
        """Shows the dialog to create lines."""
        dialog = GridDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            horizontal, vertical = dialog.get_dimensions()
            self.image_widget.create_lines(horizontal, vertical)
            self.lock_lines_button.setEnabled(True)

    def toggle_lines_lock(self):
        """Toggles the lines lock state."""
        is_locked, horizontal_lines, vertical_lines = self.image_widget.toggle_lock()
        self.lock_lines_button.setText("Unlock Lines" if is_locked else "Lock Lines")
        if is_locked:
            self.horizontal_lines = horizontal_lines
            self.vertical_lines = vertical_lines

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
        
    def on_ocr_completed(self, header, data):
        """Handles successful OCR completion with data."""
        QApplication.restoreOverrideCursor()
        
    def on_ocr_error(self, error_message):
        """Handles OCR processing errors."""
        QApplication.restoreOverrideCursor()
        QMessageBox.critical(self, "OCR Error", f"Failed to process image with OCR: {error_message}")
        print(f"Error during OCR processing: {error_message}")
        
    def on_ocr_no_results(self):
        """Handles the case when OCR completes but finds no data."""
        QApplication.restoreOverrideCursor()
        QMessageBox.information(self, "OCR Result", "No table data could be extracted from the image.")

def main():
    app = QApplication(sys.argv)
    main_window = TableOCRApp()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 