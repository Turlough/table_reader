import sys
import os
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QLabel, QScrollArea, QMessageBox, QPushButton, QVBoxLayout,
                             QFileDialog, QDialog, QSpinBox, QDialogButtonBox, QTableWidget,
                             QTableWidgetItem, QLineEdit, QSizePolicy)
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QImage
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
        self.original_image = None  # Store the original image for cropping
        self.setWindowTitle("Handwritten Table OCR")
        self.setGeometry(100, 100, 1200, 750)
        
        # Initialize OCR object
        self.ocr = OCR(self)  # Pass self as parent for proper cleanup
        
        # Connect OCR signals to slots
        self.ocr.ocr_started.connect(self.on_ocr_started)
        self.ocr.ocr_completed.connect(self.on_ocr_completed)
        self.ocr.ocr_error.connect(self.on_ocr_error)
        self.ocr.ocr_no_results.connect(self.on_ocr_no_results)
        self.ocr.cell_processed.connect(self.on_cell_processed)

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
        right_panel_widget.setFixedWidth(700)  # Set fixed width for the right panel
        right_layout = QVBoxLayout(right_panel_widget)
        
        # Add cell image display
        self.cell_image = QLabel()
        self.cell_image.setStyleSheet("border: 1px solid lightgrey;")
        self.cell_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cell_image.setFixedHeight(200)  # Set fixed height only
        self.cell_image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Allow horizontal expansion
        right_layout.addWidget(self.cell_image)
        
        # Add cell text input
        self.cell_text = QLineEdit()
        self.cell_text.setPlaceholderText("Cell text will appear here")
        right_layout.addWidget(self.cell_text)
        
        # Create table widget for results
        self.results_table = QTableWidget()
        self.results_table.setStyleSheet("border: 1px solid lightgrey;")
        right_layout.addWidget(self.results_table)
        
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

        # Load image with OpenCV for cropping
        self.original_image = cv2.imread(self.image_path)
        if self.original_image is None:
            error_msg = f"Could not load image: {self.image_path}"
            QMessageBox.warning(self, "Error", error_msg)
            self.image_path = None
            return

        # Convert to RGB for display
        rgb_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
        height, width = rgb_image.shape[:2]
        
        # Create QImage and QPixmap
        bytes_per_line = 3 * width
        q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
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
            
            # Create matching table in right panel
            self.results_table.setRowCount(horizontal)
            self.results_table.setColumnCount(vertical)
            self.results_table.resizeColumnsToContents()
            self.results_table.resizeRowsToContents()
            
            # Connect cell selection signal from image widget
            self.image_widget.cell_selected.connect(self.on_cell_selected)

    def toggle_lines_lock(self):
        """Toggles the lines lock state."""
        is_locked, horizontal_lines, vertical_lines = self.image_widget.toggle_lock()
        self.lock_lines_button.setText("Unlock Lines" if is_locked else "Lock Lines")
        if is_locked:
            self.horizontal_lines = horizontal_lines
            self.vertical_lines = vertical_lines

    def start_ocr(self):
        """Initiates OCR processing on the current image."""
        if not self.image_path:
            QMessageBox.information(self, "Info", "Please load an image first.")
            return
            
        if not self.horizontal_lines or not self.vertical_lines:
            QMessageBox.information(self, "Info", "Please draw and lock the grid lines first.")
            return
            
        # Calculate grid cells from the lines
        grid_cells = []
        for i in range(len(self.horizontal_lines) - 1):
            row_cells = []
            top_line = self.horizontal_lines[i]
            bottom_line = self.horizontal_lines[i + 1]
            
            for j in range(len(self.vertical_lines) - 1):
                left_line = self.vertical_lines[j]
                right_line = self.vertical_lines[j + 1]
                
                # Get cell corners from line intersections
                top_left = [left_line.start.x, top_line.start.y]
                top_right = [right_line.start.x, top_line.start.y]
                bottom_right = [right_line.start.x, bottom_line.start.y]
                bottom_left = [left_line.start.x, bottom_line.start.y]
                
                cell = Cell(top_left, top_right, bottom_right, bottom_left)
                row_cells.append(cell)
            
            grid_cells.append(row_cells)
        
        # Initialize results table
        self.results_table.setRowCount(len(grid_cells))
        self.results_table.setColumnCount(len(grid_cells[0]) if grid_cells else 0)
        
        # Start OCR processing
        try:
            self.ocr.process_image(self.image_path, grid_cells)
        except Exception as e:
            QMessageBox.critical(self, "OCR Error", f"Failed to start OCR processing: {e}")

    def on_cell_processed(self, row, col, text):
        """Handles individual cell OCR results."""
        item = QTableWidgetItem(text)
        self.results_table.setItem(row, col, item)
        self.results_table.resizeColumnsToContents()
        self.results_table.resizeRowsToContents()

    def on_ocr_started(self):
        """Handles the start of OCR processing."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
    def on_ocr_completed(self, header, data):
        """Handles successful OCR completion with data."""
        QApplication.restoreOverrideCursor()
        # Set header labels
        for col, text in enumerate(header):
            self.results_table.setHorizontalHeaderItem(col, QTableWidgetItem(text))
        
    def on_ocr_error(self, error_message):
        """Handles OCR processing errors."""
        QApplication.restoreOverrideCursor()
        QMessageBox.critical(self, "OCR Error", f"Failed to process image with OCR: {error_message}")
        print(f"Error during OCR processing: {error_message}")
        
    def on_ocr_no_results(self):
        """Handles the case when OCR completes but finds no data."""
        QApplication.restoreOverrideCursor()
        QMessageBox.information(self, "OCR Result", "No table data could be extracted from the image.")

    def on_cell_selected(self, row, col):
        """Handle cell selection from the image widget."""
        # Highlight the corresponding cell in the table
        self.results_table.selectRow(row)
        self.results_table.selectColumn(col)

        # Get the cell boundaries from the lines
        if self.horizontal_lines and self.vertical_lines:
            # Get the cell boundaries from the scaled display
            top = int(self.horizontal_lines[row].start.y)
            bottom = int(self.horizontal_lines[row + 1].start.y)
            left = int(self.vertical_lines[col].start.x)
            right = int(self.vertical_lines[col + 1].start.x)
            
            # Get the original image dimensions
            orig_height, orig_width = self.original_image.shape[:2]
            
            # Get the scaled display dimensions
            display_width = self.image_widget.scaled_pixmap.width()
            display_height = self.image_widget.scaled_pixmap.height()
            
            # Calculate the scaling factors
            width_scale = orig_width / display_width
            height_scale = orig_height / display_height
            
            # Calculate image offset within the widget
            x_offset = (self.image_widget.width() - display_width) // 2
            y_offset = (self.image_widget.height() - display_height) // 2
            
            # Adjust coordinates by the offset before scaling
            top = int((top - y_offset) * height_scale)
            bottom = int((bottom - y_offset) * height_scale)
            left = int((left - x_offset) * width_scale)
            right = int((right - x_offset) * width_scale)
            
            # Ensure coordinates are within image bounds
            top = max(0, min(top, orig_height))
            bottom = max(0, min(bottom, orig_height))
            left = max(0, min(left, orig_width))
            right = max(0, min(right, orig_width))
            
            # Crop the cell from the original image
            cropped_image = self.original_image[top:bottom, left:right]
            
            # Convert to RGB for display
            cropped_image_rgb = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)
            height, width = cropped_image_rgb.shape[:2]
            
            # Create QImage and QPixmap
            bytes_per_line = 3 * width
            q_image = QImage(cropped_image_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            # Scale the pixmap to fit the label's current dimensions while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(self.cell_image.width(), self.cell_image.height(),
                                        Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
            
            # Display the cropped cell
            self.cell_image.setPixmap(scaled_pixmap)
            
            # Perform OCR on the cell image
            text = self.ocr.process_cell_image(cropped_image)
            
            # Update the text box with the OCR result
            self.cell_text.setText(text)
            
            # Update the table cell if it exists
            current_item = self.results_table.item(row, col)
            if current_item:
                current_item.setText(text)
            else:
                self.results_table.setItem(row, col, QTableWidgetItem(text))

def main():
    app = QApplication(sys.argv)
    main_window = TableOCRApp()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 