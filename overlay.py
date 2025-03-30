from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QSpacerItem, QSizePolicy
from PyQt5.QtCore import QTimer, Qt
import socket
import psutil
import time
import os
from PyQt5.QtGui import QMovie

WALLPAPER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'bg.gif')

class FullscreenApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("PiRate")
        self.setGeometry(0, 0, 1920, 1080)

        self.setCursor(Qt.BlankCursor)

        # Background GIF
        self.gif_label = QLabel(self)
        self.gif_label.setGeometry(0, 0, self.width(), self.height())
        self.movie = QMovie(WALLPAPER)
        self.gif_label.setMovie(self.movie)
        self.movie.setScaledSize(self.size())  # Scale the GIF dynamically
        self.gif_label.setScaledContents(True)
        self.movie.start()

        # Central widget container
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Layouts
        self.container_layout = QVBoxLayout(self.central_widget)

        # Spacer to push content to center
        self.container_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Main vertical layout (centered items)
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignCenter)

        # Time Label (Biggest)
        self.time_label = QLabel("00:00:00", self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size: 100px; font-weight: bold; color: white;")
        self.main_layout.addWidget(self.time_label)

        # Status Label (CPU & Memory)
        self.status_label = QLabel("CPU Usage: --%    Memory Usage: --%", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 20px;")
        self.main_layout.addWidget(self.status_label)

        # Add main centered content
        self.container_layout.addLayout(self.main_layout)

        # Another spacer to keep things centered
        self.container_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Bottom Layout for IP (Bottom Left)
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setAlignment(Qt.AlignLeft)  # Align to bottom left

        self.ip_label = QLabel("IP Address: Loading...", self)
        self.ip_label.setStyleSheet("font-size: 27px; color: white;")
        self.bottom_layout.addWidget(self.ip_label)

        # Push IP to the bottom
        self.container_layout.addLayout(self.bottom_layout)

        self.central_widget.setLayout(self.container_layout)

        # Make sure labels are on top of GIF
        self.gif_label.lower()
        self.central_widget.raise_()

        # Set global text style
        self.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                letter-spacing: 1.7px;
            }
        """)

        # Timer for updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)  

        self.showFullScreen()

    def get_ip_address(self):
        interfaces = psutil.net_if_addrs()
        for interface, addresses in interfaces.items():
            for addr in addresses:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    return addr.address  
        return "No active network connection"

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
        local_time = self.get_local_time()

        self.status_label.setText(f"CPU Usage:  {cpu_usage}    Memory Usage:  {memory_usage}")
        self.ip_label.setText(f"Please visit:&nbsp;&nbsp;<a style='color:#008CD7; text-decoration: none;' href='#'>http://{ip_address}:8080</a>")
        self.time_label.setText(local_time)
