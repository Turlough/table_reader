# Table Reader
This is a PyQt6 application that allows the user to load an image containing a table and read its contents into table format.

The image may be a photo, in which case the user can normalise the image (i.e. make it rectangular again) by drawing a quadrilateral boundary within the image showing the outline of the page as it appears in the photo. 
Once drawn, the image is reshaped to a rectangle.

When the image is ready, they may click the OCR button to read the contents into a table.

The image and control buttons are on the left panel; the OCR results are in the right panel.

## Suggested Improvements:
- Implement proper threading for OCR processing to prevent UI freezing
- Add error handling for missing Google credentials
- Implement the placeholder features (straighten, crop)
- Add image preprocessing to improve OCR accuracy
- Implement adaptive column detection instead of assuming 4 columns
- Add caching for processed images to avoid redundant API calls
- Improve the table detection algorithm with more robust heuristics
- Add export functionality for the extracted table data