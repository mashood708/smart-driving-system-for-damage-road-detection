# smart-driving-system-for-damage-road-detection
Smart Driving System for Damage Road Detection
A machine learning-based system that detects damaged road surfaces (potholes, cracks, etc.) using YOLOv8 object detection. This project aims to improve road safety by automatically identifying road defects from images or real-time camera feeds.

📌 Project Overview
Road damage poses a significant risk to drivers and vehicles. This project introduces an AI-powered solution that uses computer vision to detect road surface damage and alert relevant authorities or drivers in real time.

The system leverages YOLOv8 (You Only Look Once) for high-speed object detection and is integrated into a web-based dashboard for data visualization, image management, and user interaction.

✅ Key Features
✔ Real-Time Road Damage Detection using YOLOv8 custom-trained model
✔ Web-Based Dashboard for managing images, reports, and alerts
✔ User Authentication (Login, Signup, Forgot Password)
✔ Admin Panel for user and data management
✔ File Management System for storing detected images and text logs
✔ Responsive Design using HTML, CSS, and JavaScript

🛠 Tech Stack
Frontend:

HTML5

CSS3

JavaScript

Backend:

Python (Flask / Django)

YOLOv8 (Custom Model)

AI Model:

YOLOv8n Custom Model (yolov8n_custome_model.pt) for pothole detection

Database:

SQLite / MySQL

Other Tools:

OpenCV

Pandas

Jinja Templates

📂 Project Structure
bash
Copy
Edit
smart-driving-system-for-damage-road-detection/
│
├── .github/workflows/          # GitHub Actions workflow files
├── Admin_Dashboard.html         # Admin dashboard UI
├── User_Home.html               # User dashboard UI
├── app_3.py                     # Main backend application script
├── yolov8n_custome_model.pt     # Trained YOLOv8 model
├── requirements.txt             # Python dependencies
├── static/                      # CSS, JS, and image assets
│   ├── *.css
│   ├── script.js
├── templates/                   # HTML templates
│   ├── *.html
└── README.md                    # Project documentation
⚙️ Installation Guide
1. Clone the Repository
bash
Copy
Edit
git clone https://github.com/mashood708/smart-driving-system-for-damage-road-detection.git
cd smart-driving-system-for-damage-road-detection
2. Install Dependencies
Create a virtual environment and install requirements:

bash
Copy
Edit
python -m venv venv
source venv/bin/activate   # For Linux/Mac
venv\Scripts\activate      # For Windows

pip install -r requirements.txt
3. Add YOLOv8 Model
Ensure the custom-trained YOLOv8 model (yolov8n_custome_model.pt) is in the project root folder.

4. Run the Application
bash
Copy
Edit
python app_3.py
Access the application at:
http://127.0.0.1:5000/

🔍 How It Works
Image Upload or Camera Feed → Captures road images

YOLOv8 Detection → Identifies potholes/cracks

Dashboard Display → Shows results & logs detections

Admin Panel → Manage users, view reports, download data

📦 requirements.txt
nginx
Copy
Edit
flask
ultralytics
opencv-python
pandas
📷 Screenshots
(Add dashboard, detection result, and login page images here for better presentation)

✅ Future Enhancements
Add GPS integration to tag exact location of road damage

Deploy as Mobile App for real-time detection

Enable REST API for integration with government portals

Use Spark for large-scale image processing

📜 License
This project is licensed under the MIT License – feel free to use and modify.

