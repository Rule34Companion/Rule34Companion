import sys, os, json, random
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog, QPushButton,
    QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QSlider, QCheckBox,
    QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QSettings, QSize, QObject, QEvent, QThread, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QPixmap, QMovie
from PySide6.QtWidgets import QSpinBox


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}

class KeyFilter(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.viewer = parent

    def eventFilter(self, obj, event):
        if event.type() != QEvent.KeyPress:
            return False

        key = event.key()

        if key == Qt.Key_Right:
            self.viewer.next_media()
            return True

        if key == Qt.Key_Left:
            self.viewer.prev_media()
            return True

        if key == Qt.Key_Delete:
            self.viewer.delete_current()
            return True

        return False



def load_tags(json_path):
    try:
        with open(json_path, "r", encoding="utf8") as f:
            data = json.load(f)
    except Exception:
        return []

    tags = data.get("tags", {})
    if not isinstance(tags, dict):
        return []

    flat = []
    for category in tags.values():
        if isinstance(category, list):
            flat.extend(category)

    return [t.lower() for t in flat]


class Viewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("R34Viewer")

        self.delete_log_path = os.path.join(os.path.dirname(__file__), "deleted_images.txt")

        self.settings = QSettings("R34Viewer", "Viewer")
        self.resize(self.settings.value("size", QSize(900, 700)))

        self.all_files = []
        self.files = []
        self.index = 0

        self.shuffle = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.next_media)

        self.image_label = QLabel(alignment=Qt.AlignCenter)
        self.movie = None
        self.movie_buffer = None
        self.image_label.setMinimumSize(1, 1)

        self.filter_box = QLineEdit()
        self.filter_box.setPlaceholderText("tag1 tag2 -tag3")
        self.filter_box.returnPressed.connect(self.apply_filter)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_current)

        self.random_btn = QPushButton("Random")
        self.random_btn.clicked.connect(self.random_media)

        self.slideshow_btn = QPushButton("Slideshow")
        self.slideshow_btn.setCheckable(True)
        self.slideshow_btn.toggled.connect(self.toggle_slideshow)

        self.shuffle_box = QCheckBox("Shuffle")
        self.shuffle_box.toggled.connect(lambda v: setattr(self, "shuffle", v))

        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 300)   # 1 to 300 seconds
        self.interval_input.setValue(5)
        self.interval_input.setSuffix(" sec")
        self.interval_input.setFixedWidth(90)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.filter_box)

        controls = QHBoxLayout()
        controls.addWidget(self.delete_btn)
        controls.addWidget(self.random_btn)
        controls.addWidget(self.slideshow_btn)
        controls.addWidget(self.shuffle_box)
        controls.addWidget(self.interval_input)

        layout.addLayout(controls)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.key_filter = KeyFilter(self)
        QApplication.instance().installEventFilter(self.key_filter)


        self.load_folder()

    # ---------- Loading ----------

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if not folder:
            return

        self.all_files = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in IMAGE_EXTS
        ]

        self.files = list(self.all_files)
        self.index = 0
        self.show_current()

    # ---------- Display ----------

    def show_current(self):
        if not self.files:
            return
        
        self.update_window_title()

        path = self.files[self.index]
        ext = os.path.splitext(path)[1].lower()

        # Stop any existing animation
        if self.movie:
            self.movie.stop()
            self.movie = None

        # Skip non-images (videos, etc.)
        if ext not in IMAGE_EXTS:
            self.next_media()
            return

        # GIF handling (animated)
        # GIF handling (memory-backed, Windows-safe)
        if ext == ".gif":
            # Fully release previous movie
            if self.movie:
                self.movie.stop()
                self.image_label.setMovie(None)
                self.movie = None
                self.movie_buffer = None

            # Load GIF into memory so file is never locked
            with open(path, "rb") as f:
                data = f.read()

            ba = QByteArray(data)
            buffer = QBuffer()
            buffer.setData(ba)
            buffer.open(QIODevice.ReadOnly)

            self.movie_buffer = buffer
            self.movie = QMovie(buffer)

            self.image_label.setMovie(self.movie)

            # Aspect-correct scaling
            self.movie.frameChanged.connect(lambda: self.movie.setScaledSize(
                self.scaled_movie_size(self.movie)
            ))

            self.movie.start()



        # Normal static images
        else:
            pix = QPixmap(path)
            pix = pix.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(pix)

        # Slideshow timing
        if self.timer.isActive():
            self.timer.stop()

        if self.slideshow_btn.isChecked():
            self.timer.start(self.interval_input.value() * 1000)





    # ---------- Navigation ----------

    def next_media(self):
        if not self.files:
            return

        if self.shuffle:
            self.index = random.randrange(len(self.files))
        else:
            self.index = (self.index + 1) % len(self.files)

        self.show_current()


    def prev_media(self):
        if not self.files:
            return
        self.index = (self.index - 1) % len(self.files)
        self.show_current()

    def random_media(self):
        if not self.files:
            return
        self.index = random.randrange(len(self.files))
        self.show_current()

    # ---------- Filtering ----------

    def apply_filter(self):
        query = self.filter_box.text().lower().split()
        pos = [q for q in query if not q.startswith("-")]
        neg = [q[1:] for q in query if q.startswith("-")]

        def matches(path):
            json_path = path + ".json"   # IMPORTANT: see section 2
            if not os.path.exists(json_path):
                return False

            tags = load_tags(json_path)

            return (
                all(t in tags for t in pos) and
                not any(t in tags for t in neg)
            )

        self.files = [f for f in self.all_files if matches(f)]
        self.index = 0
        self.show_current()


    # ---------- Delete ----------

    def delete_current(self):
        if not self.files:
            return

        path = self.files[self.index]
        filename = os.path.basename(path)
        json_path = path + ".json"

        # Stop and release any active movie
        if self.movie:
            self.movie.stop()
            self.image_label.setMovie(None)
            self.movie = None
            self.movie_buffer = None
            QApplication.processEvents()

        # Delete image
        try:
            os.remove(path)
            self.record_deleted(filename)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Delete Error",
                f"Could not delete file:\n{e}"
            )
            return

        # Delete sidecar JSON
        if os.path.exists(json_path):
            try:
                os.remove(json_path)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Delete Error",
                    f"Could not delete JSON:\n{e}"
                )

        # Remove from lists
        if path in self.all_files:
            self.all_files.remove(path)
        if path in self.files:
            self.files.remove(path)

        # Continue viewing
        if self.files:
            self.index %= len(self.files)
            self.show_current()
        else:
            self.image_label.clear()

        self.update_window_title()



    # ---------- Slideshow ----------

    def toggle_slideshow(self, enabled):
        if enabled:
            self.timer.start(self.interval_input.value() * 1000)
        else:
            self.timer.stop()


    # ---------- Cleanup ----------

    def closeEvent(self, e):
        self.settings.setValue("size", self.size())
        e.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if not self.files:
            return

        path = self.files[self.index]
        ext = os.path.splitext(path)[1].lower()

        # Animated GIF
        if ext == ".gif" and self.movie:
            self.movie.setScaledSize(self.scaled_movie_size(self.movie))
            return


        # Static image
        if ext in IMAGE_EXTS:
            pix = QPixmap(path)
            pix = pix.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(pix)

    def scaled_movie_size(self, movie):
        orig = movie.currentPixmap().size()
        target = self.image_label.size()

        if orig.width() == 0 or orig.height() == 0:
            return target

        return orig.scaled(target, Qt.KeepAspectRatio)
    
    def update_window_title(self):
        if not self.files:
            self.setWindowTitle("R34 Viewer")
            return

        name = os.path.basename(self.files[self.index])
        self.setWindowTitle(f"R34 Viewer — {name}")

    def record_deleted(self, filename):
        # Load existing entries
        existing = set()
        if os.path.exists(self.delete_log_path):
            try:
                with open(self.delete_log_path, "r", encoding="utf8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            existing.add(line)
            except:
                pass

        # Add new filename
        existing.add(filename)

        # Write back sorted
        try:
            with open(self.delete_log_path, "w", encoding="utf8") as f:
                for name in sorted(existing):
                    f.write(name + "\n")
        except:
            pass



app = QApplication(sys.argv)
v = Viewer()
v.show()
sys.exit(app.exec())
