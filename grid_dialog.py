from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                            QLabel, QSpinBox, QDialogButtonBox)

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