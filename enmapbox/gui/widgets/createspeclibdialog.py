from typing import List

from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from qgis.PyQt.QtWidgets import QFileDialog, QDialogButtonBox, QPushButton, QLineEdit, QHBoxLayout, QLabel, \
    QRadioButton, \
    QButtonGroup, QVBoxLayout, QDialog
from qgis.core import QgsVectorLayer


class CreateSpectralLibraryDialog(QDialog):
    """
    Dialog to create a new spectral library with user-specified profile fields.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Spectral Library")
        self.setMinimumWidth(400)

        # Storage type selection
        self._storage_in_memory = True
        self._file_path = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Profile field names input
        field_layout = QVBoxLayout()
        field_label = QLabel("Profile Field Names (comma or space separated):")
        self.field_input = QLineEdit('profiles')
        self.field_input.setPlaceholderText("e.g., profiles, reflectance, transmittance")
        field_layout.addWidget(field_label)
        field_layout.addWidget(self.field_input)
        layout.addLayout(field_layout)

        # Storage location selection
        storage_label = QLabel("Storage Location:")
        layout.addWidget(storage_label)

        # Radio buttons for storage type
        self.radio_memory = QRadioButton("Memory (temporary)")
        self.radio_file = QRadioButton("File")
        self.radio_memory.setChecked(True)

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.radio_memory)
        self.button_group.addButton(self.radio_file)

        layout.addWidget(self.radio_memory)

        # File selection layout
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.radio_file)
        self.file_path_input = QLineEdit()
        self.file_path_input.setEnabled(False)
        self.file_path_input.setPlaceholderText("Select output file...")
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setEnabled(False)
        self.browse_button.clicked.connect(self._browse_file)

        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(self.browse_button)
        layout.addLayout(file_layout)

        # Connect radio button signals
        self.radio_memory.toggled.connect(self._on_storage_type_changed)
        self.radio_file.toggled.connect(self._on_storage_type_changed)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _on_storage_type_changed(self):
        """Enable/disable file selection based on storage type."""
        is_file = self.radio_file.isChecked()
        self.file_path_input.setEnabled(is_file)
        self.browse_button.setEnabled(is_file)
        self._storage_in_memory = not is_file

    def _browse_file(self):
        """Open file dialog to select output file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Spectral Library",
            "",
            "GeoPackage (*.gpkg);;GeoJSON (*.geojson);;All Files (*)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
            self._file_path = file_path

    def get_profile_field_names(self) -> List[str]:
        """
        Returns a list of profile field names from user input.

        Returns:
            list: List of field names, empty list if no input.
        """
        text = self.field_input.text().strip()
        return list(set([name.strip() for name in text.split(',') if name.strip()]))

    def is_memory_storage(self) -> bool:
        """
        Returns True if the library should be stored in memory.

        Returns:
            bool: True for memory storage, False for file storage.
        """
        return self._storage_in_memory

    def get_file_path(self):
        """
        Returns the file path if file storage is selected.

        Returns:
            str or None: File path or None if memory storage is selected.
        """
        if self._storage_in_memory:
            return None
        return self.file_path_input.text().strip() or None

    def create_speclib(self) -> QgsVectorLayer:

        profile_fields = self.get_profile_field_names()
        path = self.get_file_path()
        sl = SpectralLibraryUtils.createSpectralLibrary(profile_fields=profile_fields)

        return sl
