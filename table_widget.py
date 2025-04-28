from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import QObject, pyqtSignal

class TableWidget(QTableWidget):
    """Custom TableWidget for displaying OCR extracted table data."""
    
    def __init__(self, parent=None):
        """Initialize the table widget with default styling and settings."""
        super().__init__(parent)
        
        # Configure appearance
        self.setStyleSheet("QTableWidget { border: 1px solid lightgrey; }")
        
        # Initial empty table setup
        self.setRowCount(0)
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels([f"Column {i+1}" for i in range(4)])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    
    def display_data(self, header, data):
        """Display OCR results in the table."""
        # Clear existing data
        self.clear()
        self.setRowCount(0)
        self.setColumnCount(0)
        
        # Handle empty data case
        if not data and not header:
            self.setup_empty_table()
            return
            
        # Set dimensions based on data
        num_rows = len(data)
        num_cols = len(header) if header else (len(data[0]) if data else 4)
        
        self.setRowCount(num_rows)
        self.setColumnCount(num_cols)
        
        # Set header if available, otherwise use default
        if header:
            self.setHorizontalHeaderLabels(header)
        else:
            self.setHorizontalHeaderLabels([f"Column {i+1}" for i in range(num_cols)])
        
        # Populate data cells
        for row_idx, row_data in enumerate(data):
            # Normalize row length to match column count
            current_cols = len(row_data)
            if current_cols < num_cols:
                row_data.extend([""] * (num_cols - current_cols))
            elif current_cols > num_cols:
                row_data = row_data[:num_cols]
            
            # Set cell items
            for col_idx, cell_data in enumerate(row_data):
                self.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))
        
        # Adjust column widths and row heights
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    
    def clear_table(self):
        """Clear all table contents and reset dimensions."""
        self.clear()
        self.setRowCount(0)
        self.setColumnCount(0)
    
    def setup_empty_table(self):
        """Set up an empty table with default headers."""
        num_cols = 4
        self.setColumnCount(num_cols)
        self.setHorizontalHeaderLabels([f"Column {i+1}" for i in range(num_cols)])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) 