"""
Clustering methods to learn a brain parcellation from fMRI
==========================================================

We use spatially-constrained Ward-clustering, KMeans and Recursive Neighbor
Agglomeration (ReNA) to create a set of parcels.

In a high dimensional regime, these methods can be interesting
to create a 'compressed' representation of the data, replacing the data
in the fMRI images by mean signals on the parcellation, which can
subsequently be used for statistical analysis or machine learning.

Also, these methods can be used to learn functional connectomes
and subsequently for classification tasks.

References
----------

Which clustering method to use, an empirical comparison can be found in this
paper

    * Bertrand Thirion, Gael Varoquaux, Elvis Dohmatob, Jean-Baptiste Poline.
      `Which fMRI clustering gives good brain parcellations ?
      <https://doi.org/10.3389/fnins.2014.00167>`_ Frontiers in Neuroscience,
      2014.

This parcellation may be useful in a supervised learning, see for
instance

    * Vincent Michel, Alexandre Gramfort, Gael Varoquaux, Evelyn Eger,
      Christine Keribin, Bertrand Thirion. `A supervised clustering approach
      for fMRI-based inference of brain states.
      <http://dx.doi.org/10.1016/j.patcog.2011.04.006>`_.
      Pattern Recognition, Elsevier, 2011.

More about ReNA clustering algorithm in the original paper

    * A. Hoyos-Idrobo, G. Varoquaux, J. Kahn and B. Thirion, "Recursive
      Nearest Agglomeration (ReNA): Fast Clustering for Approximation of
      Structured Signals," in IEEE Transactions on Pattern Analysis and
      Machine Intelligence, vol. 41, no. 3, pp. 669-681, 1 March 2019.
      https://hal.archives-ouvertes.fr/hal-01366651/

The big picture discussion corresponding to this example can be found
in the documentation section :ref:`parcellating_brain`.
"""

########################################################################
# Download a brain development fmri dataset and turn it to a data matrix
# -----------------------------------------------------------------------
#
# We download one subject of the movie watching dataset from Internet

from nilearn import datasets
dataset = datasets.fetch_development_fmri(n_subjects=1)

# print basic information on the dataset
print('First subject functional nifti image (4D) is at: %s' %
      dataset.func[0])  # 4D data


#########################################################################
# Brain parcellations with Ward Clustering
# ----------------------------------------
#
# Transforming list of images to data matrix and build brain parcellations,
# all can be done at once using `Parcellations` object.

from nilearn.regions import Parcellations

# Computing ward for the first time, will be long... This can be seen by
# measuring using time
import time
start = time.time()

# Agglomerative Clustering: ward

# We build parameters of our own for this object. Parameters related to
# masking, caching and defining number of clusters and specific parcellations
# method.
ward = Parcellations(method='ward', n_parcels=1000,
                     standardize=False, smoothing_fwhm=2.,
                     memory='nilearn_cache', memory_level=1,
                     verbose=1)
# Call fit on functional dataset: single subject (less samples).
ward.fit(dataset.func)
print("Ward agglomeration 1000 clusters: %.2fs" % (time.time() - start))

# We compute now ward clustering with 2000 clusters and compare
# time with 1000 clusters. To see the benefits of caching for second time.

# We initialize class again with n_parcels=2000 this time.
start = time.time()
ward = Parcellations(method='ward', n_parcels=2000,
                     standardize=False, smoothing_fwhm=2.,
                     memory='nilearn_cache', memory_level=1,
                     verbose=1)
ward.fit(dataset.func)
print("Ward agglomeration 2000 clusters: %.2fs" % (time.time() - start))

###########################################################################
# Visualize: Brain parcellations (Ward)
# -------------------------------------
#
# First, we display the parcellations of the brain image stored in attribute
# `labels_img_`
ward_labels_img = ward.labels_img_

# Now, ward_labels_img are Nifti1Image object, it can be saved to file
# with the following code:
ward_labels_img.to_filename('ward_parcellation.nii.gz')

from nilearn import plotting
from nilearn.image import mean_img, index_img

first_plot = plotting.plot_roi(ward_labels_img, title="Ward parcellation",
                               display_mode='xz')

# Grab cut coordinates from this plot to use as a common for all plots
cut_coords = first_plot.cut_coords

###########################################################################
# Compressed representation of Ward clustering
# --------------------------------------------
#
# Second, we illustrate the effect that the clustering has on the signal.
# We show the original data, and the approximation provided by the
# clustering by averaging the signal on each parcel.

# Grab number of voxels from attribute mask image (mask_img_).
import numpy as np
original_voxels = np.sum(ward.mask_img_.get_data())

# Compute mean over time on the functional image to use the mean
# image for compressed representation comparisons
mean_func_img = mean_img(dataset.func[0])

# Compute common vmin and vmax
vmin = np.min(mean_func_img.get_data())
vmax = np.max(mean_func_img.get_data())

plotting.plot_epi(mean_func_img, cut_coords=cut_coords,
                  title='Original (%i voxels)' % original_voxels,
                  vmax=vmax, vmin=vmin, display_mode='xz')

# A reduced dataset can be created by taking the parcel-level average:
# Note that Parcellation objects with any method have the opportunity to
# use a `transform` call that modifies input features. Here it reduces their
# dimension. Note that we `fit` before calling a `transform` so that average
# signals can be created on the brain parcellations with fit call.
fmri_reduced = ward.transform(dataset.func)

# Display the corresponding data compressed using the parcellation using
# parcels=2000.
fmri_compressed = ward.inverse_transform(fmri_reduced)

plotting.plot_epi(index_img(fmri_compressed, 0),
                  cut_coords=cut_coords,
                  title='Ward compressed representation (2000 parcels)',
                  vmin=vmin, vmax=vmax, display_mode='xz')
# As you can see below, this approximation is almost good, although there
# are only 2000 parcels, instead of the original 60000 voxels

#########################################################################
# Brain parcellations with KMeans Clustering
# ------------------------------------------
#
# We use the same approach as with building parcellations using Ward
# clustering. But, in the range of a small number of clusters,
# it is most likely that we want to use standardization. Indeed with
# standardization and smoothing, the clusters will form as regions.

# class/functions can be used here as they are already imported above.

# This object uses method='kmeans' for KMeans clustering with 10mm smoothing
# and standardization ON
start = time.time()
kmeans = Parcellations(method='kmeans', n_parcels=2000,
                       standardize=True, smoothing_fwhm=10.,
                       memory='nilearn_cache', memory_level=1,
                       verbose=1)
# Call fit on functional dataset: single subject (less samples)
kmeans.fit(dataset.func)

###########################################################################
# Visualize: Brain parcellations (KMeans)
# ---------------------------------------
#
# Grab parcellations of brain image stored in attribute `labels_img_`
kmeans_labels_img = kmeans.labels_img_

plotting.plot_roi(kmeans_labels_img, mean_func_img,
                  title="KMeans parcellation",
                  display_mode='xz')

# kmeans_labels_img is a Nifti1Image object, it can be saved to file with
# the following code:
kmeans_labels_img.to_filename('kmeans_parcellation.nii.gz')

##################################################################
# Brain parcellations with ReNA Clustering
# ----------------------------------------
# The spatial constraints are implemented inside the ReNA object.
#
# We use caching. As a result, the clustering doesn't have
# to be recomputed later.
from nilearn.connectome import ReNA
start = time.time()
rena = ReNA(scaling=True, n_clusters=1000, memory='nilearn_cache')

rena.fit_transform(dataset.func[0])
print("ReNA 1000 clusters: %.2fs" % (time.time() - start))

start = time.time()
rena = ReNA(scaling=True, n_clusters=2000, memory='nilearn_cache')

rena.fit_transform(dataset.func[0])
print("ReNA 2000 clusters: %.2fs" % (time.time() - start))

# We notice that, at the first computation (without using precomputed data),
# for 1000 clusters, the computation time is almost divided by 2 comparing to
# Ward clustering. This is due to the interesting algorithmic properties of
# ReNA. In some cases (higher number of voxels), this reduction in time
# computation can be much more significant.

##################################################################
# Visualize: Brain parcellations (ReNA)
# -------------------------------------
#
# First we display the labels of the clustering in the brain.
#
# To visualize results, we need to transform the clustering's labels back
# to a neuroimaging volume. For this, we use the NiftiMasker's
# inverse_transform method.

# Avoid 0 label
labels = rena.labels_
# Shuffling the labels for visualization
permutation = np.random.permutation(np.unique(labels).shape[0])
labels = 1 + permutation[labels]
# Obtain the masker
nifti_masker = rena.masker_
# Unmask the labels
labels_img = nifti_masker.inverse_transform(labels)

##################################################################
# labels_img is a Nifti1Image object, it can be saved to file with the
# following code:
labels_img.to_filename('rena_parcellation.nii.gz')


from nilearn.image import mean_img

plotting.plot_roi(labels_img, mean_func_img, title="ReNA parcellation",
                  display_mode='xz')

# common cut coordinates for all plots
cut_coords = first_plot.cut_coords

##################################################################
# Compressed representation of ReNA clustering
# --------------------------------------------
#
# We illustrate the effect that the clustering has on the signal.
# We show the original data, and the approximation provided by
# the clustering by averaging the signal on each parcel.
#
# We can then compare the results with the compressed representation
# obtained with Ward.

# Display the original data
plotting.plot_epi(mean_func_img, cut_coords=cut_coords,
                  title='Original (%i voxels)' % original_voxels,
                  vmax=vmax, vmin=vmin, display_mode='xz')

# A reduced data can be created by taking the parcel-level average:
# Note that, as many scikit-learn objects, the ReNA object exposes
# a transform method that modifies input features. Here it reduces their
# dimension.
# However, the data are in one single large 4D image, we need to use
# index_img to do the split easily:
from nilearn.image import index_img
fmri_reduced_rena = rena.transform(index_img(dataset.func[0], 0))

# Display the corresponding data compression using the parcellation
compressed_img_rena = rena.inverse_transform(fmri_reduced_rena)

plotting.plot_epi(compressed_img_rena, cut_coords=cut_coords,
                  title='Ward compressed representation (2000 parcels)',
                  vmin=vmin, vmax=vmax, display_mode='xz')

# Even if the compressed signal is relatively close
# to the original signal, we can notice that Ward Clustering
# gives a slightly more accurate compressed representation.
# However, as said in the previous section, the computation time is
# reduced which could still make ReNA more relevant than Ward in
# some cases.
