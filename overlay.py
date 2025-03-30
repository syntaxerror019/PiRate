from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt
import socket
import psutil
import random
import time

class FullscreenApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("PiRate")
        self.setGeometry(0, 0, 1920, 1080)

        self.setCursor(Qt.BlankCursor)

        # Main layout
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignCenter)

        # IP label at the center
        self.ip_label = QLabel("IP Address: Loading...", self)
        self.ip_label.setAlignment(Qt.AlignCenter)
        self.ip_label.setStyleSheet("font-size: 32px;")
        self.main_layout.addWidget(self.ip_label)

        # Bottom-left layout for the status label
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setAlignment(Qt.AlignCenter)
        self.status_label = QLabel("Status: Loading...", self)
        self.status_label.setStyleSheet("font-size: 20px;")
        self.bottom_layout.addWidget(self.status_label)

        # Add the bottom layout to the main layout
        self.main_layout.addLayout(self.bottom_layout)

        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        color1 = "#7BA3C7"
        color2 = "#7BA3C7"

        self.setStyleSheet(
            f"""
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 {color1}, stop:1 {color2});
            color: #fff;
            line-height: 1.6;
            padding: 20px;
            """
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)  # Update every second

        self.showFullScreen()

    def get_ip_address(self):
        interfaces = psutil.net_if_addrs()
        for interface, addresses in interfaces.items():
            for addr in addresses:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    return addr.address  # Returns the first non-localhost IPv4 address

        return "No active network connection found"

    def get_cpu_usage(self):
        return f"{psutil.cpu_percent()}%"

    def get_memory_usage(self):
        memory = psutil.virtual_memory()
        return f"{memory.percent}%"
    
    def get_local_time(self):
        return time.strftime("%H:%M:%S", time.localtime())

    def update_status(self):
        ip_address = self.get_ip_address()
        cpu_usage = self.get_cpu_usage()
        memory_usage = self.get_memory_usage()
        time = self.get_local_time()

        self.status_label.setText(f"CPU Usage: {cpu_usage} | Memory Usage: {memory_usage} | {time}")
        self.ip_label.setText(f"Please visit: <a style='color:#021E83' href='#'>http://{ip_address}:8080</a>")
