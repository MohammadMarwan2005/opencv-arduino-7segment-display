# 🤖 Mechanical 7-Segment Display — Hand Tracker

A physical 7-segment display built from **7 servo motors**, controlled by an Arduino.  
A Python script reads finger counts from a webcam in real time and sends the total to the Arduino over serial, which then physically moves the servos to form the corresponding digit.

---
## 📹 Demo

<table>
  <tr>
    <th align="center">Infinite Count Mode</th>
    <th align="center">Hand Tracking → Display</th>
  </tr>
  <tr>
    <td align="center">
      <video src="https://github.com/user-attachments/assets/4ee3b811-7f8d-4137-80fa-b252f3d70b13" controls width="100%"></video>
    </td>
    <td align="center">
      <video src="https://github.com/user-attachments/assets/298a6338-722c-49cd-b35e-aac83f54e4b3" controls width="100%"></video>
    </td>
  </tr>
</table>

---

## 🔩 Hardware Components

| Component | Quantity | Purpose |
|---|---|---|
| Servo motor | 7 | One per segment (a–g) of the display |
| Arduino board | 1 | Main microcontroller, receives serial commands |
| PCA9685 PWM driver | 1 | Controls all 7 servos via I²C |
| HW-95 motor driver | 1 | Steps down / regulates 12 V supply for servos |
| 12 V battery | 1 | Power source for the servo system |
| USB cable | 1 | Serial communication between PC and Arduino |
| Jumper wires | — | Wiring everything together |

---

## 💻 Software Requirements

### Python dependencies

```bash
pip install opencv-python mediapipe pyserial
```

### Arduino library

Install via the Arduino Library Manager:

- **Adafruit PWM Servo Driver Library** (for the PCA9685)

---

## 📁 Project Structure

```
├── hands_tracker.py       # Python: webcam hand tracking + serial sender
├── arduino_skitch.ino     # Arduino: receives serial data, drives servos
└── hand_landmarker.task   # MediaPipe model file (download separately)
```

---

## ⚙️ How It Works

```
Webcam → MediaPipe (finger count) → Serial (left,right\n) → Arduino → PCA9685 → 7 Servos
```

1. **Python** captures the webcam feed, detects hands using MediaPipe, and counts raised fingers on each hand (0–5 per hand).
2. The total (`left + right`) is sent over serial every 30 ms in the format `left,right\n`.
3. **Arduino** parses the message, computes the sum, and moves the 7 servos to physically display the corresponding digit (0–9).
4. Each servo represents one segment of the display — `SEG_ON` (180°) = segment visible, `SEG_OFF` (0°) = segment hidden.

---

## 🚀 Setup & Usage

### 1. Wire the hardware

- Connect the PCA9685 to the Arduino via I²C (SDA / SCL).
- Plug all 7 servos into channels 0–6 of the PCA9685.
- Power the servos through the HW-95 driver from the 12 V battery.
- Connect the Arduino to your PC via USB.

### 2. Flash the Arduino

Open `arduino_skitch.ino` in the Arduino IDE and upload it to your board.

### 3. Configure the serial port

In `hands_tracker.py`, update the `PORT` constant to match your Arduino's port:

```python
# Windows
PORT = "COM7"

# macOS / Linux
PORT = "/dev/ttyUSB0"
```

### 4. Run the hand tracker

```bash
python hands_tracker.py
```

Point your hands at the webcam — the display will show the total number of raised fingers.  
Press **ESC** to quit.

---

## 🔁 Infinite Count Mode (standalone)

To run the display as a standalone counter (no camera needed), open `arduino_skitch.ino` and uncomment this line in `loop()`:

```cpp
// infiniteCount();
```

The display will cycle through digits 0–9 continuously with a 500 ms delay between each.

> **Note:** Comment out `handleSerial()` in `loop()` if you enable `infiniteCount()`, so the two modes don't interfere.

---

## 🗂️ Segment Mapping

Each servo channel corresponds to a standard 7-segment layout:

```
 _
|_|
|_|

Channel:  0=a  1=b  2=c  3=d  4=e  5=f  6=g
```

| Digit | a | b | c | d | e | f | g |
|---|---|---|---|---|---|---|---|
| 0 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 1 | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 2 | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| 3 | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| 4 | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| 5 | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |
| 6 | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 7 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 8 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 9 | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |

---

## 🛠️ Configuration Reference

| Constant | File | Default | Description |
|---|---|---|---|
| `PORT` | `hands_tracker.py` | `COM7` | Arduino serial port |
| `INTERVAL` | `hands_tracker.py` | `30` ms | Serial send interval |
| `CAMERA_INDEX` | `hands_tracker.py` | `0` | Webcam index |
| `MAX_HANDS` | `hands_tracker.py` | `2` | Max hands detected |
| `SERVO_MIN` | `arduino_skitch.ino` | `150` | PWM pulse for 0° |
| `SERVO_MAX` | `arduino_skitch.ino` | `400` | PWM pulse for 180° |
| `SEG_ON` | `arduino_skitch.ino` | `180°` | Servo angle for active segment |
| `SEG_OFF` | `arduino_skitch.ino` | `0°` | Servo angle for inactive segment |
