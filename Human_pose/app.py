import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import cv2
import mediapipe as mp
import platform
import subprocess

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Ensure upload and output folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Route to upload and process image
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            output_path = process_image(filepath, filename)
            return redirect(url_for('uploaded_file', filename=filename))
    return render_template('upload.html')

# Route to display the processed image
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

# Function to process the image and save the output
def process_image(filepath, filename):
    # Initialize MediaPipe Pose
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    # Load the image
    image = cv2.imread(filepath)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Process the image to detect poses
    results = pose.process(image_rgb)

    # Draw the pose annotation on the image
    mp_drawing = mp.solutions.drawing_utils
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)
        )

    # Save the output image with pose landmarks
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    cv2.imwrite(output_path, image)

    # Release resources
    pose.close()
    
    return output_path

# Function to open file based on OS
def open_file(filepath):
    if platform.system() == 'Windows':
        os.startfile(filepath)
    elif platform.system() == 'Darwin':  # macOS
        subprocess.call(('open', filepath))
    else:  # Linux
        subprocess.call(['xdg-open', filepath])

# HTML template for file upload (save this as 'templates/upload.html')
"""
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Image for Pose Estimation</title>
</head>
<body>
    <h1>Upload Image for Pose Estimation</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
</body>
</html>
"""

# Run the Flask app
if __name__ == '__main__':
    # Listen on all IP addresses (0.0.0.0) to make the app accessible from other devices
    app.run(host='0.0.0.0', port=5000, debug=True)
