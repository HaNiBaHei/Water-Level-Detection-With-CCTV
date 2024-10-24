import cv2
import threading
import numpy as np
from queue import Queue
from flask import Flask, render_template, Response
from waitress import serve  # Import waitress
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get InfluxDB configurations from environment variables
url = os.getenv("INFLUXDB_URL")
token = os.getenv("INFLUXDB_TOKEN")
org = os.getenv("INFLUXDB_ORG")
bucket = os.getenv("INFLUXDB_BUCKET")

# Initialize Flask app
app = Flask(__name__)

# Replace these values with your camera credentials and IP
username = os.getenv("CAMERA_USERNAME")
password = os.getenv("CAMERA_PWD")
camera_ip = os.getenv("CAMERA_IP")

# Construct the RTSP URL based on the settings
video_url = f"rtsp://{username}:{password}@{camera_ip}:554/profile1"
# video_url = "http://101.109.253.60:8999"

# Initialize InfluxDB client
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Define the water level pixel mappings
original_water_level_mapping = {
    1297: 0.40,
    1120: 1.30,
    1080: 1.40,
    1045: 1.50,
    1017: 1.60,
    984: 1.70,
    950: 1.80,
    922: 1.90,
    892: 2.00,
    856: 2.10,
    822: 2.20,
    785: 2.30,
    750: 2.40,
    708: 2.50,
    670: 2.60,
    627: 2.70,
    585: 2.80,
    540: 2.90,
    495: 3.00,
    445: 3.10,
    400: 3.20,
    351: 3.30,
    304: 3.40,
    254: 3.50,
    206: 3.60,
    155: 3.70,
    105: 3.80,
    53: 3.90,
    20: 4.00,
}

# Define level offset
level_offset = -217

# Create new mapping by adjusting the key with the level_offset
water_level_mapping = {key + level_offset: value for key, value in original_water_level_mapping.items()}

# Create a shared queue to store frames
frame_queue = Queue(maxsize=10)

latest_water_level = 0.0  # Variable to store the latest water level

def draw_detected_level_line(image, y_detected, water_level):
    """Draw a horizontal line for the detected water level and display the value above it."""
    if y_detected is not None:
        # Draw the detected water level line in green
        line_color = (0, 255, 0)  # Green color

        # Draw the horizontal line across the frame
        cv2.line(image, (0, y_detected), (image.shape[1], y_detected), line_color, 2)

        # Display the water level value slightly above the line
        text_position = (10, y_detected - 10)  # 10px above the line
        cv2.putText(image, f"{water_level:.2f}m", text_position, 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)



def detect_yellow_region(image, x_start=1020, x_end=1180):
    """Detect the lowest yellow region within the specified x-axis range."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Adjusted yellow color range based on the uploaded image
    lower_yellow = np.array([25, 100, 100])  # Adjusted lower bound
    upper_yellow = np.array([90, 255, 255])  # Adjusted upper bound
    
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # Mask out the left part of the image
    mask[:, :x_start] = 0
    
    # Mask out the right part of the image
    mask[:, x_end:] = 0
    
    # Draw the vertical line at x_start
    cv2.line(image, (x_start, 0), (x_start, image.shape[0]), (255, 0, 0), 2)  # Blue line
    
    # Draw the vertical line at x_end
    cv2.line(image, (x_end, 0), (x_end, image.shape[0]), (255, 0, 0), 2)  # Green line
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        lowest_contour = max(contours, key=lambda cnt: cv2.boundingRect(cnt)[1])  # Max y-coordinate
        _, y, _, _ = cv2.boundingRect(lowest_contour)
        return y

    return None


def get_interpolated_water_level(y, water_level_mapping):
    """Map the y-coordinate to the corresponding water level using interpolation."""
    y_coords = sorted(water_level_mapping.keys())
    if y >= y_coords[0]:
        for i in range(len(y_coords) - 1):
            if y_coords[i + 1] >= y > y_coords[i]:
                level_low = water_level_mapping[y_coords[i]]
                level_high = water_level_mapping[y_coords[i + 1]]
                interpolated_level = level_low + (level_high - level_low) * (y - y_coords[i]) / (y_coords[i + 1] - y_coords[i])
                return interpolated_level
    return None

def draw_level_lines(image, water_level_mapping, y_lowest_yellow):
    """Draw horizontal lines for each water level and display the water level text."""
    for y_coord, level in water_level_mapping.items():
        # Choose the color based on whether it's above or below the detected water level
        line_color = (0, 255, 0) if y_coord <= y_lowest_yellow else (0, 0, 255)  # Green for above, red for below
        
        # Draw the horizontal line across the frame
        cv2.line(image, (0, y_coord), (image.shape[1], y_coord), line_color, 2)
        
        # Display the water level number at the same y-coordinate
        cv2.putText(image, f"{level:.2f}m", (10, y_coord - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Draw the horizontal line across the frame
        cv2.line(image, (0, y_coord), (image.shape[1], y_coord), line_color, 2)
        
        # Display the water level number at the same y-coordinate
        cv2.putText(image, f"{level:.2f}m", (10, y_coord - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


def process_frame(frame):
    """Function to process each frame and detect water level."""
    global latest_water_level
    y_lowest_yellow = detect_yellow_region(frame)

    if y_lowest_yellow is not None:
        latest_water_level = get_interpolated_water_level(y_lowest_yellow, water_level_mapping)
        draw_detected_level_line(frame, y_lowest_yellow, latest_water_level)
    else:
        # Display message if water level is not detected
        cv2.putText(frame, "Water Level: Not Detected!", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    return frame

def write_water_level_to_influxdb():
    """Write the latest water level to InfluxDB every 5 minutes."""
    time.sleep(2)
    global latest_water_level
    while True:
        # Create a point in InfluxDB format
        point = Point("water_level").tag("location", "camera_1").field("level", latest_water_level)
        
        # Write point to InfluxDB
        if(latest_water_level != 0):
            write_api.write(bucket=bucket, org=org, record=point)
        print(f"Water level {latest_water_level :.2f}m written to InfluxDB.")
        
        # Wait for 5 minutes (300 seconds)
        time.sleep(300)

def process_video_stream(video_url):
    cap = cv2.VideoCapture(video_url)

    # Set a lower resolution to improve performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    frame_skip = 1  # Process every frame
    frame_count = 0

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame_count += 1
        if frame_count % frame_skip != 0:
            continue

        processed_frame = process_frame(frame)

        # Skip queueing if the queue is full
        if frame_queue.full():
            frame_queue.get()  # Remove oldest frame
        frame_queue.put(processed_frame)

def generate_frame():
    """Generate frames from the queue for MJPEG streaming."""
    while True:
        if not frame_queue.empty():
            frame = frame_queue.get()
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]  # Reduce JPEG quality for performance
            _, buffer = cv2.imencode('.jpg', frame, encode_param)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Flask route to serve the video feed
@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(generate_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Flask route to serve the webpage
@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')

if __name__ == "__main__":
    # Start video processing in a separate thread
    video_thread = threading.Thread(target=process_video_stream, args=(video_url,))
    video_thread.daemon = True
    video_thread.start()

    # Start writing water level to InfluxDB every 5 minutes
    write_thread = threading.Thread(target=write_water_level_to_influxdb)
    write_thread.daemon = True
    write_thread.start()

    # Run Flask app with Waitress
    serve(app, host="0.0.0.0", port=5000)
