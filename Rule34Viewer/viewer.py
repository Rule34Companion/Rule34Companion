import sys, os, json, random
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog, QPushButton,
    QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QSlider, QCheckBox,
    QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QSettings, QSize, QObject, QEvent, QThread, QByteArray, QBuffer, QIODevice, QUrl
from PySide6.QtGui import QPixmap, QMovie
from PySide6.QtWidgets import QSpinBox, QTextEdit, QSplitter
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".webm", ".mkv", ".mov"}
MEDIA_EXTS = IMAGE_EXTS | VIDEO_EXTS

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

        if key == Qt.Key_Space:
            self.viewer.toggle_play()
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


def load_comments(json_path):
    try:
        with open(json_path, "r", encoding="utf8") as f:
            data = json.load(f)
    except Exception:
        return []

    comments = data.get("comments")
    if not isinstance(comments, list):
        return []

    return comments


class SeekSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            value = self.minimum() + (
                (self.maximum() - self.minimum()) *
                event.position().x() / self.width()
            )
            self.setValue(int(value))
            self.sliderMoved.emit(int(value))
        super().mousePressEvent(event)


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
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(2,2)

        from PySide6.QtWidgets import QStackedLayout

        self.media_container = QWidget()

        self.stack = QStackedLayout()
        self.stack.setContentsMargins(0,0,0,0)

        # Image page
        image_page = QWidget()
        image_layout = QHBoxLayout()
        image_layout.setContentsMargins(0,0,0,0)
        image_layout.addStretch()
        image_layout.addWidget(self.image_label)
        image_layout.addStretch()
        image_page.setLayout(image_layout)

        # Video page
        video_page = QWidget()
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0,0,0,0)
        video_layout.addWidget(self.video_widget)
        video_page.setLayout(video_layout)

        self.stack.addWidget(image_page)
        self.stack.addWidget(video_page)

        self.media_container.setLayout(self.stack)

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

        # --- Comments panel ---
        self.comment_panel = QTextEdit()
        self.comment_panel.setReadOnly(True)
        self.comment_panel.setMinimumWidth(300)
        self.comment_panel.setFocusPolicy(Qt.NoFocus)

        # --- Toggle checkboxes ---
        self.show_comments_box = QCheckBox("Show Comments")
        self.only_comments_box = QCheckBox("Only With Comments")
        self.only_comments_box.setEnabled(False)

        self.show_comments_box.toggled.connect(self.toggle_comments)
        self.only_comments_box.toggled.connect(self.apply_comment_filter)

        self.audio = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)

        self.player.mediaStatusChanged.connect(self.video_status_changed)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)

        # --- Video Controls ---
        self.video_controls = QWidget()
        vc_layout = QHBoxLayout()

        self.play_btn = QPushButton("Pause")
        self.play_btn.clicked.connect(self.toggle_play)

        self.seek_slider = SeekSlider(Qt.Horizontal)
        self.seek_slider.setStyleSheet("""
        QSlider::groove:horizontal {
            background: #444;
            height: 6px;
            border-radius: 3px;
        }

        QSlider::handle:horizontal {
            background: #ddd;
            border: 1px solid #222;
            width: 12px;
            margin: -5px 0;
            border-radius: 6px;
        }

        QSlider::sub-page:horizontal {
            background: #888;
            border-radius: 3px;
        }
        """)
        self.seek_slider.sliderPressed.connect(self.pause_for_seek)
        self.seek_slider.sliderReleased.connect(self.seek_to_position)
        self.seek_slider.sliderMoved.connect(self.player.setPosition)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setStyleSheet("""
        QSlider::groove:horizontal {
            background: #444;
            height: 6px;
            border-radius: 3px;
        }

        QSlider::handle:horizontal {
            background: #ddd;
            border: 1px solid #222;
            width: 10px;
            margin: -5px 0;
            border-radius: 5px;
        }
        """)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.volume_changed)

        self.mute_btn = QPushButton("Mute")
        self.mute_btn.clicked.connect(self.toggle_mute)

        vc_layout.addWidget(self.play_btn)
        vc_layout.addWidget(self.seek_slider, 1)
        self.seek_slider.setTracking(False)
        vc_layout.addWidget(self.volume_slider)
        vc_layout.addWidget(self.mute_btn)

        self.video_controls.setLayout(vc_layout)
        self.video_controls.hide()


        # --- Left side layout ---
        left_layout = QVBoxLayout()

        left_layout.addWidget(self.media_container, 1)
        left_layout.addWidget(self.video_controls)
        left_layout.addWidget(self.filter_box)

        controls = QHBoxLayout()
        controls.addWidget(self.delete_btn)
        controls.addWidget(self.random_btn)
        controls.addWidget(self.slideshow_btn)
        controls.addWidget(self.shuffle_box)
        controls.addWidget(self.interval_input)
        controls.addWidget(self.show_comments_box)
        controls.addWidget(self.only_comments_box)

        left_layout.addLayout(controls)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        # --- Splitter (permanent side panel) ---
        splitter = QSplitter()
        splitter.addWidget(left_widget)
        splitter.addWidget(self.comment_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

        # --- Hide panel content initially (but panel remains) ---
        self.comment_panel.hide()

        self.key_filter = KeyFilter(self)
        QApplication.instance().installEventFilter(self.key_filter)

        self.volume_slider.setValue(self.settings.value("volume", 50, int))
        self.audio.setVolume(self.volume_slider.value() / 100)

        mute = self.settings.value("muted", False, bool)
        self.audio.setMuted(mute)
        self.mute_btn.setText("Unmute" if mute else "Mute")

        self.load_folder()

    # ---------- Loading ----------

    def load_folder(self, folder=None):

        last = self.settings.value("last_folder", "")

        start_dir = last if last and os.path.exists(last) else ""

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Image Folder",
            start_dir
        )

        if not folder:
            return

        self.settings.setValue("last_folder", folder)

        self.all_files = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in MEDIA_EXTS
        ]

        self.files = list(self.all_files)
        self.index = 0
        self.show_current()

    # ---------- Display ----------

    def show_current(self):
        if not self.files:
            return

        path = self.files[self.index]
        ext = os.path.splitext(path)[1].lower()

        self.update_window_title()

        # -------- VIDEO --------
        if ext in VIDEO_EXTS:

            # Stop slideshow timer so it can't interrupt video
            if self.timer.isActive():
                self.timer.stop()

            self.stack.setCurrentIndex(1)  # video page
            self.video_controls.show()

            self.player.stop()
            self.player.setSource(QUrl.fromLocalFile(path))

            QTimer.singleShot(50, self.player.play)

            return

        path = self.files[self.index]
        ext = os.path.splitext(path)[1].lower()

        # Stop any existing animation
        if self.movie:
            self.movie.stop()
            self.movie = None

        # Skip non-images (videos, etc.)
        if ext not in MEDIA_EXTS:
            self.next_media()
            return

        # GIF handling (animated)
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

            target = self.media_container.size()

            self.movie.setScaledSize(
                self.movie.currentPixmap().size().scaled(
                    target,
                    Qt.KeepAspectRatio
                )
            )

            self.image_label.setMovie(self.movie)
            self.movie.start()

        # ---------- Static image handling ----------
        if ext != ".gif":
            pix = QPixmap(path)

            target = self.media_container.size()

            pix = pix.scaled(
                target,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.image_label.setPixmap(pix)

        # ---------- Comment display ----------
        if self.show_comments_box.isChecked():
            json_path = path + ".json"
            comments = load_comments(json_path) if os.path.exists(json_path) else []

            if comments:
                text = []
                for c in comments:
                    creator = c.get("creator", "unknown")
                    body = c.get("body", "")
                    created = c.get("created_at", "")
                    text.append(f"{creator} ({created})\n{body}\n")
                self.comment_panel.setPlainText("\n---\n".join(text))
            else:
                self.comment_panel.setPlainText("No comments.")
        else:
            self.comment_panel.clear()

        # Slideshow timing
        if self.timer.isActive():
            self.timer.stop()

        # slideshow only applies to images
        if self.slideshow_btn.isChecked() and ext not in VIDEO_EXTS:
            self.timer.start(self.interval_input.value() * 1000)

        self.stack.setCurrentIndex(0)  # image page
        self.video_controls.hide()
        self.player.stop()


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
        # Stop video playback to release file lock
        self.player.stop()
        self.player.setSource(QUrl())

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

            target = self.media_container.size()

            pix = pix.scaled(
                target,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.image_label.setPixmap(pix)


    def scaled_movie_size(self, movie):
        orig = movie.currentPixmap().size()
        target = self.media_container.size()

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


    def toggle_comments(self, enabled):
        self.only_comments_box.setEnabled(enabled)

        if not enabled:
            self.only_comments_box.setChecked(False)

        # Keep panel width reserved but hide text content
        if enabled:
            self.comment_panel.show()
        else:
            self.comment_panel.hide()

        self.show_current()


    def apply_comment_filter(self):
        if not self.only_comments_box.isChecked():
            self.files = list(self.all_files)
        else:
            filtered = []
            for path in self.all_files:
                json_path = path + ".json"
                if not os.path.exists(json_path):
                    continue
                comments = load_comments(json_path)
                if comments:
                    filtered.append(path)

            self.files = filtered

        self.index = 0
        self.show_current()


    def video_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:

            if self.slideshow_btn.isChecked():
                self.next_media()
            else:
                # loop video
                self.player.setPosition(0)
                self.player.play()


    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("Play")
        else:
            self.player.play()
            self.play_btn.setText("Pause")


    def toggle_mute(self):
        muted = not self.audio.isMuted()
        self.audio.setMuted(muted)

        self.settings.setValue("muted", muted)

        self.mute_btn.setText("Unmute" if muted else "Mute")


    def update_position(self, pos):
        if not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(pos)


    def update_duration(self, dur):
        self.seek_slider.setRange(0, dur)


    def pause_for_seek(self):
        self.was_playing = self.player.playbackState() == QMediaPlayer.PlayingState
        self.player.pause()


    def seek_to_position(self):
        pos = self.seek_slider.value()
        self.player.setPosition(pos)

        if getattr(self, "was_playing", False):
            self.player.play()


    def volume_changed(self, value):
        self.audio.setVolume(value / 100)
        self.settings.setValue("volume", value)





app = QApplication(sys.argv)
v = Viewer()
v.show()
sys.exit(app.exec())
