# Water-Level-Detection-With-CCTV

This project is a **Water Level Monitoring System** that:
- Captures real-time video streams from an IP camera.
- Detects water levels based on color detection and image processing.
- Displays the video stream with the detected water level in a web-based dashboard using **Flask**.
- Stores the water level data to **InfluxDB** every 5 minutes.

---

## Features

- **Real-time Video Stream**: View live video streams from the IP camera.
- **Water Level Detection**: Detects the water level by detecting yellow markers.
- **Responsive Dashboard**: Display the stream and water level information on a web dashboard with **Bootstrap**.
- **InfluxDB Storage**: Periodically writes water level data to InfluxDB every 5 minutes.
- **Waitress Server**: Runs the Flask app with production-grade performance using **Waitress**.
- **Environment Variables**: Uses `.env` file for secure storage of sensitive information.

---

## Technologies Used

- **Python**: Backend logic and data processing.
- **Flask**: Web framework to serve the dashboard and video feed.
- **OpenCV**: Image processing for water level detection.
- **InfluxDB**: Time-series database for storing water level data.
- **Bootstrap**: Frontend styling for a responsive dashboard.
- **Waitress**: Production-grade WSGI server.
- **Dotenv**: To manage environment variables.

---

## Prerequisites

1. **Python 3.x** installed on your system.
2. **InfluxDB** installed and running (local or remote instance).
3. **IP Camera** accessible via RTSP URL.
4. **Pipenv** or **virtualenv** (optional for dependency management).

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <this-repository-url>
   cd water-level-monitoring
   ```

2. **Create a Virtual Environment** (Optional):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/Mac
   venv\Scripts\activate     # On Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` File**:
   Create a `.env` file in the project directory with the following content:

   ```plaintext
   INFLUXDB_URL=your_influxdb_url
   INFLUXDB_TOKEN=your_influxdb_token
   INFLUXDB_ORG=your_org
   INFLUXDB_BUCKET=your_bucket
   CAMERA_USERNAME=your_camera_username
   CAMERA_PWD=your_camera_password
   CAMERA_IP=your_camera_ip
   ```

---

## Usage

1. **Run the Flask App with Waitress**:
   ```bash
   python app.py
   ```

2. **Access the Dashboard**:
   Open your web browser and go to:
   ```
   http://localhost:5000
   ```

3. **InfluxDB Monitoring**:
   - Water level data will be stored in InfluxDB every 5 minutes.
   - You can view the data using the InfluxDB UI or query it using Flux queries.

---

## Project Structure

```
water-level-monitoring/
│
├── templates/
│   └── index.html         # Dashboard HTML file
├── app.py                 # Main Python script
├── .env                   # Environment variables (not committed)
└── README.md              # This README file
```

---

## Dependencies

The following packages are required (included in `requirements.txt`):

```plaintext
flask
opencv-python
numpy
influxdb-client
waitress
python-dotenv
```

---

## How It Works

1. **Water Level Detection**:
   - The video stream is captured from the IP camera using **OpenCV**.
   - A specific yellow region is detected within the defined `x_start` and `x_end` coordinates.
   - The y-coordinate of the yellow region is mapped to a water level using predefined mappings.

2. **Data Storage in InfluxDB**:
   - The water level is written to InfluxDB every 5 minutes using the **InfluxDB Python Client**.
   - Only detected water levels are written (skipping if the water level is not detected).

3. **Web Dashboard**:
   - The Flask app serves a web dashboard that displays the live video stream with the detected water level.
   - The Waitress server is used to run the Flask app in a production-ready environment.

---

## Troubleshooting

- **RTSP Stream Not Working**:
  - Ensure the IP camera is accessible from the machine running the Flask app.
  - Check if the camera credentials in the `.env` file are correct.

- **InfluxDB Connection Error**:
  - Verify the InfluxDB URL, token, organization, and bucket in the `.env` file.
  - Make sure InfluxDB is running and accessible.

- **Performance Issues**:
  - Lower the frame resolution in `app.py` by adjusting:
    ```python
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    ```

---

## Future Improvements

- **Add Historical Data Charts**: Display historical water levels using **Chart.js**.
- **Add Alerts**: Trigger alerts for abnormal water levels using email or SMS.
- **Use WebSockets**: For real-time updates instead of MJPEG streaming.
- **Improve Detection Accuracy**: Enhance the image processing logic for more accurate water level detection.

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

---

## Acknowledgments

- **InfluxDB** for the time-series database.
- **OpenCV** for real-time video stream processing.
- **Flask** for the web framework.
- **Bootstrap** for the responsive UI styling.

---

Feel free to reach out if you have any questions or need further assistance. Enjoy monitoring your water levels in real time! 🚀
