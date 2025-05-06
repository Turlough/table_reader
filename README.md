# Handwritten Table OCR Application

This project contains tools for OCR processing of handwritten tables and perspective correction of document images.

## Page Perspective Correction

The `page_perspective_app.py` application allows you to correct perspective distortion in images of documents. 

### Features:
- Load any image file
- Draw a quadrilateral on the image by dragging the corners to match the boundaries of the document
- Transform the image to correct perspective, creating a rectangular output
- Save the corrected image with "_cropped" suffix

### Usage:
1. Run the application: `python page_perspective_app.py`
2. Click "Load Image" to select an image file
3. Drag the blue corner points to align with the document edges
4. Click "Reshape" to process and save the corrected image

## Requirements

See `requirements.txt` for dependencies. Install them using:

```
pip install -r requirements.txt
```

## Table OCR Application

The existing `table_ocr_app.py` provides OCR functionality for handwritten tables.

### Features:
- Load and display images
- Perform OCR on handwritten tables
- Display extracted data in a structured format

### Usage:
```
python table_ocr_app.py
```

# Table Reader
This is a PyQt6 application that allows the user to load an image containing a table and read its contents into table format.

The image may be a photo, in which case the user can normalise the image (i.e. make it rectangular again) by drawing a quadrilateral boundary within the image showing the outline of the page as it appears in the photo. 
Once drawn, the image is reshaped to a rectangle.

When the image is ready, they may click the OCR button to read the contents into a table.

The image and control buttons are on the left panel; the OCR results are in the right panel.

## Challenges
Images may be photographs, and may contain perspective distortion.

## Suggested Improvements:
- Implement proper threading for OCR processing to prevent UI freezing
- Add error handling for missing Google credentials
- Implement the placeholder features (straighten, crop)
- Add image preprocessing to improve OCR accuracy
- Implement adaptive column detection instead of assuming 4 columns
- Add caching for processed images to avoid redundant API calls
- Improve the table detection algorithm with more robust heuristics
- Add export functionality for the extracted table data