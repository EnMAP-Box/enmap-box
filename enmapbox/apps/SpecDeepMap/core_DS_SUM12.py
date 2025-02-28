# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 11:46:35 2024

@author: leon-
"""

#
from qgis._core import QgsProcessingFeedback

# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 18:56:51 2024

@author: leon-
"""
from osgeo import gdal
import numpy as np
import glob
import pandas as pd
from tqdm import tqdm
from scipy.stats import wasserstein_distance
from collections import Counter
import os
import math


## set progress counter for two main loops


def set_progress_counter(num_permutations, file_paths, val_perc, test_perc, normalize):
    if normalize == False:
        progress_counter_total = num_permutations

    else:
        train_length = math.ceil(len(file_paths) * (1 - (val_perc + test_perc)))
        # Return the number of files found
        progress_counter_total = num_permutations + (
                train_length * 2)  # because one loop mean, one loop std if normalization is choosen

    return progress_counter_total


def identify_unique_classes(input_folder):
    # Path to the label images
    input_folder_f = fix_path(input_folder)
    paths = os.path.join(input_folder_f, 'labels/*.tif')
    file_paths = glob.glob(paths)

    # Set to store unique labels across all images
    unique_labels = set()

    # Loop through each file
    for path in tqdm(file_paths, desc="Processing label images"):
        try:
            # Open the image file
            dataset = gdal.Open(path)
            if dataset is None:
                raise ValueError(f"Could not read data from {path}")

            # Read data as an array
            labels = dataset.ReadAsArray()

            # Update the set of unique labels
            unique_labels.update(np.unique(labels))

            num_classes = len(unique_labels)
        except Exception as e:
            print(f"Error processing {path}: {str(e)}")

        return num_classes, unique_labels


### calculate equal data distribution across datasets

def read_label_images_and_create_histograms(input_folder, num_labels):
    paths = os.path.join(input_folder, 'labels/*.tif')
    file_paths = glob.glob(paths)
    label_histograms = []
    for path in tqdm(file_paths, desc="Reading label images"):
        labels = gdal.Open(path).ReadAsArray()
        # Adjust histogram to ignore label 0 and include only relevant labels
        histogram, _ = np.histogram(labels, bins=np.arange(1, num_labels + 2), range=(1, num_labels + 1))
        label_histograms.append(histogram)
    return np.array(label_histograms), file_paths


def find_best_split(label_histograms, num_permutations, train_perc, test_perc, val_perc, min_perc, random_seed,
                    progress_counter_total, feedback: QgsProcessingFeedback = None):
    num_files = len(label_histograms)  # Total number of images
    num_per_class = np.sum(label_histograms, axis=0)  # Sum of labels per class
    min_per_class = num_per_class * min_perc  # Minimum instances per class based on min_perc

    idx = np.arange(num_files)
    rng = np.random.default_rng(seed=random_seed)  # Random number generator with seed
    num_test = int(num_files * test_perc)  # Number of test images
    num_val = int(num_files * val_perc)
    num_train = int(num_files * train_perc)  # Number of validation images (cumulative with test)

    best_emd = np.inf
    best_perm = None  # To store the best permutation

    progress_counter = 0

    for _ in tqdm(range(num_permutations), desc="Evaluating permutations"):
        # for _ in range(num_permutations):
        progress_counter += 1
        progress = (progress_counter / progress_counter_total) * 100
        # print(progress)
        if isinstance(feedback, QgsProcessingFeedback):
            feedback.setProgress(progress)

            # Allow user to cancel the process
            if feedback.isCanceled():
                break
        perm = rng.permutation(idx)  # Random permutation of the dataset
        test_hist = np.sum(label_histograms[perm[:num_test]], axis=0)
        val_hist = np.sum(label_histograms[perm[num_test:num_test + num_val]], axis=0)
        train_hist = np.sum(label_histograms[perm[num_test + num_val:num_val + num_test + num_train]], axis=0)
        # Ensure counts are not less than the minimum required and the sums are not zero
        if np.any(test_hist < min_per_class) or np.any(train_hist < min_per_class) or np.any(val_hist < min_per_class):
            continue

        sum_test_hist = np.sum(test_hist).astype(float)
        sum_val_hist = np.sum(val_hist).astype(float)
        sum_train_hist = np.sum(train_hist).astype(float)

        if sum_test_hist == 0 or sum_val_hist == 0 or sum_train_hist == 0:
            continue

        test_hist = test_hist / sum_test_hist
        val_hist = val_hist / sum_val_hist
        train_hist = train_hist / sum_train_hist

        emd_test_train = wasserstein_distance(test_hist, train_hist)
        emd_val_train = wasserstein_distance(val_hist, train_hist)
        emd_test_val = wasserstein_distance(test_hist, val_hist)

        avg_emd = (emd_test_train + emd_val_train + emd_test_val) / 3

        if avg_emd < best_emd:
            best_emd = avg_emd
            best_perm = perm  # Store the best permutation

        # print('permute ', progress_counter)

    # Calculate percentages
    perc_train = (num_train / num_files) * 100
    perc_val = (num_val / num_files) * 100
    perc_test = (num_test / num_files) * 100

    b = f"Final dataset split: Training dataset: {num_train} images ({perc_train:.2f}%), Validation dataset: {num_val} images ({perc_val:.2f}%),Test dataset: {num_test} images ({perc_test:.2f}%)."

    return best_perm, num_train, num_test, num_val, progress_counter, progress_counter_total, b, feedback


### create csv for the datasets

def fix_path(path):
    return path.replace('\\', '/')


def replace_last_labels_with_images(file_paths):
    new_paths = []
    for f in file_paths:
        # Split path into two parts at the last occurrence of 'labels'
        new_path = f.rsplit('labels', 1)  # Split from the right
        # Rebuild path with 'images' replacing the last 'labels'
        new_paths.append('images'.join(new_path))
    return new_paths


def save_splits_to_csv(file_paths, best_perm, num_train, num_test, num_val, out_folder_path):
    # Convert file paths using the fix_path function before processing
    fixed_file_paths = [fix_path(path) for path in file_paths]

    # Extract paths based on the permutation indices
    test_files = [fixed_file_paths[i] for i in best_perm[:num_test]]
    val_files = [fixed_file_paths[i] for i in best_perm[num_test:num_val + num_test]]
    train_files = [fixed_file_paths[i] for i in best_perm[num_val + num_test: num_val + num_test + num_train]]

    test_images = replace_last_labels_with_images(test_files)
    val_images = replace_last_labels_with_images(val_files)
    train_images = replace_last_labels_with_images(train_files)

    # Create DataFrames with two columns: 'image' and 'mask'
    test_df = pd.DataFrame({'image': test_images, 'mask': test_files})
    val_df = pd.DataFrame({'image': val_images, 'mask': val_files})
    train_df = pd.DataFrame({'image': train_images, 'mask': train_files})

    # Write to CSV files

    test_csv_path = os.path.join(out_folder_path, 'test_files.csv')
    val_csv_path = os.path.join(out_folder_path, 'validation_files.csv')
    train_csv_path = os.path.join(out_folder_path, 'train_files.csv')

    # Save the DataFrames to CSV files
    test_df.to_csv(test_csv_path, index=False)
    val_df.to_csv(val_csv_path, index=False)
    train_df.to_csv(train_csv_path, index=False)

    print("CSV files have been saved successfully.")

    return test_csv_path, val_csv_path, train_csv_path


### create summary csv with distribution absolute count and counts in percentage, as well as class weights

def calculate_class_distribution_from_csv(csv_path):
    df = pd.read_csv(csv_path)
    label_image_paths = df['mask'].tolist()
    class_counts = Counter()

    for path in label_image_paths:
        dataset = gdal.Open(path)
        if dataset is None:
            continue
        band = dataset.GetRasterBand(1)
        image_array = band.ReadAsArray()
        class_counts.update(Counter(image_array.flatten()))

    # Remove the count for non-interest pixels (if class 0 is background)
    if 0 in class_counts:
        del class_counts[0]

    total_pixels = sum(class_counts.values())
    class_percentages = {cls: (count / total_pixels * 100) for cls, count in class_counts.items()}

    return class_counts, class_percentages


def calculate_class_weights_from_counts(class_counts):
    # Remove class '0' if present
    if 0 in class_counts:
        del class_counts[0]

    total_counts = sum(class_counts.values())
    class_weights = {cls: total_counts / count for cls, count in class_counts.items() if count > 0}

    # Normalize weights so that the sum of weights equals the number of classes
    num_classes = len(class_weights)
    norm_factor = num_classes / sum(class_weights.values())
    class_weights = {cls: weight * norm_factor for cls, weight in class_weights.items()}

    return class_weights


def create_summary_csv(train_csv, val_csv, test_csv, out_folder_path, scaler, zero_class_removed):
    train_counts, train_percentages = calculate_class_distribution_from_csv(train_csv)
    val_counts, val_percentages = calculate_class_distribution_from_csv(val_csv)
    test_counts, test_percentages = calculate_class_distribution_from_csv(test_csv)

    # Gather all classes seen in any dataset
    all_classes = sorted(set(train_counts.keys()) | set(val_counts.keys()) | set(test_counts.keys()))

    print('scaler', scaler)
    if scaler == 0:
        scaler_s = 'None'

    else:
        scaler_s = scaler
        # Create DataFrame with two columns

    class_weights_train = calculate_class_weights_from_counts(train_counts)

    data = []
    for cls in all_classes:
        data.append({
            'Class ID': int(cls),
            'Train Count': train_counts.get(cls, 0),
            'Train Percentage': round(train_percentages.get(cls, 0), 2),
            'Validation Count': val_counts.get(cls, 0),
            'Validation Percentage': round(val_percentages.get(cls, 0), 2),
            'Test Count': test_counts.get(cls, 0),
            'Test Percentage': round(test_percentages.get(cls, 0), 2),
            'Class Train Weight': round(class_weights_train.get(cls, 0), 4),
            'Scaler': scaler_s,
            'Ignored Background : Class Zero': zero_class_removed
        })

    summary_df = pd.DataFrame(data)
    summary_csv = os.path.join(out_folder_path, 'Summary_train_val.csv')
    summary_df.to_csv(summary_csv, index=False)


######Create additional Normalization Mean Std Normalizer, whcih ignores No-data value if no-data defined

def read_no_data_value(train_csv_path):
    df_train = pd.read_csv(train_csv_path)
    train_image_paths = df_train['image'].tolist()

    if not train_image_paths:
        print("No image paths provided.")
        return None

    first_image = gdal.Open(train_image_paths[0])
    if not first_image:
        print("Failed to open the first image.")
        return None

    first_band = first_image.GetRasterBand(1)
    no_data_value = first_band.GetNoDataValue()
    return no_data_value


def calculate_summed_statistics(train_csv_path, progress_counter, progress_counter_total, scaler,
                                no_data_value=None, feedback: QgsProcessingFeedback = None, ):
    df_train = pd.read_csv(train_csv_path)
    train_image_paths = df_train['image'].tolist()

    train_length = len(train_image_paths)
    print(train_length)

    summed_values_per_channel = None
    pixel_counts_per_channel = None
    bands = None

    progress_counter = progress_counter
    progress_counter_total = progress_counter_total

    # Process each image
    for path in train_image_paths:
        dataset = gdal.Open(path)
        progress_counter += 1
        progress = (progress_counter / progress_counter_total) * 100
        if isinstance(feedback, QgsProcessingFeedback):
            feedback.setProgress(progress)

            # Allow user to cancel the process
            if feedback.isCanceled():
                break

        if not dataset:
            continue

        bands = dataset.RasterCount

        if summed_values_per_channel is None:
            summed_values_per_channel = np.zeros(bands)
            pixel_counts_per_channel = np.zeros(bands)

        for b in range(1, bands + 1):
            band = dataset.GetRasterBand(b)
            image_array = band.ReadAsArray()

            if scaler != 0:
                image_array = image_array / scaler

            # Apply no_data_value mask if no_data_value is provided and valid
            if no_data_value is not None:
                valid_data_mask = image_array != no_data_value
                image_array = image_array[valid_data_mask]

            summed_values_per_channel[b - 1] += np.sum(image_array)
            pixel_counts_per_channel[b - 1] += image_array.size

    progress_counter1 = progress_counter

    global_mean = summed_values_per_channel / pixel_counts_per_channel
    squared_diffs_per_channel = np.zeros(bands)

    # Calculate squared differences for standard deviation
    for path in train_image_paths:
        dataset = gdal.Open(path)
        progress_counter1 += 1
        progress = (progress_counter1 / progress_counter_total) * 100
        # print(progress)
        if isinstance(feedback, QgsProcessingFeedback):
            feedback.setProgress(progress)

            # Allow user to cancel the process
            if feedback.isCanceled():
                break
        # print('std_loop', progress_counter1, 'progess total', progress_counter_total)

        for b in range(1, bands + 1):
            band = dataset.GetRasterBand(b)
            image_array = band.ReadAsArray()

            if scaler != 0:
                image_array = image_array / scaler

            if no_data_value is not None:
                valid_data_mask = image_array != no_data_value
                image_array = image_array[valid_data_mask]

            squared_diffs_per_channel[b - 1] += np.sum((image_array - global_mean[b - 1]) ** 2)

        # progress_counter =float(progress_counter)

    global_std = np.sqrt(squared_diffs_per_channel / pixel_counts_per_channel)

    band_numbers = list(range(1, bands + 1))

    if scaler != 0:
        norm_df = pd.DataFrame({
            'Band_Number': band_numbers,
            'std': global_std,
            'mean': global_mean,
            'std and mean already scaled by scaler': scaler
        })
    else:
        norm_df = pd.DataFrame({
            'Band_Number': band_numbers,
            'std': global_std,
            'mean': global_mean,
        })

    return norm_df


def save_normalized_band_data(train_csv_path, out_folder_path, progress_counter, progress_counter_total, scaler,
                              no_data_value=None, feedback: QgsProcessingFeedback = None):
    norm_df = calculate_summed_statistics(train_csv_path, progress_counter, progress_counter_total, scaler,
                                          no_data_value, feedback)
    norm_csv = os.path.join(out_folder_path, 'Normalize_Bands.csv')
    norm_df.to_csv(norm_csv, index=False)
    print(f"Summary saved to {norm_csv}")


def create_train_validation_csv_balance(input_folder, out_folder_path, train_int_perc, test_int_perc, val_int_perc,
                                        scaler,
                                        random_seed=42, datatyp_index=None, normalize=True,
                                        feedback: QgsProcessingFeedback = None, min_perc=0.01, num_permutations=10000):
    assert train_int_perc + val_int_perc + test_int_perc <= 100, "The sum of train, validation, and test percentages exceeds 100%. Reduce percentages number of datasets so sum is max 100%!"

    train_perc = train_int_perc / 100
    test_perc = test_int_perc / 100  ## orig 0.1
    val_perc = val_int_perc / 100

    print('scaler', scaler)
    # Make sure the folder path uses forward slashes
    folder_path = fix_path(input_folder)
    print(folder_path)
    print(out_folder_path)
    # Get the image files and fix the paths
    data_type_options = ['tif', 'jpg', 'jpeg', 'png']
    datatyp = data_type_options[datatyp_index]

    img_files = glob.glob(os.path.join(folder_path, 'images', f'*.{datatyp}'))

    num_classes, unique_labels = identify_unique_classes(folder_path)

    # default no zero class removed
    zero_class_removed = 'No'

    # Remove the label '0' if present, assuming it's the background or not relevant
    if 0 in unique_labels:
        zero_class_removed = 'Yes'
        unique_labels.remove(0)
        num_classes = len(unique_labels)

    label_histograms, file_paths = read_label_images_and_create_histograms(input_folder, num_labels=num_classes)
    progress_counter_total = set_progress_counter(num_permutations, file_paths, val_perc, test_perc, normalize)
    best_perm, num_train, num_test, num_val, progress_counter, progress_counter_total, b, feedback = find_best_split(
        label_histograms,
        num_permutations, train_perc,
        test_perc, val_perc,
        min_perc, random_seed,
        progress_counter_total, feedback)

    if best_perm is None:
        raise ValueError("No valid permutation found that meets minimum class count and non-zero sum requirements.")

    test_csv_path, val_csv_path, train_csv_path = save_splits_to_csv(file_paths, best_perm, num_train, num_test,
                                                                     num_val,
                                                                     out_folder_path)

    create_summary_csv(train_csv_path, val_csv_path, test_csv_path, out_folder_path, scaler, zero_class_removed)
    if normalize == True:
        no_data_value = read_no_data_value(train_csv_path)
        save_normalized_band_data(train_csv_path, out_folder_path, progress_counter, progress_counter_total, scaler,
                                  no_data_value, feedback)

    return b
