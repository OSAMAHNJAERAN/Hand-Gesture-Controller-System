# 🖐️ Hand Gesture Control System

A powerful, real-time Python application that allows you to control your computer and presentations using hand gestures. Powered by **MediaPipe** and **OpenCV**, this system provides a seamless touchless experience for mouse control, volume adjustment, and slide navigation.

## 🚀 Features

### 💻 Mouse Controller
- **Precision Movement**: Smooth cursor control with linear interpolation.
- **Clicking**: Left and Right clicks using pinch gestures.
- **Drag & Drop**: Long-pinch to grab and move windows or items.
- **Volume Control**: Adjust system volume by moving your hand up and down.

### 📊 Presentation Mode
- **Navigation**: Move to the next or previous slide with simple thumb/pinky gestures.
- **Drawing**: Annotate your slides in real-time.
- **Laser Pointer**: A virtual red pointer for highlighting key points.
- **Undo/Erase**: Quickly remove mistakes or clear the entire slide.
- **PiP Overlay**: See your webcam feed in a small window over the presentation.

## 🛠️ Tech Stack
- **Language**: Python 3.10+
- **AI Framework**: MediaPipe (Hand Landmarker)
- **Computer Vision**: OpenCV
- **Automation**: PyAutoGUI
- **Audio Control**: Pycaw

## ⚙️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/OSAMAHNJAERAN/Hand-Gesture-Controller-System.git
   cd Hand-Gesture-Controller-System
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare Slides**:
   Place your presentation slides (images like `1.png`, `2.png`, etc.) in the `Presentation` folder.

## 🎮 How to Use

Run the main application:
```bash
python main.py
```

### 🖖 Gesture Map

| Action | Mode | Gesture |
| :--- | :--- | :--- |
| **Switch Mode** | Both | Thumb + Pinky Up (Hang Loose) |
| **Move Mouse** | Mouse | Index Finger Up |
| **Left Click** | Mouse | Pinch (Index + Thumb) |
| **Right Click** | Mouse | Double Pinch or Hold |
| **Volume Control**| Mouse | Three Fingers Up + Move Vertical |
| **Next Slide** | Presentation | Pinky Up (Hand above green line) |
| **Prev Slide** | Presentation | Thumb Up (Hand above green line) |
| **Draw** | Presentation | Index Finger Up |
| **Laser Pointer** | Presentation | Index + Middle Finger Up |
| **Undo Stroke** | Presentation | Index + Middle + Ring Finger Up |
| **Clear All** | Presentation | All Fingers Up |

## 📝 Configuration
You can adjust sensitivity, smoothing, and gesture thresholds in `main.py` and `mouse_controller.py` to match your environment.

## 📜 License
This project is open-source and available under the MIT License.

---
*Created with ❤️ by Antigravity*
