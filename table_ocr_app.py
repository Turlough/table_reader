import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QLabel, QScrollArea, QMessageBox, QPushButton, QVBoxLayout,
                             QFileDialog, QDialog, QSpinBox, QDialogButtonBox)
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt, QPoint, QLineF, QRectF

# Import the new classes
from ocr import OCR

class LineEndpoint:
    def __init__(self, x, y, radius=5):
        self.x = x
        self.y = y
        self.radius = radius
        
    def contains(self, point):
        return (point.x() - self.x)**2 + (point.y() - self.y)**2 <= self.radius**2
        
    def set_pos(self, x, y):
        self.x = x
        self.y = y

class Line:
    def __init__(self, start: LineEndpoint, end: LineEndpoint):
        self.start = start
        self.end = end

class CustomLineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.scaled_pixmap = None
        self.horizontal_lines = []  # List of Line objects
        self.vertical_lines = []    # List of Line objects
        self.dragging_endpoint = None
        self.is_locked = False
        self.setMouseTracking(True)
        
    def set_image(self, pixmap):
        self.pixmap = pixmap
        self.update_scaled_pixmap()
        self.update()
        
    def update_scaled_pixmap(self):
        if self.pixmap:
            self.scaled_pixmap = self.pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
    def create_lines(self, num_horizontal, num_vertical):
        if not self.scaled_pixmap:
            return
            
        width = self.scaled_pixmap.width()
        height = self.scaled_pixmap.height()
        
        # Calculate position to center the image
        x_offset = (self.width() - width) // 2
        y_offset = (self.height() - height) // 2
        
        # Clear existing lines
        self.horizontal_lines = []
        self.vertical_lines = []
        
        # Create horizontal lines
        for i in range(num_horizontal + 1):
            y = y_offset + (i * height) // num_horizontal
            start = LineEndpoint(x_offset, y)
            end = LineEndpoint(x_offset + width, y)
            self.horizontal_lines.append(Line(start, end))
        
        # Create vertical lines
        for i in range(num_vertical + 1):
            x = x_offset + (i * width) // num_vertical
            start = LineEndpoint(x, y_offset)
            end = LineEndpoint(x, y_offset + height)
            self.vertical_lines.append(Line(start, end))
        
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw background
        painter.fillRect(self.rect(), Qt.GlobalColor.white)
        
        if self.scaled_pixmap:
            # Calculate position to center the image
            x = (self.width() - self.scaled_pixmap.width()) // 2
            y = (self.height() - self.scaled_pixmap.height()) // 2
            
            # Draw the image
            painter.drawPixmap(x, y, self.scaled_pixmap)
            
            # Draw all lines
            pen = QPen(QColor(255, 0, 0))  # Red color
            pen.setWidth(2)
            painter.setPen(pen)
            
            # Draw horizontal lines
            for line in self.horizontal_lines:
                painter.drawLine(
                    QPoint(line.start.x, line.start.y),
                    QPoint(line.end.x, line.end.y)
                )
            
            # Draw vertical lines
            for line in self.vertical_lines:
                painter.drawLine(
                    QPoint(line.start.x, line.start.y),
                    QPoint(line.end.x, line.end.y)
                )
            
            # Draw the endpoints
            pen.setColor(QColor(0, 0, 255))  # Blue color
            painter.setPen(pen)
            
            # Draw horizontal line endpoints
            for line in self.horizontal_lines:
                painter.drawEllipse(QPoint(line.start.x, line.start.y), line.start.radius, line.start.radius)
                painter.drawEllipse(QPoint(line.end.x, line.end.y), line.end.radius, line.end.radius)
            
            # Draw vertical line endpoints
            for line in self.vertical_lines:
                painter.drawEllipse(QPoint(line.start.x, line.start.y), line.start.radius, line.start.radius)
                painter.drawEllipse(QPoint(line.end.x, line.end.y), line.end.radius, line.end.radius)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.is_locked:
            # Check horizontal line endpoints
            for line in self.horizontal_lines:
                if line.start.contains(event.position()):
                    self.dragging_endpoint = (line, 'start', 'horizontal')
                    return
                if line.end.contains(event.position()):
                    self.dragging_endpoint = (line, 'end', 'horizontal')
                    return
            
            # Check vertical line endpoints
            for line in self.vertical_lines:
                if line.start.contains(event.position()):
                    self.dragging_endpoint = (line, 'start', 'vertical')
                    return
                if line.end.contains(event.position()):
                    self.dragging_endpoint = (line, 'end', 'vertical')
                    return
    
    def mouseMoveEvent(self, event):
        if self.dragging_endpoint is not None and not self.is_locked:
            line, end, orientation = self.dragging_endpoint
            endpoint = line.start if end == 'start' else line.end
            
            # Constrain movement based on line orientation
            if orientation == 'horizontal':
                # Only allow vertical movement for horizontal line endpoints
                endpoint.y = int(event.position().y())
            else:
                # Only allow horizontal movement for vertical line endpoints
                endpoint.x = int(event.position().x())
            
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging_endpoint = None
            
    def resizeEvent(self, event):
        self.update_scaled_pixmap()
        if self.horizontal_lines or self.vertical_lines:
            old_width = event.oldSize().width() if event.oldSize().width() > 0 else 1
            old_height = event.oldSize().height() if event.oldSize().height() > 0 else 1
            
            width_ratio = self.width() / old_width
            height_ratio = self.height() / old_height
            
            # Scale all endpoints
            for line in self.horizontal_lines + self.vertical_lines:
                line.start.x = int(line.start.x * width_ratio)
                line.start.y = int(line.start.y * height_ratio)
                line.end.x = int(line.end.x * width_ratio)
                line.end.y = int(line.end.y * height_ratio)
        
        super().resizeEvent(event)
        
    def toggle_lock(self):
        self.is_locked = not self.is_locked
        return self.is_locked

class GridDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Lines")
        
        layout = QVBoxLayout(self)
        
        # Horizontal lines input
        row_layout = QHBoxLayout()
        row_layout.addWidget(QLabel("Number of horizontal lines:"))
        self.horizontal_spinbox = QSpinBox()
        self.horizontal_spinbox.setRange(1, 999999)
        self.horizontal_spinbox.setValue(4)
        row_layout.addWidget(self.horizontal_spinbox)
        layout.addLayout(row_layout)
        
        # Vertical lines input
        col_layout = QHBoxLayout()
        col_layout.addWidget(QLabel("Number of vertical lines:"))
        self.vertical_spinbox = QSpinBox()
        self.vertical_spinbox.setRange(1, 999999)
        self.vertical_spinbox.setValue(4)
        col_layout.addWidget(self.vertical_spinbox)
        layout.addLayout(col_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_dimensions(self):
        return self.horizontal_spinbox.value(), self.vertical_spinbox.value()

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
        # self.straighten_button.clicked.connect(self.straighten_image) # Placeholder
        button_layout.addWidget(self.straighten_button)

        self.crop_button = QPushButton("Crop")
        # self.crop_button.clicked.connect(self.crop_image) # Placeholder
        button_layout.addWidget(self.crop_button)

        self.ocr_button = QPushButton("OCR")
        self.ocr_button.clicked.connect(self.start_ocr)
        self.ocr_button.setEnabled(False)
        button_layout.addWidget(self.ocr_button)

        button_layout.addStretch() # Pushes buttons to the left
        left_layout.addLayout(button_layout) # Add the button row layout

        # Replace QLabel with CustomLineWidget for image display
        self.line_widget = CustomLineWidget()
        self.line_widget.setStyleSheet("border: 1px solid lightgrey; min-height: 500px;")

        # Scroll Area for Image
        scroll_area_left = QScrollArea()
        scroll_area_left.setWidgetResizable(True)
        scroll_area_left.setWidget(self.line_widget)
        scroll_area_left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(scroll_area_left, 1)

        main_layout.addWidget(left_panel_widget, 1)

        # --- Right Panel: Line Display ---
        self.line_widget = CustomLineWidget()
        main_layout.addWidget(self.line_widget, 1)

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
        self.line_widget.set_image(scaled_pixmap)
        self.draw_lines_button.setEnabled(True)
        self.ocr_button.setEnabled(True)

    def show_line_dialog(self):
        """Shows the dialog to create lines."""
        dialog = GridDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            horizontal, vertical = dialog.get_dimensions()
            self.line_widget.create_lines(horizontal, vertical)
            self.lock_lines_button.setEnabled(True)

    def toggle_lines_lock(self):
        """Toggles the lines lock state."""
        is_locked = self.line_widget.toggle_lock()
        self.lock_lines_button.setText("Unlock Lines" if is_locked else "Lock Lines")

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