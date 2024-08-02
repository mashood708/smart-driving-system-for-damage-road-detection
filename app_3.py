from flask import Flask, render_template, request, redirect, url_for, session, flash, Response,send_from_directory, abort,send_file
import scrypt
import cv2
import math
from datetime import datetime
from ultralytics import YOLO  # YOLOv8 model for object detection
import mysql.connector  # Library for MySQL database interaction
import os
import io
import zipfile
import boto3  # AWS SDK for Python
from botocore.exceptions import NoCredentialsError
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.secret_key = os.urandom(24)

# S3 bucket configuration (replace with your own credentials)
S3_BUCKET_NAME= 'my-image-and'
S3_REGION = 'us-east-1'
S3_ACCESS_KEY = 'AKIA3FLD4WNIFL56KAHV'
S3_SECRET_KEY = 'Xv4cpDgUlzE4gro40CMaZR2AfVyKk956VODrWSKh'
# Initialize S3 client
# S3 bucket configuration (replace with your own credentials)
s3_client = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)


# Load YOLO model and define class names
model = YOLO("yolov8n_custome_model.pt")  # YOLO model for object detection
classNames = ["Potholes", "object", "pothole", "potholes"]  # Class names for detected objects

# Database configuration
db_config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'a'  # Ensure the database name is correct
}

# ThreadPool for concurrent operations
executor = ThreadPoolExecutor(max_workers=4)

# Function to hash passwords
def hash_password(password):
    salt = os.urandom(16)
    hashed_password = scrypt.hash(password.encode('utf-8'), salt)
    return salt + hashed_password

# Function to verify passwords
def verify_password(stored_password, provided_password):
    salt = stored_password[:16]
    stored_hash = stored_password[16:]
    salt = bytes(salt)
    provided_hash = scrypt.hash(provided_password.encode('utf-8'), salt)
    return stored_hash == provided_hash

# Flag to control object detection
detect_objects_flag = False

# Function to perform object detection on a frame
# Assuming classNames and model are defined elsewhere in your code

def detect_objects(frame):
    global classNames
    
    # Getting current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Getting current date for folder name
    folder_name = datetime.now().strftime("%Y-%m-%d")
    
    # Doing detections using YOLOv8
    results = model(frame, stream=True)
    
    detected = False  # Flag to check if any object is detected in the frame
    
    # Initialize an empty list to store the detected objects' coordinates
    detected_objects = []
    
    for r in results:
        boxes = r.boxes
        for box in boxes:
            # Calculate the confidence score and ensure it's at least 0.40
            conf = math.ceil((box.conf[0] * 100)) / 100
            if conf >= 0.40:
                detected = True  # Set detected flag to True if an object is detected
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)  # Draw bounding box
                cls = int(box.cls[0])
                class_name = classNames[cls]
            
                label = f'{class_name} {conf}'
                
                # Append the coordinates to the detected_objects list
                detected_objects.append((label, (x1, y1), (x2, y2)))
                
                t_size = cv2.getTextSize(label, 0, fontScale=1, thickness=2)[0]
                c2 = x1 + t_size[0], y1 - t_size[1] - 3
                cv2.rectangle(frame, (x1, y1), c2, [255, 0, 255], -1, cv2.LINE_AA)  
                cv2.putText(frame, label, (x1, y1 - 2), 0, 1, [255, 255, 255], thickness=1, lineType=cv2.LINE_AA)
    
    # Save the image with bounding boxes only if an object is detected
    if detected:
        executor.submit(save_data, frame, detected_objects, timestamp, folder_name)
    
    return frame
# Function to save data (locally or to S3)
def save_data(frame, detected_objects, timestamp, folder_name):
    # Convert image to bytes
    _, buffer = cv2.imencode('.jpg', frame)
    image_bytes = io.BytesIO(buffer)
    
    # Write the coordinates to a string
    label_str = ""
    for obj in detected_objects:
        label, (x1, y1), (x2, y2) = obj
        label_str += f"{label}: ({x1}, {y1}), ({x2}, {y2})\n"
    
    # Convert string to bytes
    label_bytes = io.BytesIO(label_str.encode())
    
    if is_s3_available():
        try:
            # Upload image to S3
            s3_client.upload_fileobj(image_bytes, S3_BUCKET_NAME, f"{folder_name}/detected_image_{timestamp}.jpg")
            # Upload text file to S3
            s3_client.upload_fileobj(label_bytes, S3_BUCKET_NAME, f"{folder_name}/detected_labels_{timestamp}.txt")
        except Exception as e:
            print(f"Error uploading to S3: {e}")
            save_locally(frame, detected_objects, timestamp, folder_name)
    else:
        save_locally(frame, detected_objects, timestamp, folder_name)
        print("AWS is not available")

# Function to check if S3 is available
def is_s3_available():
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        return True
    except NoCredentialsError:
        return False
    except Exception as e:
        print(f"Error checking S3 availability: {e}")
        return False

# Function to save data locally
def save_locally(frame, detected_objects, timestamp, folder_name):
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # Save the image to the folder
    cv2.imwrite(os.path.join(folder_name, f"detected_image_{timestamp}.jpg"), frame)
    
    # Write the coordinates to the .txt file
    with open(os.path.join(folder_name, f"detected_labels_{timestamp}.txt"), "w") as file:
        for obj in detected_objects:
            label, (x1, y1), (x2, y2) = obj
            file.write(f"{label}: ({x1}, {y1}), ({x2}, {y2})\n")

# Generator function to generate video frames
def gen_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
        
            break
        else: 
            if detect_objects_flag:  # Start object detection if flag is True
                frame = detect_objects(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Default route
@app.route('/')
def index():
    return redirect(url_for('index'))

# Route for signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_password = hash_password(password)

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()['count']

            role_name = 'Admin' if user_count == 0 else 'User'
            cursor.execute("SELECT RoleID FROM roles WHERE RoleName = %s", (role_name,))
            role_id = cursor.fetchone()['RoleID']

            cursor.execute("INSERT INTO users (Username, Password) VALUES (%s, %s)", (username, hashed_password))
            user_id = cursor.lastrowid

            cursor.execute("INSERT INTO user_roles (UserID, RoleID) VALUES (%s, %s)", (user_id, role_id))

            conn.commit()
            cursor.close()
            conn.close()

            flash('Signup successful! You can now login.', 'success')
            return redirect(url_for('index'))
        except mysql.connector.Error as err:
            flash(f"Error signing up: {err}", 'danger')

    return render_template('signup.html')

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            user_query = """
                SELECT u.Password, u.UserID, r.RoleName 
                FROM users u 
                JOIN user_roles ur ON u.UserID = ur.UserID 
                JOIN roles r ON ur.RoleID = r.RoleID 
                WHERE u.Username = %s
            """
            cursor.execute(user_query, (username,))
            users = cursor.fetchall()
            cursor.close()
            conn.close()

            if users:
                user = users[0]
                if verify_password(user['Password'], password):
                    session['username'] = username
                    session['role'] = user['RoleName']
                    if user['RoleName'] == 'Admin':
                        return redirect(url_for('Admin_Dashboard'))
                    else:
                        return redirect(url_for('user_home'))
            flash('Invalid username or password', 'danger')
        except mysql.connector.Error as err:
            flash(f"Error logging in: {err}", 'danger')

    return render_template('index.html')
# Route for forgot password
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']
        
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM users WHERE Username = %s", (username,))
            user = cursor.fetchone()

            if user:
                hashed_password = hash_password(new_password)
                cursor.execute("UPDATE users SET Password = %s WHERE UserID = %s", (hashed_password, user['UserID']))
                conn.commit()

                flash('Password updated successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Username not found.', 'danger')

            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            flash(f"Error updating password: {err}", 'danger')

    return render_template('forgot_password.html')



# Route for admin home
@app.route('/Admin_Dashboard')
def Admin_Dashboard():
    if 'username' in session and session['role'] == 'Admin':
        return render_template('Admin_Dashboard.html', username=session['username'])
    else:
        return redirect(url_for('omfrc'))

# Route for user home
@app.route('/user_home')
def user_home():
    if 'username' in session and session['role'] == 'User':
        return render_template('User_Home.html', username=session['username'])
    else:
        return redirect(url_for('login'))

# Route for logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

# Additional routes for user management
@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role_name = request.form['role_name']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            hashed_password = hash_password(password)
            cursor.execute("INSERT INTO users (Username, Password) VALUES (%s, %s)", (username, hashed_password))
            user_id = cursor.lastrowid

            cursor.execute("SELECT RoleID FROM roles WHERE RoleName = %s", (role_name,))
            role = cursor.fetchone()
            if not role:
                cursor.execute("INSERT INTO roles (RoleName) VALUES (%s)", (role_name,))
                role_id = cursor.lastrowid
            else:
                role_id = role['RoleID']

            cursor.execute("INSERT INTO user_roles (UserID, RoleID) VALUES (%s, %s)", (user_id, role_id))

            conn.commit()
            cursor.close()
            conn.close()

            flash('User created successfully', 'success')
            return redirect(url_for('user_list'))
        except mysql.connector.Error as err:
            flash(f"Error creating user: {err}", 'danger')
            return redirect(url_for('create_user'))
    else:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM roles")
        roles = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('create_user.html', roles=roles)

@app.route('/user_list')
def user_list():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    users_query = """
        SELECT users.UserID, users.Username, roles.RoleName 
        FROM users 
        JOIN user_roles ON users.UserID = user_roles.UserID 
        JOIN roles ON user_roles.RoleID = roles.RoleID
    """
    cursor.execute(users_query)
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('user_list.html', users=users)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM user_roles WHERE UserID = %s", (user_id,))
        cursor.execute("DELETE FROM users WHERE UserID = %s", (user_id,))

        conn.commit()
        cursor.close()
        conn.close()

        flash('User deleted successfully', 'success')
    except mysql.connector.Error as err:
        flash(f"Error deleting user: {err}", 'danger')
    return redirect(url_for('user_list'))

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role_name = request.form['role_name']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            hashed_password = hash_password(password)
            cursor.execute("UPDATE users SET Username = %s, Password = %s WHERE UserID = %s", (username, hashed_password, user_id))

            cursor.execute("SELECT RoleID FROM roles WHERE RoleName = %s", (role_name,))
            role = cursor.fetchone()
            if not role:
                cursor.execute("INSERT INTO roles (RoleName) VALUES (%s)", (role_name,))
                role_id = cursor.lastrowid
            else:
                role_id = role['RoleID']

            cursor.execute("UPDATE user_roles SET RoleID = %s WHERE UserID = %s", (role_id, user_id))

            conn.commit()
            cursor.close()
            conn.close()

            flash('User updated successfully', 'success')
            return redirect(url_for('user_list'))
        except mysql.connector.Error as err:
            flash(f"Error updating user: {err}", 'danger')
            return redirect(url_for('edit_user', user_id=user_id))
    else:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE UserID = %s", (user_id,))
        user = cursor.fetchone()

        cursor.execute("SELECT * FROM roles")
        roles = cursor.fetchall()

        cursor.execute("SELECT RoleID FROM user_roles WHERE UserID = %s", (user_id,))
        user_role = cursor.fetchone()

        cursor.close()
        conn.close()

        return render_template('edit_user.html', user=user, roles=roles, user_role=user_role)

# Route to start object detection
@app.route('/start_detection')
def start_detection():
    global detect_objects_flag
    detect_objects_flag = True
    return "Object detection started."

# Route to stop object detection
@app.route('/stop_detection')
def stop_detection():
    global detect_objects_flag
    detect_objects_flag = False
    return "Object detection stopped."

# Route for video feed
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
# Route to list folders in S3 bucket
@app.route('/s3_list_folders')
def s3_list_folders():
    folders = []
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Delimiter='/')
    for prefix in response.get('CommonPrefixes', []):
        folders.append(prefix.get('Prefix'))
    return render_template('s3_folders.html', folders=folders)

# Route to list files in a specific folder in S3 bucket
@app.route('/s3_list_files/<path:folder_name>', methods=['GET', 'POST'])
def s3_list_files(folder_name):
    files = []
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=folder_name)
    for obj in response.get('Contents', []):
        files.append(obj.get('Key'))
    return render_template('s3_files.html', folder_name=folder_name, files=files)

# Route to view text content of a file
@app.route('/view_text/<path:file_key>')
def view_text(file_key):
    try:
        obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=file_key)
        text = obj['Body'].read().decode('utf-8')
        return render_template('view_text.html', file_key=file_key, text=text)
    except Exception as e:
        print(f"Error retrieving text file from S3: {e}")
        abort(404)

# Route to view image content of a file
@app.route('/view_image/<path:file_key>')
def view_image(file_key):
    try:
        # Generate a presigned URL for the image object in S3
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': file_key},
            ExpiresIn=3600  # Expires in 1 hour
        )
        return render_template('view_image.html', presigned_url=presigned_url)
    except Exception as e:
        print(f"Error generating presigned URL for image: {e}")
        abort(404)

# Route to handle file download
@app.route('/download_files', methods=['POST'])
def download_files():
    selected_files = request.form.getlist('selected_files')
    folder_name = request.form.get('folder_name')

    # Set to store unique file keys
    files_to_download = set()

    # Add selected files to the set
    for selected_file in selected_files:
        files_to_download.add(selected_file)

        # Add corresponding text files for selected images and vice versa
        if selected_file.endswith(('.jpg', '.jpeg', '.png')):
            corresponding_text_file = selected_file.replace('detected_image', 'detected_labels').rsplit('.', 1)[0] + '.txt'
            response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=corresponding_text_file)
            if 'Contents' in response and len(response['Contents']) > 0:
                files_to_download.add(corresponding_text_file)
        elif selected_file.endswith('.txt'):
            corresponding_image_file = selected_file.replace('detected_labels', 'detected_image').rsplit('.', 1)[0] + '.jpg'
            if not s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=corresponding_image_file):
                corresponding_image_file = selected_file.replace('detected_labels', 'detected_image').rsplit('.', 1)[0] + '.jpeg'
            if not s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=corresponding_image_file):
                corresponding_image_file = selected_file.replace('detected_labels', 'detected_image').rsplit('.', 1)[0] + '.png'
            response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=corresponding_image_file)
            if 'Contents' in response and len(response['Contents']) > 0:
                files_to_download.add(corresponding_image_file)

    # Create a zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_key in files_to_download:
            try:
                obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=file_key)
                zip_file.writestr(file_key, obj['Body'].read())
            except Exception as e:
                print(f"Error adding file to zip: {e}")

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='Historical_Data.zip')

# Route to handle folder download
@app.route('/download_folders', methods=['POST'])
def download_folders():
    selected_folders = request.form.getlist('selected_folders')

    # Create a zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for folder in selected_folders:
            response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=folder)
            for obj in response.get('Contents', []):
                try:
                    file_key = obj.get('Key')
                    obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=file_key)
                    zip_file.writestr(file_key, obj['Body'].read())
                except Exception as e:
                    print(f"Error adding file to zip: {e}")

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='selected_folders.zip')



if __name__ == '__main__':
    app.run(debug=True,port=8000)
     

