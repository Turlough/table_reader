import sys
import os
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QLabel, QPushButton, QVBoxLayout, QFileDialog, QMessageBox)
from PyQt6.QtGui import QPixmap, QPainter, QPen, QImage
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal

class CornerPoint:
    def __init__(self, x, y, radius=10):
        self.x = x
        self.y = y
        self.radius = radius
        
    def contains(self, point):
        return (point.x() - self.x)**2 + (point.y() - self.y)**2 <= self.radius**2
        
    def set_pos(self, x, y):
        self.x = x
        self.y = y

class ImageWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.scaled_pixmap = None
        self.orig_image = None
        self.corners = []
        self.dragging_corner = None
        self.setMouseTracking(True)
        
    def set_image(self, image_path):
        self.pixmap = QPixmap(image_path)
        
        # Convert QPixmap to OpenCV format to preserve orientation
        qimage = self.pixmap.toImage()
        width = qimage.width()
        height = qimage.height()
        
        # Convert QImage to OpenCV format
        ptr = qimage.constBits()
        ptr.setsize(height * width * 4)
        arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
        
        # Convert RGBA to BGR (OpenCV format)
        self.orig_image = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        
        self.update_scaled_pixmap()
        self.init_corners()
        self.update()
        
    def update_scaled_pixmap(self):
        if self.pixmap:
            self.scaled_pixmap = self.pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
    def init_corners(self):
        if not self.scaled_pixmap:
            return
            
        width = self.scaled_pixmap.width()
        height = self.scaled_pixmap.height()
        
        # Calculate position to center the image
        x_offset = (self.width() - width) // 2
        y_offset = (self.height() - height) // 2
        
        # Initialize corners at the four corners of the image
        self.corners = [
            CornerPoint(x_offset, y_offset),                  # Top-left
            CornerPoint(x_offset + width, y_offset),              # Top-right
            CornerPoint(x_offset + width, y_offset + height),         # Bottom-right
            CornerPoint(x_offset, y_offset + height)              # Bottom-left
        ]
    
    def resizeEvent(self, event):
        self.update_scaled_pixmap()
        if self.corners:
            old_width = event.oldSize().width() if event.oldSize().width() > 0 else 1
            old_height = event.oldSize().height() if event.oldSize().height() > 0 else 1
            
            width_ratio = self.width() / old_width
            height_ratio = self.height() / old_height
            
            # Scale corner positions based on resize
            for corner in self.corners:
                corner.x = int(corner.x * width_ratio)
                corner.y = int(corner.y * height_ratio)
        
        super().resizeEvent(event)
    
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
            
            # Draw the quadrilateral
            if len(self.corners) == 4:
                pen = QPen(Qt.GlobalColor.red)
                pen.setWidth(2)
                painter.setPen(pen)
                
                # Draw the quadrilateral lines
                for i in range(4):
                    painter.drawLine(
                        QPoint(self.corners[i].x, self.corners[i].y),
                        QPoint(self.corners[(i+1)%4].x, self.corners[(i+1)%4].y)
                    )
                
                # Draw the draggable corner points
                pen.setColor(Qt.GlobalColor.blue)
                painter.setPen(pen)
                for corner in self.corners:
                    painter.drawEllipse(
                        QPoint(corner.x, corner.y),
                        corner.radius,
                        corner.radius
                    )
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            for i, corner in enumerate(self.corners):
                if corner.contains(event.position()):
                    self.dragging_corner = i
                    break
    
    def mouseMoveEvent(self, event):
        if self.dragging_corner is not None:
            # Update the position of the corner being dragged
            self.corners[self.dragging_corner].set_pos(
                int(event.position().x()),
                int(event.position().y())
            )
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging_corner = None

    def get_perspective_transform(self):
        if not self.corners or self.orig_image is None:
            return None
            
        # Get corner points relative to original image
        src_points = []
        for corner in self.corners:
            # Convert from display coordinates to original image coordinates
            x_ratio = self.orig_image.shape[1] / self.scaled_pixmap.width()
            y_ratio = self.orig_image.shape[0] / self.scaled_pixmap.height()
            
            # Adjust for any offset if image is centered
            x_offset = (self.width() - self.scaled_pixmap.width()) // 2
            y_offset = (self.height() - self.scaled_pixmap.height()) // 2
            
            orig_x = (corner.x - x_offset) * x_ratio
            orig_y = (corner.y - y_offset) * y_ratio
            
            src_points.append([orig_x, orig_y])
        
        src_points = np.array(src_points, dtype=np.float32)
        
        # Define the destination points (rectangle)
        width = max(
            np.linalg.norm(src_points[0] - src_points[1]),
            np.linalg.norm(src_points[2] - src_points[3])
        )
        height = max(
            np.linalg.norm(src_points[0] - src_points[3]),
            np.linalg.norm(src_points[1] - src_points[2])
        )
        
        dst_points = np.array([
            [0, 0],
            [width, 0],
            [width, height],
            [0, height]
        ], dtype=np.float32)
        
        # Compute the perspective transform
        return cv2.getPerspectiveTransform(src_points, dst_points), int(width), int(height)

class PerspectiveCorrectionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_path = None
        
        self.setWindowTitle("Page Perspective Correction")
        self.setGeometry(100, 100, 1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Button row
        button_layout = QHBoxLayout()
        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.open_image_dialog)
        button_layout.addWidget(self.load_button)
        
        self.reshape_button = QPushButton("Reshape")
        self.reshape_button.clicked.connect(self.reshape_image)
        self.reshape_button.setEnabled(False)
        button_layout.addWidget(self.reshape_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Image display
        self.image_widget = ImageWidget()
        main_layout.addWidget(self.image_widget, 1)
        
    def open_image_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            os.path.expanduser("~"),
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;All Files (*)"
        )
        
        if file_name:
            self.image_path = file_name
            self.image_widget.set_image(file_name)
            self.reshape_button.setEnabled(True)
    
    def reshape_image(self):
        if not self.image_path:
            return
            
        # Get the perspective transform
        transform_result = self.image_widget.get_perspective_transform()
        if not transform_result:
            return
            
        transform_matrix, width, height = transform_result
        
        # Apply the transform
        img = self.image_widget.orig_image
        warped_img = cv2.warpPerspective(img, transform_matrix, (width, height))
        
        # Save the result
        file_base, file_ext = os.path.splitext(self.image_path)
        output_path = f"{file_base}_cropped{file_ext}"
        
        cv2.imwrite(output_path, warped_img)
        
        QMessageBox.information(
            self,
            "Image Saved",
            f"Corrected image saved as {output_path}"
        )

def main():
    app = QApplication(sys.argv)
    main_window = PerspectiveCorrectionApp()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 