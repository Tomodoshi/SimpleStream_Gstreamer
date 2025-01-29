from flask import Flask, jsonify, request, render_template, Response, request, redirect, url_for
from flask_restful import Api
import threading
import cv2 as cv

app = Flask(__name__)

RTSP_URL = "rtsp://0.0.0.0:8559/test"

stop_event = threading.Event()
streaming = False
frame_lock = threading.Lock()
current_frame = None


def refresh():
    # Redirecting to the same route to refresh the page
    return redirect(url_for(request.endpoint))

def generate_frames():
    # Open the RTSP stream
    cap = cv.VideoCapture(RTSP_URL)

    if not cap.isOpened():
        print("Error: Unable to open RTSP stream.")
        return

    while not stop_event.is_set():
        success, frame = cap.read()
        if not success:
            print("Error: Unable to read frame.")
            break

        with frame_lock:
            current_frame = frame

        # Encode frame as JPEG
        ret, buffer = cv.imencode('.jpg', frame)
        if not ret:
            print("Error: Unable to encode frame.")
            continue

        # Convert buffer to byte data for streaming
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
    
def generate_frames_thread():
    global current_frame
    cap = cv.VideoCapture(RTSP_URL)

    if not cap.isOpened():
        print("Error: Unable to open RTSP stream.")
        return

    while not stop_event.is_set():
        success, frame = cap.read()
        if not success:
            print("Error: Unable to read frame.")
            break

        with frame_lock:
            current_frame = frame  # Save the latest frame for `/video`

    cap.release()
    print("Stream stopped.")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    """Serve the video stream to the client."""
    def stream_frames():
        global current_frame
        while streaming:
            with frame_lock:
                if current_frame is None:
                    continue
                ret, buffer = cv.imencode('.jpg', current_frame)
                if not ret:
                    continue
                frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    if streaming:
        return Response(stream_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return jsonify({"status": "Stream is stopped"}), 400

@app.route('/start_stream', methods=['POST'])
def start_stream():
    """Start the video stream."""
    global streaming
    if not streaming:
        streaming = True
        stop_event.clear()
        
        # Start the frame generation in a separate thread
        thread = threading.Thread(target=generate_frames_thread)
        thread.daemon = True  # Ensure thread stops when the main program exits
        thread.start()
        refresh()
        return jsonify({"status": "Stream started", "refresh": True})
    else:
        return jsonify({"status": "Stream is already running"})

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    """Stop the video stream."""
    global streaming
    if streaming:
        streaming = False
        stop_event.set()
        refresh()
        return jsonify({"status": "Stream stopped", "refresh": True})
    else:
        return jsonify({"status": "Stream is already stopped"})

@app.route('/check_status', methods=['GET'])
def check_status():
    """Check the status of the video stream."""
    global streaming
    return jsonify({"status": "Running" if streaming else "Stopped"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
