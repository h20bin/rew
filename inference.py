import argparse
import signal
import socketserver
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import cv2


latest_frames = {}
running = True


class StreamHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        parts = self.path.strip("/").split("/")
        if len(parts) != 2 or parts[0] != "stream":
            self.send_error(404)
            return

        cam_id = parts[1]
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        while running:
            frame = latest_frames.get(cam_id)
            if not frame:
                time.sleep(0.05)
                continue
            try:
                self.wfile.write(
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                break
            time.sleep(0.05)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def parse_camera(value):
    if "=" not in value:
        raise argparse.ArgumentTypeError("camera must be CAM-ID=/dev/videoN or CAM-ID=N")
    cam_id, device = value.split("=", 1)
    cam_id = cam_id.strip()
    device = device.strip()
    if device.isdigit():
        device = int(device)
    if not cam_id:
        raise argparse.ArgumentTypeError("camera id is empty")
    return cam_id, device


def start_stream_server(host, port):
    server = ThreadedHTTPServer((host, port), StreamHandler)
    print(f"[stream] http://{host}:{port}/stream/{{camera_id}}")
    server.serve_forever()


def webcam_loop(device, cam_id, width, height, fps, jpeg_quality):
    global running
    print(f"[{cam_id}] open camera: {device}")

    while running:
        cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)

        if not cap.isOpened():
            print(f"[{cam_id}] camera open failed: {device}; retry in 2s")
            time.sleep(2)
            continue

        while running:
            ok, frame = cap.read()
            if not ok:
                print(f"[{cam_id}] frame read failed; reconnect")
                break

            cv2.putText(frame, cam_id, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
            if ok:
                latest_frames[cam_id] = jpeg.tobytes()
            time.sleep(max(0.001, 1 / fps))

        cap.release()
        time.sleep(0.5)


def shutdown(*_):
    global running
    running = False
    print("\n[stream] shutdown requested")


def main():
    parser = argparse.ArgumentParser(description="Raspberry Pi webcam MJPEG streaming server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--camera", action="append", type=parse_camera, default=None,
                        help="camera mapping. example: --camera CAM-001=0 --camera CAM-002=2")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--jpeg-quality", type=int, default=75)
    args = parser.parse_args()

    cameras = args.camera or [("CAM-001", 0)]

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    threading.Thread(target=start_stream_server, args=(args.host, args.port), daemon=True).start()

    for cam_id, device in cameras:
        threading.Thread(
            target=webcam_loop,
            args=(device, cam_id, args.width, args.height, args.fps, args.jpeg_quality),
            daemon=True,
        ).start()
        print(f"[{cam_id}] stream URL: http://<raspberry-pi-ip>:{args.port}/stream/{cam_id}")

    print("[stream] running. press Ctrl+C to stop.")
    while running:
        time.sleep(1)


if __name__ == "__main__":
    main()
