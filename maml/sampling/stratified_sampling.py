from __future__ import annotations

import warnings

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


class SelectKFromClusters(BaseEstimator, TransformerMixin):
    def __init__(self, k: int = 1, allow_duplicate=False):
        """
        Args:
            k: Select k structures from each cluster.
            allow_duplicate: Whether structures are allowed to be
                selected over once.
        """
        self.k = k
        self.allow_duplicate = allow_duplicate

    def fit(self, X, y=None):
        return self

    def transform(self, clustering_data: dict):
        if any(key not in clustering_data.keys() for key in ["labels", "PCAfeatures"]):
            raise Exception(
                "The data returned by clustering step should at least provide label and feature information."
            )
        if "label_centers" not in clustering_data.keys():
            warnings.warn(
                "Centroid location is not provided, so random selection from each cluster will be performed, "
                "which will likely still significantly outperform manual sampling in terms of feature coverage. "
            )

        selected_indexes = []
        for label in set(clustering_data["labels"]):
            indexes_same_label = np.where(label == clustering_data["labels"])[0]
            features_same_label = clustering_data["PCAfeatures"][indexes_same_label]
            n_same_label = len(features_same_label)
            if "label_centers" in clustering_data:
                center_same_label = clustering_data["label_centers"][label]
                distance_to_center = np.sqrt(np.sum((features_same_label - center_same_label) ** 2, axis=1)).reshape(
                    len(indexes_same_label), 1
                )
                select_k_indexes = [int(i) for i in np.linspace(0, n_same_label - 1, self.k)]
                selected_indexes.extend(
                    indexes_same_label[
                        np.argpartition(distance_to_center.sum(axis=1), select_k_indexes)[select_k_indexes]
                    ]
                )
            else:
                selected_indexes.extend(indexes_same_label[np.random.randint(n_same_label, size=self.k)])
        n_duplicate = len(selected_indexes) - len(set(selected_indexes))
        if not self.allow_duplicate and n_duplicate > 0:
            selected_indexes = list(set(selected_indexes))
        elif self.allow_duplicate and n_duplicate > 0:
            warnings.warn(f"There are {n_duplicate} duplicated selections.")
        print(f"Finally selected {len(selected_indexes)} configurations.")
        return {
            "PCAfeatures": clustering_data["PCAfeatures"],
            "selected_indexes": selected_indexes,
        }
