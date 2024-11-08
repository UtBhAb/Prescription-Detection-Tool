from flask import Flask, request, render_template, jsonify, redirect, url_for
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import re
import os

# Initialize Flask app
app = Flask(__name__)

# Path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Upload folder configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper function to preprocess the uploaded image
def preprocess_image(image_path):
    try:
        # Open and verify the image
        img = Image.open(image_path)
        img.verify()
        img = Image.open(image_path)
        
        # Convert to grayscale
        gray_image = img.convert('L')
        
        # Increase the contrast and sharpness
        contrast_enhancer = ImageEnhance.Contrast(gray_image)
        gray_image = contrast_enhancer.enhance(2.5)
        sharpener = ImageEnhance.Sharpness(gray_image)
        sharp_image = sharpener.enhance(3.0)

        # Apply adaptive thresholding
        numpy_image = np.array(sharp_image)
        threshold_image = cv2.adaptiveThreshold(numpy_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                cv2.THRESH_BINARY, 15, 3)
        threshold_image_pil = Image.fromarray(threshold_image)
        
        # Further noise reduction
        processed_image = threshold_image_pil.filter(ImageFilter.MedianFilter(5))

        return processed_image

    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return None

# Function to filter and extract medicine names from the OCR result
def extract_medicine_names(text):
    # Normalize text
    text = text.upper()

    # Define a whitelist of characters to include only letters, numbers, and common dosage units
    allowed_chars = re.compile(r'[A-Z0-9\s\-mgML]+')

    # Filter text to only allow valid medicine name formats (e.g., "AMOXICILLIN 500MG")
    matches = allowed_chars.findall(text)

    # Known medicine list (extend as needed)
    known_medicines = {"ASPIRIN", "IBUPROFEN", "PARACETAMOL", "AMOXICILLIN"}  # add your specific medicines here

    # Extract valid medicine names by checking against known medicines and length criteria
    medicines = [match for match in matches if (match in known_medicines or len(match) > 3)]
    
    # Sort and remove duplicates
    return sorted(set(medicines))

@app.route('/')
def index():
    return render_template('index.html')  # Serve the HTML page for the user to upload image

@app.route('/extract_text', methods=['POST'])
def extract_text():
    # Ensure the request contains an image file
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        # Save the uploaded image
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Process the image and extract text using Tesseract
        try:
            # Preprocess the image for better OCR accuracy
            processed_image = preprocess_image(file_path)
            if processed_image is None:
                return jsonify({'error': 'Failed to process the image'}), 400

            # OCR Configuration: limit output to allowed characters
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789mgML"'
            extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)

            # Extract medicine names from the OCR output
            medicines = extract_medicine_names(extracted_text)

            # Redirect to the new route to display the extracted medicine names
            return redirect(url_for('show_extracted_text', medicines=",".join(medicines)))

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Unknown error occurred'}), 500

@app.route('/show_extracted_text')
def show_extracted_text():
    # Get medicines from the query parameter and split back into a list
    medicines = request.args.get('medicines', '').split(',')
    return render_template('extracted_text.html', medicines=medicines)

if __name__ == '__main__':
    app.run(debug=True)
