"""
Python program to control a JF-RC Robot using a gamepad.

Author: Fredrik Peteri, fredrik@peteri.se
"""
import threading
from PySide2.QtCore import Slot, Qt, QUrl
from PySide2.QtWidgets import *
from PySide2.QtWebEngineWidgets import QWebEngineView
from sys import argv

from JFRCModel import JFRCModel
from JFRCRobotConnection import JFRCRobotConnection
from keys import KEYS


class JFRCController(QWidget):
	"""
	A controller for the JF-RC application, uses PySide2 as the view and a JFRCModel as the model.
	"""

	jfrc_robot_connection = None
	is_connected = False
	model = JFRCModel()

	def __init__(self):
		super().__init__()

		# Prepare update thread for sending commands to robot
		self.update_thread = None

		# Set up the main window
		self.setWindowTitle("JF-RC Controller")
		self.setGeometry(0, 0, 1000, 1000)

		# Add the 'Connect' button
		connect_button = QPushButton(parent=self, text="Connect")
		connect_button.released.connect(self.connect_dialog)

		# Add the Current URL label
		self.current_url = QLabel(parent=self, text="")

		# Add the Load and Save button
		load_button = QPushButton(parent=self, text="Load")
		load_button.released.connect(lambda: self.model.load(QFileDialog.getOpenFileName(self, "Load Settings")[0]))
		save_button = QPushButton(parent=self, text="Save")
		save_button.released.connect(lambda: self.model.save(QFileDialog.getSaveFileName(self, "Save Settings")[0]))

		# Add camera view
		self.camera = QWebEngineView()
		self.camera.width, self.camera.height = self.model.get_camera_size()

		# Add slider for the steering
		self.steering_indicator = QSlider(orientation=Qt.Horizontal)
		self.steering_indicator.setRange(0, 100)
		self.steering_indicator.setEnabled(False)
		self.model.steering_updated.connect(lambda val: self.steering_indicator.setValue(val * 100))

		# Add slider for throttle
		self.throttle_indicator = QSlider(orientation=Qt.Vertical)
		self.throttle_indicator.setRange(0, 100)
		self.throttle_indicator.setEnabled(False)
		self.model.throttle_updated.connect(lambda val: self.throttle_indicator.setValue(val * 100))

		# Add slider for zoom-level of camera
		self.camera_zoom = QSlider(orientation=Qt.Horizontal)
		self.camera_zoom.setRange(25, 500)
		self.camera_zoom.valueChanged.connect(lambda val: self.camera.setZoomFactor(val / 100))

		# Set the layout of the main window
		main_layout = QGridLayout()
		main_layout.addWidget(connect_button, 0, 0)
		main_layout.addWidget(self.current_url, 0, 1)
		main_layout.addWidget(self.camera_zoom, 1, 0, 1, 2)
		main_layout.addWidget(self.camera, 2, 0, 1, 2)
		main_layout.addWidget(self.throttle_indicator, 2, 2)
		main_layout.addWidget(self.steering_indicator, 3, 0, 1, 2)
		main_layout.addWidget(load_button, 4, 0)
		main_layout.addWidget(save_button, 5, 0)
		self.setLayout(main_layout)

		# Show all the components
		self.show()

	def show_camera(self, url=""):
		self.camera.load(QUrl(f"http://{url}:{self.model.get_camera_port()}"))

	def keyPressEvent(self, event):
		if event.isAutoRepeat() or not self.is_connected:
			return

		key_press = {
			KEYS[self.model.get_keymap()["turn_left"]]: self.model.left,
			KEYS[self.model.get_keymap()["turn_right"]]: self.model.right,
			KEYS[self.model.get_keymap()["turn_center"]]: self.model.move_center,
			KEYS[self.model.get_keymap()["forward"]]: self.model.forward,
			KEYS[self.model.get_keymap()["reverse"]]: self.model.reverse,
		}

		if event.key() in key_press:
			key_press[event.key()]()

	def keyReleaseEvent(self, event):
		if event.isAutoRepeat() or not self.is_connected:
			return

		key_release = {
			KEYS[self.model.get_keymap()["turn_left"]]: self.model.center,
			KEYS[self.model.get_keymap()["turn_right"]]: self.model.center,
			KEYS[self.model.get_keymap()["turn_center"]]: self.model.center_stop,
			KEYS[self.model.get_keymap()["forward"]]: self.model.neutral,
			KEYS[self.model.get_keymap()["reverse"]]: self.model.neutral,
		}

		if event.key() in key_release:
			key_release[event.key()]()

	def start_updates(self):
		self.update_thread = threading.Thread(target=self.jfrc_robot_connection.start)
		self.update_thread.start()

	def stop_updates(self):
		if self.is_connected:
			self.jfrc_robot_connection.stop()
			self.update_thread.join()

	@Slot()
	def connect_dialog(self):
		"""
		Triggers when the user clicks the 'Connect' button, will try to set up a connection with an JF-RC Robot
		"""
		text, ok = QInputDialog().getText(self, "Connect", "URL", QLineEdit.Normal)
		if ok and text:
			try:
				self.model.url = text
				self.jfrc_robot_connection = JFRCRobotConnection(model=self.model)
				self.current_url.setText(f"Connected to: {text}")
				self.is_connected = True
				self.show_camera(text)
				self.start_updates()
			except RuntimeError as e:
				self.current_url.setText(str(e))


if __name__ == '__main__':
	app = QApplication(argv)
	jfrc_controller = JFRCController()

	app.exec_()
	jfrc_controller.stop_updates()
