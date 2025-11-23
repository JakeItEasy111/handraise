import sys
import requests
from PyQt5.QtWidgets import QApplication, QScrollArea, QMainWindow, QFrame, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QMessageBox, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from sseclient import SSEClient

SERVER_URL = "http://127.0.0.1:5000"
class_id = None 

shadow = QGraphicsDropShadowEffect()
shadow.setBlurRadius(20)
shadow.setXOffset(0)
shadow.setYOffset(5)
shadow.setColor(QColor(0, 0, 0, 80))  # semi-transparent black

class SSEWorker(QThread):
    new_message = pyqtSignal(str)

    def __init__(self, class_id):
        super().__init__()
        self.class_id = class_id
        self._running = True
        
    def run(self):
        print(f"SSEWorker started for {self.class_id}")
        while self._running:
            try: 
                messages = SSEClient(f"{SERVER_URL}/classrooms/{self.class_id}/stream")
                for msg in messages:
                    self.new_message.emit(msg.data)

            except Exception as e:
                print(f"{self.class_id}: could not load messages - {e}")
                self.msleep(3000)  # wait 3 seconds before retrying
        
    def stop(self):
        self._running = False
        self.quit()
        self.wait()

class TeacherApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Handraise Teacher")
        self.setGeometry(480, 270, 960, 540)
        
        # Initialize screens
        self.create_class_session = CreateClassSessionUI()
        self.create_class_session.classCreated.connect(self.change_screen)

        self.setCentralWidget(self.create_class_session)

    def change_screen(self):
        self.stream = StreamSessionUI()
        self.setCentralWidget(self.stream)
        

class CreateClassSessionUI(QFrame):
    classCreated = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Outer layout
        v_layout = QVBoxLayout() 
        self.setLayout(v_layout)
        v_layout.addStretch(1)

        # App title 
        app_title = QLabel("Handraise Teacher")
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
        self.instruction_label = QLabel("Create class session:")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet("font-size: 30px; font-weight: bold; font-family: arial, Helvetica, sans-serif;")
        
        #class id entry 
        self.id_entry = QLineEdit()
        self.id_entry.setPlaceholderText("Enter classroom ID")
        self.id_entry.setStyleSheet("color: white; background-color: #a3a6b0; border-radius:10px; padding: 6px; min-width: 5em; font:bold 36px; font-family: arial, Helvetica, sans-serif; ")
        self.id_entry.setGraphicsEffect(shadow)
        self.id_entry.setMaxLength(10)

        # name entry 
        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("Enter class name")
        self.name_entry.setStyleSheet("color: white; background-color: #a3a6b0; border-radius:10px; padding: 6px; min-width: 5em; font:bold 36px; font-family: arial, Helvetica, sans-serif; ")

        #create button 
        self.join_button = QPushButton("Make session")
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
        self.join_button.pressed.connect(self.make_pressed)

        # ERROR LABEL (appears when classroom ID invalid)
        self.error_label = QLabel("Please enter a class ID")
        self.error_label.setStyleSheet("color: red; font-size: 14px;")
        self.error_label.setVisible(False)

        # Optional: Next button (after classroom accepted)
        self.name_button = QPushButton("Join Class")
        self.name_button.setVisible(False)
        function_layout.addWidget(self.name_button)

        self.middle_widget.setLayout(function_layout)
        function_layout.addWidget(self.instruction_label)
        function_layout.addWidget(self.id_entry)
        function_layout.addWidget(self.name_entry)
        function_layout.addWidget(self.join_button)
        function_layout.addWidget(self.error_label)
        
        h_layout.addWidget(self.middle_widget)
        h_layout.addStretch(1)
        v_layout.addStretch(1)

    def make_pressed(self):
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
            self.error_label.setText("Please enter a classroom name.")
            self.error_label.setVisible(True)
            return

        # 2. Check if classroom exists
        try:
            response = requests.post(f"{SERVER_URL}/classrooms/{id_field}/create", json={"name":name_field})
            if response.status_code != 201 and response.status_code != 409:
                self.error_label.setText("Classroom couldn't be created")
                self.error_label.setVisible(True)
                return
            
        except Exception:
            self.error_label.setText("Could not connect to server.")
            self.error_label.setVisible(True)
            return

        global class_id
        class_id = id_field
        self.classCreated.emit()

class StreamSessionUI(QFrame):

    def __init__(self):
        super().__init__()
        self.worker = SSEWorker(class_id)
        self.worker.new_message.connect(self.add_message_to_list)
        self.worker.start()

        outer_layout = QVBoxLayout() 
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()
        self.setLayout(outer_layout)

        # ID at top left corner 
        self.id_label = QLabel(f"Class ID: {class_id}")
        self.id_label.setStyleSheet("""
        background-color: #5ece88;
        color: white;
        border-radius: 15px;
        padding: 10px 20px;
        font-size: 24px;
        font-family: arial, Helvetica, sans-serif;
        """)

        top_layout.addWidget(self.id_label)
        top_layout.setContentsMargins(5, 5, 5, 5)
        top_layout.addStretch(1)
        
        middle_layout = QVBoxLayout()

        self.list_label = QLabel("Your Signals")
        self.list_label.setAlignment(Qt.AlignHCenter)
        self.list_label.setStyleSheet("""
        background-color: #717587;
        color: white;
        border-radius: 15px;
        padding: 5px 30px;
        font-size: 24px;
        font-family: arial, Helvetica, sans-serif;
        """)

        
        self.list_widget = QWidget()
        self.signals_layout = QVBoxLayout()
        self.signals_layout.setContentsMargins(15, 15, 15, 15)
        self.signals_layout.setSpacing(10)
        self.list_widget.setLayout(self.signals_layout)

        scroll = QScrollArea()
        scroll.setWidget(self.list_widget)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
                            QScrollBar:vertical{                                         
                                border: none;
                                width: 5px;
                                border-radius: 3px; 
                            }
                            QScrollBar::handle:vertical{
                                background-color: WHITE;
                                width: 10px; 
                                border-radius: 7px;
                            }
                            QScrollBar::add-line:horizontal 
                            {
                                width: 0px;
                                subcontrol-position: right;
                                subcontrol-origin: margin;
                            }
                            QScrollBar::sub-line:horizontal 
                            {
                                width: 0 px;
                                subcontrol-position: left;
                                subcontrol-origin: margin;
                            }
                            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                                background: none;
                            }
                            """)
        
        middle_layout.addWidget(self.list_label)
        middle_layout.addWidget(scroll)

        bottom_layout.addStretch(1)
        bottom_layout.addLayout(middle_layout, 3)
        bottom_layout.setContentsMargins(20, 20, 20, 20)
        bottom_layout.addStretch(1)

        outer_layout.addLayout(top_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        outer_layout.addWidget(separator)

        outer_layout.addLayout(bottom_layout)

    def add_message_to_list(self, msg):
        frame = signalFrame(msg) 
        self.signals_layout.addWidget(frame)
        self.signals_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

class signalFrame(QFrame):
    def __init__(self, msg):
        super().__init__()

        self.message = msg 

        frame_layout = QHBoxLayout()
        self.setLayout(frame_layout)

        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("background-color: white; padding: 10px; border-radius: 20px;")

        self.label = QLabel(self.message)
        self.label.setStyleSheet("font-size: 18px; font-family: arial, Helvetica, sans-serif;")
        
        self.acknowledge_button = QPushButton("Acknowledge")
        self.acknowledge_button.setStyleSheet("""
            QPushButton {
                background-color: #b3e1be;
                color: white;
                border-radius: 15px;
                padding: 10px 10px;
                font-size: 24px;
                font-family: arial, Helvetica, sans-serif;
            }
            QPushButton:hover {
                background-color: #47bd78;
            }
        """)
        self.acknowledge_button.pressed.connect(self.remove_signal)
        
        frame_layout.addStretch(1)
        frame_layout.addWidget(self.label)
        frame_layout.addWidget(self.acknowledge_button)
    
    def remove_signal(self):
        try:
            response = requests.delete(f"{SERVER_URL}/classrooms/{class_id}/signal/remove", json={"signal": self.message})

            if response.status_code != 200: 
                print("Could not delete")
                return

            print("Deleted signal successfully")
            self.setParent(None)
            self.deleteLater()
            self.objectName = None
            return 

        except Exception:
            print("fail")
            return
        
def main(): 
    if __name__ == "__main__":
        app = QApplication(sys.argv)
        window = TeacherApp()
        window.show()
        sys.exit(app.exec())

main() 