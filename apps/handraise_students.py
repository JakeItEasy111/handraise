import sys
import requests
from PyQt5.QtWidgets import QApplication, QScrollArea, QMainWindow, QFrame, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QMessageBox, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, pyqtSignal 
from PyQt5.QtGui import QColor

SERVER_URL = "http://127.0.0.1:5000" #localhost
student_name = None 
class_id = None 

shadow = QGraphicsDropShadowEffect()
shadow.setBlurRadius(20)
shadow.setXOffset(0)
shadow.setYOffset(5)
shadow.setColor(QColor(0, 0, 0, 80))  # semi-transparent black

class StudentApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Handraise Student")
        self.setGeometry(480, 270, 960, 540)
        
        # Initialize screens
        self.join_class_screen = JoinClassScreen()
        self.join_class_screen.classJoined.connect(self.change_screen)
        self.signal_screen = SignalScreen()
        self.signal_screen.signalSelected.connect(send_signal)

        self.setCentralWidget(self.join_class_screen)

    def change_screen(self):
        self.setCentralWidget(self.signal_screen)
        print("Screen changed!")

# Centered vbox that just says 
class JoinClassScreen(QFrame): 
    classJoined = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Outer layout
        v_layout = QVBoxLayout() 
        self.setLayout(v_layout)
        v_layout.addStretch(1)

        # App title 
        app_title = QLabel("Handraise Student")
        app_title.setStyleSheet("font-size: 36px; font-weight: bold; font-family: arial, Helvetica, sans-serif;")
        app_title.setAlignment(Qt.AlignCenter)
        v_layout.addWidget(app_title)

        # Horizontal layout for centering 
        h_layout = QHBoxLayout() 
        v_layout.addLayout(h_layout)
        h_layout.addStretch(1)

        #Centered widget 
        self.middle_widget = QWidget()
        self.middle_widget.setFixedSize(400, 300)
        self.middle_widget.setStyleSheet("background-color: WHITE; border-radius: 15px;")

        function_layout = QVBoxLayout()
        function_layout.setContentsMargins(20, 20, 20, 20)
        function_layout.setSpacing(10)

        #Centered widget contents
        self.instruction_label = QLabel("Join your class:")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet("font-size: 30px; font-weight: bold; font-family: arial, Helvetica, sans-serif;")
        
        # name entry 
        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("Enter your name")
        self.name_entry.setStyleSheet("color: white; background-color: #a3a6b0; border-radius:10px; padding: 6px; min-width: 5em; font:bold 36px; font-family: arial, Helvetica, sans-serif; ")

        #class id entry 
        self.id_entry = QLineEdit()
        self.id_entry.setPlaceholderText("Enter classroom ID")
        self.id_entry.setStyleSheet("color: white; background-color: #a3a6b0; border-radius:10px; padding: 6px; min-width: 5em; font:bold 36px; font-family: arial, Helvetica, sans-serif; ")
        self.id_entry.setGraphicsEffect(shadow)
        self.id_entry.setMaxLength(10)

        #join button 
        self.join_button = QPushButton("Join")
        self.join_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 15px;
                padding: 10px 20px;
                font-size: 24px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.join_button.setGraphicsEffect(shadow)
        self.join_button.pressed.connect(self.joinPressed)

        # ERROR LABEL (appears when classroom ID invalid)
        self.error_label = QLabel("Invalid class ID, please try again")
        self.error_label.setStyleSheet("color: red; font-size: 14px;")
        self.error_label.setVisible(False)

        self.middle_widget.setLayout(function_layout)
        function_layout.addWidget(self.instruction_label)
        function_layout.addWidget(self.name_entry)
        function_layout.addWidget(self.id_entry)
        function_layout.addWidget(self.join_button)
        function_layout.addWidget(self.error_label)
        
        h_layout.addWidget(self.middle_widget)
        h_layout.addStretch(1)
        v_layout.addStretch(1)

    def joinPressed(self):
        id_field = self.id_entry.text().strip()
        name_field = self.name_entry.text().strip()

        # Clear previous error
        self.error_label.setVisible(False)

        # 1. Check empty field
        if not id_field:
            self.error_label.setText("Please enter a classroom code.")
            self.error_label.setVisible(True)
            return
        if not name_field:
            self.error_label.setText("Please enter your name")
            self.error_label.setVisible(True)
            return

        # 2. Check if classroom exists
        try:
            response = requests.get(f"{SERVER_URL}/classrooms/{id_field}")
            if response.status_code != 200:
                self.error_label.setText("Classroom not found.")
                self.error_label.setVisible(True)
                return
        except Exception:
            self.error_label.setText("Could not connect to server.")
            self.error_label.setVisible(True)
            return

        # SUCCESS — classroom exists
        response = requests.post(f"{SERVER_URL}/classrooms/{id_field}/join", json={"name": name_field})
        if response.status_code == 200 or response.status_code == 201:
            print("Joined successfully!")
            global class_id, student_name
            class_id = id_field
            student_name = name_field
            self.classJoined.emit()
        else:
            print("Failed:", response.status_code, response.text)
            self.error_label.setText("Error joining classroom")


class SignalScreen(QFrame):
    signalSelected = pyqtSignal(str)   # emits signal_type when user taps a button

    def __init__(self):
        super().__init__()

        # Main layout (full window)
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)
        self.setLayout(main_layout)

        # Title
        title = QLabel("Send your teacher a signal!")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 32px;
            font-family: arial, Helvetica, sans-serif;
        """)
        main_layout.addWidget(title)

        # Scrollable area for buttons (in case they overflow)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)

        container = QWidget()
        self.buttons_layout = QVBoxLayout()
        self.buttons_layout.setAlignment(Qt.AlignTop)
        container.setLayout(self.buttons_layout)
        scroll.setWidget(container)

        # Load buttons from API
        self.load_signal_types()

    # ---------------------------
    # Fetch signal types from API
    # ---------------------------

    def load_signal_types(self):
        try:
            res = requests.get(f"{SERVER_URL}/signal-types")
            signal_types = res.json()       # { "pencil": "I need a pencil", ... }
        except Exception as e:
            print("Failed to load signal types:", e)
            return

        # Create a button for each signal type
        for signal_type, text in signal_types.items():
            btn = QPushButton(text)
            btn.setFixedHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    font-size: 20px;
                    padding: 10px;
                    border-radius: 12px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            btn.clicked.connect(lambda checked, s=signal_type: self.signalSelected.emit(s))

            self.buttons_layout.addWidget(btn)

def send_signal(signal_type):
    try:
        url = f"{SERVER_URL}/classrooms/{class_id}/signal"
        payload = {"name": student_name, "signal_type": signal_type}

        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True, response.get_json()

    except Exception as e:
        return False, str(e)

def main():
    if __name__ == "__main__":
        app = QApplication(sys.argv)
        window = StudentApp()
        window.show()
        sys.exit(app.exec())

main()
