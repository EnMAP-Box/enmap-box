import webbrowser
from collections import defaultdict, OrderedDict
from os.path import basename
from typing import Dict, Any, List, Tuple

import numpy as np
from scipy.cluster import hierarchy
from scipy.stats import spearmanr

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.reportwriter import MultiReportWriter, HtmlReportWriter, CsvReportWriter
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class FeatureClusteringHierarchicalAlgorithm(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Dataset'
    P_NO_PLOT, _NO_PLOT = 'noPlot', 'Do not report plots'
    P_OPEN_REPORT, _OPEN_REPORT = 'openReport', 'Open output report in webbrowser after running algorithm'
    P_OUTPUT_REPORT, _OUTPUT_REPORT = 'outputHierarchicalFeatureClustering', 'Output report'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'Dataset pickle file with feature data X to be evaluated.'),
            (self._NO_PLOT, 'Skip the creation of plots, which can take a lot of time for large features sets.'),
            (self._OPEN_REPORT, self.ReportOpen),
            (self._OUTPUT_REPORT, self.ReportFileDestination)
        ]

    def displayName(self) -> str:
        return 'Hierarchical feature clustering'

    def shortDescription(self) -> str:
        return 'Evaluate feature multicollinearity by performing hierarchical/agglomerative clustering with ' \
               'Ward linkage using squared Spearman rank-order correlation as distance between features. ' \
               'The result report includes ' \
               'i) pairwise squared Spearman rank-order correlation matrix, ' \
               'ii) clustering dendrogram, ' \
               'iii) inter-cluster correlation distribution, ' \
               'iv) intra-cluster correlation distribution, and ' \
               'v) a clustering hierarchy table detailing selected cluster representatives for each ' \
               'cluster size n.\n' \
               'For further analysis, all relevant results are also stored as a JSON sidecar file next to the report.'

    def group(self):
        return Group.Test.value + Group.FeatureSelection.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_DATASET, self._DATASET, extension=self.PickleFileExtension)
        self.addParameterBoolean(self.P_NO_PLOT, self._NO_PLOT, False, False, True)
        self.addParameterBoolean(self.P_OPEN_REPORT, self._OPEN_REPORT, True)
        self.addParameterFileDestination(self.P_OUTPUT_REPORT, self._OUTPUT_REPORT, self.ReportFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:

        import matplotlib.pyplot as plt

        filenameDataset = self.parameterAsFile(parameters, self.P_DATASET, context)
        noPlot = self.parameterAsBoolean(parameters, self.P_NO_PLOT, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_REPORT, context)
        openReport = self.parameterAsBoolean(parameters, self.P_OPEN_REPORT, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            dump = Utils.pickleLoad(filenameDataset)
            X = dump['X']
            features = dump['features']
            feedback.pushInfo(f'Load feature data: X{list(X.shape)}')
            feedback.pushInfo('Performing hierarchical clustering')
            corr = spearmanr(X).correlation ** 2
            corr_linkage = hierarchy.ward(corr)
            corrCopy = corr.copy()
            np.fill_diagonal(corr, np.nan)

            feedback.pushInfo('Prepare results')

            # prepare results
            inter_cluster_correlation = list()
            intra_cluster_correlation = list()
            cluster_hierarchy = list()
            feature_subset_hierarchy = list()
            n = len(corr_linkage)
            for i, t in enumerate(reversed(corr_linkage[:, 2]), 1):
                feedback.setProgress(i / n * 100)

                # cluster hierarchy
                fcluster = hierarchy.fcluster(corr_linkage, t, criterion='distance')
                cluster_hierarchy.append(fcluster)

                # cluster representative
                cluster_id_to_feature_ids = defaultdict(list)
                for idx, cluster_id in enumerate(fcluster):
                    cluster_id_to_feature_ids[cluster_id].append(idx)
                selected_features = [v for v in cluster_id_to_feature_ids.values()]
                intra_cluster_corr = [list(np.nanmean(corr[v][:, v], axis=0)) for v in selected_features]
                featureSubset = [f[np.argmax(c)] for f, c in zip(selected_features, intra_cluster_corr)]
                feature_subset_hierarchy.append(featureSubset)

                # inter-cluster corr
                values = corr[featureSubset][:, featureSubset]
                inter_cluster_correlation.append(values[np.isfinite(values)])

                # intra-cluster corr
                values = list()
                for fs in selected_features:
                    corr_mean = np.nanmean(corr[fs][:, fs])
                    if np.isfinite(corr_mean):
                        values.append(corr_mean)
                intra_cluster_correlation.append(values)

            dumpJson = OrderedDict()
            dumpJson['features'] = features
            dumpJson['squared_spearmanr'] = corrCopy
            dumpJson['ward_linkage'] = corr_linkage
            dumpJson['cluster_hierarchy'] = cluster_hierarchy
            dumpJson['feature_subset_hierarchy'] = feature_subset_hierarchy
            dumpJson['inter_cluster_correlation'] = inter_cluster_correlation
            dumpJson['intra_cluster_correlation'] = intra_cluster_correlation
            Utils.jsonDump(dumpJson, filename + '.json')

            if not noPlot:
                feedback.pushInfo('Plot dendrogamm')
                figsizeX = len(features) * 0.15 + 5
                figsizeY = 10
                fig, ax = plt.subplots(figsize=(figsizeX, figsizeY))
                plt.title('Feature clustering dendrogram')
                dendro = hierarchy.dendrogram(
                    corr_linkage, orientation='bottom',
                    labels=features,
                    ax=ax, leaf_rotation=90, leaf_font_size=10
                )
                plt.ylabel('Ward inter-cluster distance')
                fig.tight_layout()
                filenameFig1 = filename + '.fig1.svg'
                fig.savefig(filenameFig1, format='svg')
                # mpld3.show(fig)
                # exit()

                feedback.pushInfo('Plot correlation matrix')
                figsizeX = len(features) * 0.15 + 5
                figsizeY = len(features) * 0.15 + 5
                fig, ax = plt.subplots(figsize=(figsizeX, figsizeY))
                plt.title('squared Spearman rank-order correlation matrix')
                dendro_idx = np.arange(0, len(dendro['ivl']))
                im = ax.imshow(corrCopy[dendro['leaves'], :][:, dendro['leaves']], cmap='jet')
                ax.set_xticks(dendro_idx)
                ax.set_yticks(dendro_idx)
                ax.set_xticklabels(dendro['ivl'], rotation='vertical')
                ax.set_yticklabels(dendro['ivl'])
                plt.xticks(fontsize=10)
                plt.yticks(fontsize=10)
                plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)  # the numbers here are quite magic, but do work :-)
                fig.tight_layout()
                filenameFig2 = filename + '.fig2.svg'
                fig.savefig(filenameFig2, format='svg')
                # mpld3.show(fig)
                # plt.show()
                # exit()

                feedback.pushInfo('Plot inter-cluster similarity')
                figsizeX = 10
                figsizeY = len(features) * 0.15 + 1
                fig, ax = plt.subplots(figsize=(figsizeX, figsizeY))
                plt.title('Inter-cluster correlation distribution')
                plt.xlabel('squared Spearman rank-order correlation')
                plt.ylabel('number of clusters')
                ax.boxplot(inter_cluster_correlation,
                           vert=False, sym='',
                           labels=[f'n={i + 1}' for i in range(len(features) - 1)],
                           )
                fig.tight_layout()
                filenameFig3 = filename + '.fig3.svg'
                fig.savefig(filenameFig3, format='svg')

                # plt.plot([3,1,4,1,5], 'ks-', mec='w', mew=5, ms=20)
                # mpld3.show(fig)
                # exit()

                feedback.pushInfo('Plot intra-cluster similarity')
                figsizeX = 10
                figsizeY = len(features) * 0.15 + 1
                fig, ax = plt.subplots(figsize=(figsizeX, figsizeY))
                plt.title('Intra-cluster correlation distribution')
                plt.xlabel('squared Spearman rank-order correlation')
                plt.ylabel('number of clusters')
                ax.boxplot(intra_cluster_correlation,
                           vert=False, sym='',
                           labels=[f'n={i + 1}' for i in range(len(features) - 1)],
                           )
                fig.tight_layout()
                filenameFig4 = filename + '.fig4.svg'
                fig.savefig(filenameFig4, format='svg')

            with \
                    open(filename, 'w') as fileHtml, \
                    open(filename + '.csv', 'w') as fileCsv:
                report = MultiReportWriter([HtmlReportWriter(fileHtml), CsvReportWriter(fileCsv)])
                report.writeHeader('Hierarchical feature clustering')
                linkWard = self.htmlLink(
                    'https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.ward.html',
                    'scipy.cluster.hierarchy.ward',
                )
                linkSpearmanr = self.htmlLink(
                    'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html',
                    'scipy.stats.spearmanr'
                )
                report.writeParagraph(f'Linkage methode: Ward (see {linkWard})')
                report.writeParagraph(f'Distance metric: squared Spearman rank-order correlation (see {linkSpearmanr})')
                if not noPlot:
                    report.writeImage(basename(filenameFig2))
                    report.writeImage(basename(filenameFig1))
                    report.writeImage(basename(filenameFig3))
                    report.writeImage(basename(filenameFig4))

                values = feature_subset_hierarchy
                rowHeaders = [f'n={i + 1}' for i, v in enumerate(feature_subset_hierarchy)]
                rowHeaders[0] = 'n=1'
                report.writeTable(
                    values,
                    'Selected features (zero-based indices)',
                    None,
                    rowHeaders,
                )

                report.writeParagraph(
                    f'Report design was inspired by {self.htmlLink("https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance_multicollinear.html#sphx-glr-auto-examples-inspection-plot-permutation-importance-multicollinear-py", "Permutation Importance with Multicollinear or Correlated Features")}.'
                )

            if openReport:
                webbrowser.open_new_tab(filename)

            result = {self.P_OUTPUT_REPORT: filename}

            self.toc(feedback, result)

        return result
