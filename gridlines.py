from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtWidgets import QWidget

class LineEndpoint:
    def __init__(self, x, y, radius=7):
        self.x = x
        self.y = y
        self.radius = radius
        
    def contains(self, point):
        return (point.x() - self.x)**2 + (point.y() - self.y)**2 <= self.radius**2
        
    def set_pos(self, x, y):
        self.x = x
        self.y = y

class Cell:
    def __init__(self, top_left, top_right, bottom_left, bottom_right):
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.bottom_right = bottom_right
        
    def get_vertices(self):
        return [self.top_left, self.top_right, self.bottom_right, self.bottom_left]

class Line:
    def __init__(self, start: LineEndpoint, end: LineEndpoint):
        self.start = start
        self.end = end
        self.intersections: list[int, int] = list()
        self.cells: list[Cell] = []  # Store the calculated cells here

class CustomLineWidget(QWidget):
    cell_selected = pyqtSignal(int, int)  # Signal to emit row and column of selected cell
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.scaled_pixmap = None
        self.horizontal_lines = []  # List of Line objects
        self.vertical_lines = []    # List of Line objects
        self.dragging_endpoint = None
        self.is_locked = False
        self.setMouseTracking(True)
        self.highlighted_cell = None  # Store the currently highlighted cell
        
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
        
    def draw_intersection_points(self, painter):
        """Draw circles at all intersection points in green."""
        if not self.is_locked:
            return
            
        # Set up green pen for intersection points
        pen = QPen(QColor(0, 255, 0))  # Green color
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw intersection points for each horizontal line
        for line in self.horizontal_lines:
            for x, y in line.intersections:
                painter.drawEllipse(QPoint(x, y), 5, 5)  # Radius of 5 pixels

    def draw_cells(self, painter):
        """Draw all cells in blue."""
        if not self.is_locked:
            return
            
        # Set up blue pen for cells
        pen = QPen(QColor(0, 0, 255))  # Blue color
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Draw cells for each horizontal line
        for line in self.horizontal_lines:
            for cell in line.cells:
                # Draw the four sides of the cell
                painter.drawLine(
                    QPoint(cell.top_left[0], cell.top_left[1]),
                    QPoint(cell.top_right[0], cell.top_right[1])
                )
                painter.drawLine(
                    QPoint(cell.top_right[0], cell.top_right[1]),
                    QPoint(cell.bottom_right[0], cell.bottom_right[1])
                )
                painter.drawLine(
                    QPoint(cell.bottom_right[0], cell.bottom_right[1]),
                    QPoint(cell.bottom_left[0], cell.bottom_left[1])
                )
                painter.drawLine(
                    QPoint(cell.bottom_left[0], cell.bottom_left[1]),
                    QPoint(cell.top_left[0], cell.top_left[1])
                )

    def highlight_cell(self, row, col):
        """Highlight a specific cell in the grid."""
        self.highlighted_cell = (row, col)
        self.update()  # Trigger a repaint

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

            # Draw highlighted cell if one is selected
            if self.highlighted_cell and self.is_locked:
                row, col = self.highlighted_cell
                if row < len(self.horizontal_lines) - 1 and col < len(self.vertical_lines) - 1:
                    # Get cell boundaries
                    top = self.horizontal_lines[row].start.y
                    bottom = self.horizontal_lines[row + 1].start.y
                    left = self.vertical_lines[col].start.x
                    right = self.vertical_lines[col + 1].start.x
                    
                    # Draw highlighted cell with semi-transparent yellow
                    pen.setColor(QColor(255, 255, 0, 128))  # Semi-transparent yellow
                    painter.setPen(pen)
                    painter.setBrush(QColor(255, 255, 0, 64))  # More transparent yellow for fill
                    painter.drawRect(left, top, right - left, bottom - top)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_locked:
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
            else:
                # If lines are locked, check for cell selection
                x, y = event.position().x(), event.position().y()
                
                # Find the cell that contains the click
                for row in range(len(self.horizontal_lines) - 1):
                    top = self.horizontal_lines[row].start.y
                    bottom = self.horizontal_lines[row + 1].start.y
                    
                    for col in range(len(self.vertical_lines) - 1):
                        left = self.vertical_lines[col].start.x
                        right = self.vertical_lines[col + 1].start.x
                        
                        if (left <= x <= right) and (top <= y <= bottom):
                            self.cell_selected.emit(row, col)
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
        
    def calculate_intersections(self):
        """Calculate intersection points between horizontal and vertical lines using general line intersection formula."""
        for h_line in self.horizontal_lines:
            h_line.intersections.clear()  # Clear any existing intersections
            for v_line in self.vertical_lines:
                # Get line segment endpoints
                x1, y1 = h_line.start.x, h_line.start.y
                x2, y2 = h_line.end.x, h_line.end.y
                x3, y3 = v_line.start.x, v_line.start.y
                x4, y4 = v_line.end.x, v_line.end.y
                
                # Calculate denominator for intersection formula
                denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
                
                # Check if lines are parallel (denominator = 0)
                if abs(denominator) < 1e-10:  # Using small epsilon for floating point comparison
                    continue
                
                # Calculate intersection point using line intersection formula
                t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denominator
                u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denominator
                
                # Check if intersection point is within both line segments (0 <= t <= 1 and 0 <= u <= 1)
                if 0 <= t <= 1 and 0 <= u <= 1:
                    # Calculate actual intersection point
                    x = x1 + t * (x2 - x1)
                    y = y1 + t * (y2 - y1)
                    h_line.intersections.append([int(x), int(y)])

    def calculate_cells(self):
        """Calculate all cells in the grid from the intersections."""
        self.cells = []
        
        # Sort intersections for each horizontal line by x-coordinate
        for h_line in self.horizontal_lines:
            h_line.intersections.sort(key=lambda p: p[0])
        
        # For each pair of consecutive horizontal lines
        for i in range(len(self.horizontal_lines) - 1):
            top_line = self.horizontal_lines[i]
            bottom_line = self.horizontal_lines[i + 1]
            
            # For each pair of consecutive intersections
            for j in range(len(top_line.intersections) - 1):
                # Get the four corners of the cell
                top_left = top_line.intersections[j]
                top_right = top_line.intersections[j + 1]
                
                # Find corresponding points on bottom line
                bottom_left = None
                bottom_right = None
                
                # Find the closest intersections on the bottom line
                for k in range(len(bottom_line.intersections)):
                    if bottom_line.intersections[k][0] >= top_left[0]:
                        bottom_left = bottom_line.intersections[k]
                        if k + 1 < len(bottom_line.intersections):
                            bottom_right = bottom_line.intersections[k + 1]
                        break
                
                # Only create cell if we found all four corners
                if bottom_left and bottom_right:
                    cell = Cell(
                        top_left=top_left,
                        top_right=top_right,
                        bottom_left=bottom_left,
                        bottom_right=bottom_right
                    )
                    top_line.cells.append(cell)

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.calculate_intersections()
            self.calculate_cells()
        return self.is_locked, self.horizontal_lines, self.vertical_lines 