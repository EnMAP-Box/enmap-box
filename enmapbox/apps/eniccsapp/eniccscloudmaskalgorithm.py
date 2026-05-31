import contextlib
import os
from typing import Any, Dict, List, Tuple

from qgis._core import QgsProcessingParameterFile
from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputRasterLayer
)
try:
    from eniccs import run_eniccs
except ImportError:
    run_eniccs = None

from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm

# for routing eniccs prints back to gui if verbose=True
class _FeedbackStream:
    def __init__(self, feedback: QgsProcessingFeedback):
        self._feedback = feedback

    def write(self, msg: str):
        msg = msg.rstrip()
        if msg:
            self._feedback.pushInfo(msg)

    def flush(self):
        pass


@typechecked
class EniccsCloudMaskAlgorithm(EnMAPProcessingAlgorithm):
    P_PRODUCT, _PRODUCT = 'product', 'EnMAP L2A product folder (single tile)'
    P_OUTPUT_DIR, _OUTPUT_DIR = 'outputDir', 'Output folder'
    P_AUTO_OPTIMIZE, _AUTO_OPTIMIZE = 'autoOptimize', 'Auto optimize'
    P_SMOOTH, _SMOOTH = 'smoothOutput', 'Smooth output'
    P_VERBOSE, _VERBOSE = 'verbose', 'Verbose (print progress to log)'
    P_CONTAMINATION, _CONTAMINATION = 'contamination', 'Contamination'
    P_PERCENTILE, _PERCENTILE = 'percentile', 'Percentile'
    P_SAMPLES, _SAMPLES = 'samples', 'Samples'
    P_BUFFER, _BUFFER = 'buffer', 'Buffer'
    P_N_JOBS, _N_JOBS = 'nJobs', 'Number of parallel jobs'
    P_OUTPUT_CLOUD, _OUTPUT_CLOUD = 'outputCloud', 'EnICCS cloud mask'
    P_OUTPUT_SHADOW, _OUTPUT_SHADOW = 'outputCloudShadow', 'EnICCS cloud shadow mask'

    def displayName(self) -> str:
        return 'EnICCS - EnMAPs Improved Cloud and Cloud Shadows (L2A)'

    def shortDescription(self) -> str:
        return ('EnICCS - a tool for generating improved EnMAP L2A cloud and cloud shadow masks. '
                'Currently optimized for densely vegetated surfaces (tropics). '
                'See https://github.com/leleist/eniccs for more details. ')

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._PRODUCT, 'Path to EnMAP L2A data directory. (one single tile)'),
            (self._OUTPUT_DIR, 'Optional output folder for the generated masks. If left empty, '
                               'masks are written into the input product folder.'),
            (self._AUTO_OPTIMIZE, 'Optimize the number of latent variables for PLS-DA '
                                  'automatically. Possibly better fit, much slower.'),
            (self._SMOOTH, 'Apply conservative morphological processing for smoothing the output masks.'),
            (self._VERBOSE, 'Print EnICCS progress messages into the processing log panel. '
                            'Includes model accuracy.'),
            (self._CONTAMINATION, 'Contamination parameter for "local outlier factor (LOF)" '
                                  'outlier detection. Is used to ensure clean training data. '
                                  'Not related to the perceived cloud contamination of the image. '),
            (self._PERCENTILE, 'Percentile for cloud-to-shadow matching routine distance '
                               'threshold. High percentile for heterogeneous cloud height.'),
            (self._SAMPLES, 'Number of samples for PLS-DA training. Sample counts as low as 200 '
                            'can suffice. Heterogeneous surface -> more samples.'),
            (self._BUFFER, 'Buffer size for smoothing (dilation) of CCS mask outputs.'),
            (self._N_JOBS, 'Number of parallel jobs (-1 = all cores). Only used when Auto '
                           'optimize is enabled.'),
        ]

    def group(self):
        return 'Pre-Processing'

    def groupId(self):
        return 'PreProcessing'

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(
            self.P_PRODUCT, self._PRODUCT, behavior=QgsProcessingParameterFile.Behavior.Folder)
        self.addParameterFile(
            self.P_OUTPUT_DIR, self._OUTPUT_DIR,
            behavior=QgsProcessingParameterFile.Behavior.Folder,
            optional=True)
        self.addParameterBoolean(self.P_AUTO_OPTIMIZE, self._AUTO_OPTIMIZE, defaultValue=False, advanced=True)
        self.addParameterBoolean(self.P_SMOOTH, self._SMOOTH, defaultValue=True, advanced=True)
        self.addParameterBoolean(self.P_VERBOSE, self._VERBOSE, defaultValue=False, advanced=True)
        self.addParameterFloat(self.P_CONTAMINATION, self._CONTAMINATION, defaultValue=0.25, advanced=True)
        self.addParameterInt(self.P_PERCENTILE, self._PERCENTILE, defaultValue=85, advanced=True)
        self.addParameterInt(self.P_SAMPLES, self._SAMPLES, defaultValue=3000, advanced=True)
        self.addParameterInt(self.P_BUFFER, self._BUFFER, defaultValue=1, advanced=True)
        self.addParameterInt(self.P_N_JOBS, self._N_JOBS, defaultValue=-1, advanced=True)

        self.addOutput(QgsProcessingOutputRasterLayer(self.P_OUTPUT_CLOUD, self._OUTPUT_CLOUD))
        self.addOutput(QgsProcessingOutputRasterLayer(self.P_OUTPUT_SHADOW, self._OUTPUT_SHADOW))

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        if run_eniccs is None:
            raise QgsProcessingException(
                'The eniccs package is not installed. '
                'Install it with: pip install eniccs'
            )

        folder = self.parameterAsFile(parameters, self.P_PRODUCT, context) # fallback for out_dir
        output_dir = self.parameterAsFile(parameters, self.P_OUTPUT_DIR, context) or folder
        auto_optimize = self.parameterAsBoolean(parameters, self.P_AUTO_OPTIMIZE, context)
        smooth = self.parameterAsBoolean(parameters, self.P_SMOOTH, context)
        verbose = self.parameterAsBoolean(parameters, self.P_VERBOSE, context)
        contamination = self.parameterAsFloat(parameters, self.P_CONTAMINATION, context)
        percentile = self.parameterAsInt(parameters, self.P_PERCENTILE, context)
        samples = self.parameterAsInt(parameters, self.P_SAMPLES, context)
        buffer = self.parameterAsInt(parameters, self.P_BUFFER, context)
        n_jobs = self.parameterAsInt(parameters, self.P_N_JOBS, context)

        stdout_redirect = (
            contextlib.redirect_stdout(_FeedbackStream(feedback)) if verbose
            else contextlib.nullcontext()
        )

        try:
            with stdout_redirect:
                mask_obj = run_eniccs(
                    dir_path=folder,
                    output_dir=output_dir,
                    save_output=True,
                    return_mask_obj=True,
                    auto_optimize=auto_optimize,
                    verbose=verbose,
                    plot=False, # hardcoded. unavaiable in enmapbox.
                    smooth_output=smooth,
                    contamination=contamination,
                    percentile=percentile,
                    num_samples=samples,
                    buffer_size=buffer,
                    n_jobs=n_jobs,
                )
        except (FileNotFoundError, ValueError) as e:  # user-actionable errors have clean
            # messages in eniccs.
            raise QgsProcessingException(str(e))
        except Exception as e: # all others
            import traceback
            for line in traceback.format_exc().splitlines():
                feedback.reportError(line)
            raise QgsProcessingException(f'EnICCS failed: {e}')

        # securely find filepath even if other *EnICCS.. files are present in output_dir
        cloud_path = os.path.join(output_dir, f'{mask_obj.datatake_name}_EnICCS_CLOUD.tif')
        shadow_path = os.path.join(output_dir, f'{mask_obj.datatake_name}_EnICCS_CLOUDSHADOW.tif')
        if not os.path.exists(cloud_path) or not os.path.exists(shadow_path):
            raise QgsProcessingException(
                f'EnICCS finished but expected output rasters were not found in {output_dir}.'
            )

        return {
            self.P_OUTPUT_CLOUD: cloud_path,
            self.P_OUTPUT_SHADOW: shadow_path,
        }
