# What is EnSoMAP



EnSoMAP (EnMAP Soil Mapper) is a software interface developed at the GFZ Helmholtz Centre for Geosciences in Potsdam, Germany. It is a platform for soil mapping applications of hyperspectral imagery that allows easy implementation in the hyperspectral and non-hyperspectral communities and gives the choice of multiple algorithms for each soil parameter. The main motivation for the EnSoMAP development is to provide experts and non-expert users with a suite of tools that can be used for soil applications. The algorithms focus on the fully automatic generation of semi-quantitative soil maps for key soil parameters such as soil moisture, soil organic carbon, and soil minerals (iron oxides, clay minerals, carbonates). Additional soil analyses tools were implemented to allow e.g. the derivation of quantitative maps based on in-situ data sets.

In EnSoMAP you can:
* Map soil feature based on the consolidated algorithm.
* Generate soil masks to remove areas covered with vegetation/water
* Calibrate your data using field measurement.
* Validate your results using field measurement.

# EnSoMAP Structure

The EnSoMAP workflow, from ortho-rectified reflectance to soil attributes maps is schematically presented here:

1. EnSoMAP reduces the spectral range to the number of bands, which are suitable for any of the further analyses. Bands which do not provide meaningful values are excluded from the available band list.

2. The software selects spectrally soil dominated pixels and eliminates from the image all pixels which are not dominated by a soil signature. This is realized in EnSoMAP by masking and excluding water pixels and vegetation pixels, in both vital and dry condition. Water dominated pixels are excluded per default through the Normalised Difference Red Blue Index (NDRBI) as suggested by Carter (1991) and Zakaluk and Ranjan (2008), which simply uses the ratio of the difference and the sum between the red (660 nm by default) and blue band (460 nm by default). To mask the remaining non-soil pixels, EnSoMAP identifies vegetation dominated regions and excludes them from further processing. 

3. Finally, the EnSoMAP Soil Mapping module performs soil functions, and produces soil maps based on the spectrally soil dominant pixels, which remain from the soil masking procedure. The one-dimensional grey value maps can easily be imported and visualized in any image processing software. In total, for the six selected soil parameters, 12 algorithms are proposed (see Table) and 12 soil map files are created, plus the map file associated with the soil quality layer. Additionally, map files associated with the soil selection procedure (water map, NDVI map, nCAI map, soil dominant pixels map) are saved. Also, an EnSoMAP run report file can be uploaded.

# Soil Mapping Tools

In the following table we present the soil functions currently available in EnSoMAP in terms of algorithms proposed, required spectral coverage for each parameter, and estimated soil parameters:

Table 2.1:	Overview of EnSoMAP automatic soil functions for identification and semi-quantification. RI: Redness Index, SWIR FI: Short-Wave Infrared Fine Particles Index, NSMI: Normalised Soil Moisture Index, SMGM: Soil Moisture Gaussian Modelling.

| Soil Chromophores | Soil Algorithm                   | Spectral Reg. (nm) | Estimated Soil Parameters                                      |
| ----------------- |----------------------------------| ------------------ |----------------------------------------------------------------|
| **Clay Minerals**<br> Al-OH content | Clay index (SWIR FI)             | 2209, 2133, 2225 | Clay mineral content (Levin et al. 2007)                       |
|                   | Clay absorption depth            | 2120 – 2250 | Clay mineral content                                           |
| **Iron Oxides**<br> Fe2O3 content | Iron index (RI)                  | 477, 556, 693 | Hematite content (Madeira et al., 1997) (Matthieu et al., 1998) |
| | Iron absorption depth VIS        | 450 – 630 | Iron oxide content                                             |
| | Iron absorption depth NIR        | 750 – 1040 | Iron oxide content                                             |
| **Carbonates**<br>Mg-OH content | Carbonate absorp-tion depth SWIR | 2300 – 2400 | Carbonate content                                              |
|**Soil Moisture** | Moisture index (NSMI)            | 1800, 2119 | Soil moisture content (Haubrock et al. 2008a/b)                |
| | Gaussian modelling (SMGM         | ~1500 – 2500 | Soil moisture content (Whiting et al. 2004)                    |
| **Soil Organic Carbon** | Band analysis SOC 1              | 400 – 700 | Organic carbon content (Bartholomeus et al. 2008)              |
| | Band analysis SOC 2              | 400, 600 | Organic carbon content (Bartholomeus et al. 2008)              |
| | Band analysis SOC 3              | 2138 – 2209 | Organic carbon content (Bartholomeus et al. 2008)              |
| | Band analysis SOC 4              | 478 - 659 | Organic carbon content (Thaler et al. 2019)               |
|**Gypsum** | NDGI                             | |                                                                |

# Soil Analyses Tools
* **Calibration**: This option allows experienced users to perform fully quantitative mapping using input field data for calibration. This input data option allows to automatically generate fully quantitative soil property maps (soil property values with units) from the semi-quantificative maps (high-low values without units; EnSoMAP's automatic soil functions). Three methods are proposed. Either the users directly enter a field measurement file with name of field location, coordinates X,Y and absolute value of soil parameter, and EnSoMAP performs the calibration and delivers as output a quantitative soil map file, or the users select a spectral library result together with an absolute value of the soil parameter and EnSoMAP performs the calibration and delivers the gain and offsets for calibration, or the users give as input already calculated gains and offsets for calibration. 

* **Validation**: This option allows the users to extract the soil parameter values of individual points based on their geographic coordinates from the EnSoMAP output soil maps.

# References

Bartholomeus, H.M., Schaepman, M.E., Kooistra, L., Stevens, A., Hoogmoed, W.B., and Spaargaren, O.S.P. (2008), Spectral reflectance based indices for soil organic carbon quantification. Geoderma, 145, 28-36

Clark, R.N., Gallagher, A.J. and Swayze, G.A. (1990). Material Absorption Band Depth Map-ping of Imaging Spectrometer Data Using a Complete Band Shape Least-Squares Fit with Library Reference Spectra. In, Proceedings of the Second Airborne Visible/Infrared Imaging Spectrometer (AVIRIS) Workshop (pp. 176-186).

Haubrock, S.-N., Chabrillat, S., Lemmnitz, C. and Kaufmann, H. (2008a), Surface soil moisture quantification models from reflectance data under field conditions, Int. J. Remote Sensing, 29 (1): 3-29.

Haubrock, S.-N., Chabrillat, S., Kuhnert, M., Hostert, P. and Kaufmann, H. (2008b), Surface soil moisture quantification and validation based on hyperspectral data and field measurements, Journal of Applied Remote Sensing, Vol. 2, 023552

Levin, N., Kidron, G.J. and Ben-Dor, E. (2007), Surface properties of stabilizing coastal dunes: combining spectral and field analyses, Sedimentology, 54, 771-788.

Madeira, J., Bedidi, A., Cervelle, B., Pouget, M. and Flay, N. 1997. Visible spectrometric indices of hematite (Hm) and goethite (Gt) content in lateritic soils: the application of a Thematic Mapper (TM) image for soil-mapping in Brasilia, Brazil. Int. J. Remote Sens. 18(13): 2835-2852. 

Mathieu, R., Pouget, M., Cervelle, B. and Escadafal, R. 1998. Relationships between satellite-based radiometric indices simulated using laboratory reflectance data and typic soil color of an arid environment. Remote Sens. Environ. 66: 17-28. 

Thaler, E.A., Larsen, I.J., Yu, Q., 2019. A new index for remote sensing of soil organic carbon based solely on visible wavelengths. Soil Sci. Soc. Am. J. 83 (5), 1443–1450.

Whiting, M.L., Li, L., and Ustin, S.L. (2004), Predicting water content using Gaussian model on soil spectra, Remote Sensing of the Environment, 89, 535-552.
