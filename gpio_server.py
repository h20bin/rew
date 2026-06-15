"""
라즈베리파이에서 실행하는 GPIO 제어 서버
- Flask 기반 간단한 HTTP 서버
- 메인 서버에서 요청 받아 LED/부저 제어

실행 방법:
    pip install flask RPi.GPIO
    python gpio_server.py
"""

from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

# ── GPIO 핀 설정 ───────────────────────────────────────────
# 실제 라즈베리파이에서 실행 시 주석 해제
# import RPi.GPIO as GPIO
# GPIO.setmode(GPIO.BCM)

LED_PINS = {
    "RED":    17,  # GPIO 17
    "YELLOW": 27,  # GPIO 27
    "GREEN":  22,  # GPIO 22
}
BUZZER_PIN = 23   # GPIO 23

# GPIO 초기화 (실제 라즈베리파이에서 주석 해제)
# for pin in LED_PINS.values():
#     GPIO.setup(pin, GPIO.OUT)
#     GPIO.output(pin, GPIO.LOW)
# GPIO.setup(BUZZER_PIN, GPIO.OUT)
# GPIO.output(BUZZER_PIN, GPIO.LOW)

current_state = {"led": "OFF", "buzzer": "OFF"}
_stop_event = threading.Event()


def _blink_led(pin: int, interval: float, stop: threading.Event):
    """LED 점멸 쓰레드"""
    while not stop.is_set():
        # GPIO.output(pin, GPIO.HIGH)
        print(f"[GPIO] LED pin {pin} ON")
        time.sleep(interval)
        # GPIO.output(pin, GPIO.LOW)
        print(f"[GPIO] LED pin {pin} OFF")
        time.sleep(interval)


def _buzzer_pattern(pin: int, pattern: str, stop: threading.Event):
    """부저 패턴 쓰레드"""
    intervals = {
        "CONTINUOUS": (1.0, 0.0),
        "INTERVAL":   (0.5, 0.5),
        "URGENT":     (0.2, 0.1),
    }
    on_time, off_time = intervals.get(pattern, (1.0, 0.0))
    while not stop.is_set():
        # GPIO.output(pin, GPIO.HIGH)
        print(f"[GPIO] BUZZER ON ({pattern})")
        time.sleep(on_time)
        if off_time > 0:
            # GPIO.output(pin, GPIO.LOW)
            print(f"[GPIO] BUZZER OFF")
            time.sleep(off_time)


# ── API 엔드포인트 ─────────────────────────────────────────

@app.route("/led", methods=["POST"])
def control_led():
    global _stop_event
    data = request.get_json()
    color = data.get("color", "RED")
    pattern = data.get("pattern", "ON")

    _stop_event.set()
    _stop_event = threading.Event()

    pin = LED_PINS.get(color, LED_PINS["RED"])

    if pattern == "ON":
        # GPIO.output(pin, GPIO.HIGH)
        print(f"[GPIO] LED {color} ON")
    else:
        interval = 0.3 if pattern == "FAST_BLINK" else 0.7
        t = threading.Thread(target=_blink_led, args=(pin, interval, _stop_event))
        t.daemon = True
        t.start()

    current_state["led"] = f"{color}_{pattern}"
    return jsonify({"status": "ok", "led": current_state["led"]})


@app.route("/buzzer", methods=["POST"])
def control_buzzer():
    global _stop_event
    data = request.get_json()
    pattern = data.get("pattern", "CONTINUOUS")

    _stop_event.set()
    _stop_event = threading.Event()

    t = threading.Thread(target=_buzzer_pattern, args=(BUZZER_PIN, pattern, _stop_event))
    t.daemon = True
    t.start()

    current_state["buzzer"] = pattern
    return jsonify({"status": "ok", "buzzer": pattern})


@app.route("/stop", methods=["POST"])
def stop_all():
    global _stop_event
    _stop_event.set()
    _stop_event = threading.Event()

    # 모든 핀 OFF
    for pin in LED_PINS.values():
        # GPIO.output(pin, GPIO.LOW)
        print(f"[GPIO] LED pin {pin} OFF")
    # GPIO.output(BUZZER_PIN, GPIO.LOW)
    print("[GPIO] BUZZER OFF")

    current_state["led"] = "OFF"
    current_state["buzzer"] = "OFF"
    return jsonify({"status": "ok", "message": "모든 장치 OFF"})


@app.route("/status", methods=["GET"])
def get_status():
    return jsonify({"status": "ok", **current_state})


if __name__ == "__main__":
    print("🔌 라즈베리파이 GPIO 서버 시작 (포트 5000)")
    app.run(host="0.0.0.0", port=5000)
