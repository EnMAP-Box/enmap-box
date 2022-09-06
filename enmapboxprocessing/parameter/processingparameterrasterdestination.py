from os.path import splitext

from qgis.core import QgsProcessingParameterRasterDestination, QgsProcessingParameters


class ProcessingParameterRasterDestination(QgsProcessingParameterRasterDestination):

    def __init__(
            self, name: str, description: str, defaultValue=None, optional=False, createByDefault=True,
            allowTif=True, allowEnvi=False, allowVrt=False
    ):
        super().__init__(name, description, defaultValue, optional, createByDefault)
        self.optional = optional
        self.allowTif = allowTif
        self.allowEnvi = allowEnvi
        self.allowVrt = allowVrt

    def clone(self):
        copy = ProcessingParameterRasterDestination(
            self.name(), self.description(), self.defaultValue(), self.optional, self.createByDefault(),
            self.allowTif, self.allowEnvi, self.allowVrt
        )
        copy.setFlags(self.flags())
        return copy

    def defaultFileExtension(self):
        if self.allowTif:
            return 'tif'
        if self.allowEnvi:
            return 'bsq'
        if self.allowVrt:
            return 'vrt'
        assert 0

    def createFileFilter(self):
        fileFilter = list()
        if self.allowTif:
            fileFilter.append('TIF files (*.tif)')
        if self.allowEnvi:
            fileFilter.append('ENVI BSQ files (*.bsq)')
            fileFilter.append('ENVI BIL files (*.bil)')
            fileFilter.append('ENVI BIP files (*.bip)')
        if self.allowVrt:
            fileFilter.append('VRT files (*.vrt)')

        return ';;'.join(fileFilter)

    def supportedOutputRasterLayerExtensions(self):
        extensions = list()
        if self.allowTif:
            extensions.append('tif')
        if self.allowEnvi:
            extensions.extend(['bsq', 'bil', 'bip'])
        if self.allowVrt:
            extensions.append('vrt')
        return extensions

    def parameterAsOutputLayer(self, definition, value, context):
        return super(QgsProcessingParameterRasterDestination, self).parameterAsOutputLayer(definition, value, context)

    def isSupportedOutputValue(self, value, context):
        output_path = QgsProcessingParameters.parameterAsOutputLayer(self, value, context)
        extensions = self.supportedOutputRasterLayerExtensions()
        extension = splitext(output_path)[1].lower().replace('.', '')
        if extension not in extensions:
            extensions = ', '.join([f'"{extension}"' for extension in extensions])
            message = f'unsupported file extension ({extension}), use {extensions} instead: {self.description()}'
            return False, message
        return True, ''
