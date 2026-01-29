import os
from typing import List, Optional

from enmapbox.qgispluginsupport.qps.fieldvalueconverter import GenericFieldValueConverter
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from qgis.PyQt.QtWidgets import QFileDialog, QDialogButtonBox, QLineEdit, QHBoxLayout, QLabel, \
    QRadioButton, \
    QButtonGroup, QVBoxLayout, QDialog
from qgis.core import QgsFeature, QgsVectorLayer, QgsVectorFileWriter, QgsProject, QgsMapLayer, edit
from qgis.gui import QgsFileWidget


class CreateSpectralLibraryDialog(QDialog):
    """
    Dialog to create a new spectral library with user-specified profile fields.
    """

    LAST_LAYER_NAME = 'SpectralLibrary'
    LAST_FILE_PATH = None
    LAST_PROFILE_FIELDS = ['profiles']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Spectral Library")
        self.setMinimumWidth(400)

        # Storage type selection
        self._storage_in_memory = True
        self._file_path = None

        self._setup_ui()
        self.validate()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Layer Name input
        name_layout = QVBoxLayout()
        name_label = QLabel("Layer Name:")
        self.layer_name = QLineEdit("Spectral Library")
        self.layer_name.setPlaceholderText("Enter layer name")
        if isinstance(CreateSpectralLibraryDialog.LAST_LAYER_NAME, str):
            self.layer_name.setText(CreateSpectralLibraryDialog.LAST_LAYER_NAME)

        name_layout.addWidget(name_label)
        name_layout.addWidget(self.layer_name)
        layout.addLayout(name_layout)

        # Profile field names input
        field_layout = QVBoxLayout()
        field_label = QLabel("Profile Field Names (comma separated):")

        self.field_input = QLineEdit('profiles')
        self.field_input.setPlaceholderText("e.g., profiles, reflectance, transmittance")
        if isinstance(CreateSpectralLibraryDialog.LAST_PROFILE_FIELDS, list):
            self.field_input.setText(','.join(CreateSpectralLibraryDialog.LAST_PROFILE_FIELDS))

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

        self.file_widget = QgsFileWidget()
        self.file_widget.setDialogTitle('Create empty spectral library')
        self.file_widget.setFilter('GeoPackage (*.gpkg);;GeoJSON (*.geojson)')
        self.file_widget.setStorageMode(QgsFileWidget.StorageMode.SaveFile)

        if isinstance(CreateSpectralLibraryDialog.LAST_FILE_PATH, str):
            self.radio_file.setChecked(True)
            self.file_widget.setFilePath(CreateSpectralLibraryDialog.LAST_FILE_PATH)

        self.file_widget.fileChanged.connect(self.validate)
        file_layout.addWidget(self.file_widget)
        # self.file_path = QLineEdit()
        # self.file_path.setEnabled(False)
        # self.file_path.setPlaceholderText("Select output file...")
        # self.file_path.textChanged.connect(self.validate)
        #
        # self.browse_button = QPushButton("Browse...")
        # self.browse_button.setEnabled(False)
        # self.browse_button.clicked.connect(self._browse_file)
        #
        # file_layout.addWidget(self.file_path)
        # file_layout.addWidget(self.browse_button)
        #
        layout.addLayout(file_layout)

        # Connect radio button signals
        self.radio_memory.toggled.connect(self._on_storage_type_changed)
        self.radio_file.toggled.connect(self._on_storage_type_changed)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.button_box = button_box
        self.setLayout(layout)

        self._on_storage_type_changed()

    def validate(self):

        v = True
        path = self.destinationPath()
        v &= path is None or (isinstance(path, str) and len(path) > 0)

        self.button_box.button(QDialogButtonBox.Ok).setEnabled(v)

    def _on_storage_type_changed(self):
        """Enable/disable file selection based on storage type."""
        is_file = self.radio_file.isChecked()
        self.file_widget.setEnabled(is_file)
        # self.file_path.setEnabled(is_file)
        # self.browse_button.setEnabled(is_file)
        self._storage_in_memory = not is_file
        self.validate()

    def _browse_file(self):
        """Open file dialog to select output file."""

        from qgis.gui import QgsFileWidget

        w = QgsFileWidget(self)
        w.setDialogTitle('Create empty spectral library')
        w.setFilter('GeoPackage (*.gpkg);;GeoJSON (*.geojson)')
        if w.exec_() == QDialog.Accepted:
            s = ""
        file_path, tmp = QFileDialog.getSaveFileName(
            self,
            "Save Spectral Library",
            "",
            "GeoPackage (*.gpkg);;GeoJSON (*.geojson)"
        )
        if file_path:
            self.file_path.setText(file_path)
            self._file_path = file_path

        self.validate()

    def fieldNames(self) -> List[str]:
        """
        Returns a list of profile field names from user input.

        Returns:
            list: List of field names, empty list if no input.
        """
        text = self.field_input.text().strip()
        fields = [n.strip() for n in text.split(',')]

        names = []
        for n in fields:
            if n not in names:
                names.append(n)
        return names

    def layerName(self) -> str:
        """
        Returns the layer name from user input.

        Returns:
            str: Layer name.
        """
        return self.layer_name.text().strip()

    def destinationPath(self) -> Optional[str]:
        """
        Returns:
            str or None: File path or None if memory storage is selected.
        """
        if self.radio_memory.isChecked():
            return None
        else:
            # return self.file_path.text().strip()
            return self.file_widget.filePath()

    def create_speclib(self) -> QgsVectorLayer:

        profile_fields = self.fieldNames()
        path = self.destinationPath()
        layer_name = self.layerName()
        sl = SpectralLibraryUtils.createSpectralLibrary(profile_fields=profile_fields, name=layer_name)
        if path:
            ext = os.path.splitext(path)[1].lower()
            options = QgsVectorFileWriter.SaveVectorOptions()
            driver = QgsVectorFileWriter.driverForExtension(ext)
            dst_fields = GenericFieldValueConverter.compatibleTargetFields(sl.fields(), driver)

            if driver == 'GeoJSON':
                # add dummy profiles
                with edit(sl):
                    feat = QgsFeature(sl.fields())
                    sl.addFeature(feat)

            options.fieldValueConverter = GenericFieldValueConverter(sl.fields(), dst_fields)
            options.driverName = driver
            options.layerName = layer_name
            r, errMsg, newPath, newLayer = QgsVectorFileWriter.writeAsVectorFormatV3(
                sl,
                path,
                QgsProject.instance().transformContext(),
                options
            )

            if not r == QgsVectorFileWriter.NoError:
                raise Exception(f'Unable to create {path}\n{errMsg}')

            slNew = QgsVectorLayer(newPath, layer_name)
            slNew.loadDefaultStyle()
            SpectralLibraryUtils.copyEditorWidgetSetup(slNew, sl)
            slNew.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)
            sl = slNew

        CreateSpectralLibraryDialog.LAST_LAYER_NAME = layer_name
        CreateSpectralLibraryDialog.LAST_FILE_PATH = path
        CreateSpectralLibraryDialog.LAST_PROFILE_FIELDS = profile_fields
        return sl
