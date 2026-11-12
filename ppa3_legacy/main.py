from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.neighbors import KNeighborsClassifier

import performance


data_folder = Path(__file__).resolve().parent


def extract_features(X):
    if X.ndim != 3 or X.shape[1:] != (5, 2):  # make sure each face has five landmarks
        raise ValueError("expected X with shape (num_samples, 5, 2).")

    features = []
    for landmarks in X:  # go through each face in the dataset
        distances = []
        for i in range(landmarks.shape[0]):
            for j in range(landmarks.shape[0]):
                p1, p2 = landmarks[i], landmarks[j]
                distance = np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
                distances.append(distance)  # save the distance between two landmarks
        features.append(distances)

    return np.array(features, dtype=float)  # return the 25 distances for each face


def main():
    X = np.load(data_folder / "X-5-Caltech.npy", allow_pickle=False)  # load the caltech landmarks
    y = np.load(data_folder / "y-5-Caltech.npy", allow_pickle=False)  # load the identity labels

    if len(X) != len(y):
        raise ValueError("X and y must have the same number of samples.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.33, random_state=42, stratify=y  # keep 33% for testing
    )

    train_features = extract_features(X_train)  # get features from training faces
    clf = OneVsRestClassifier(KNeighborsClassifier())  # one binary knn classifier per identity
    clf.fit(train_features, y_train)  # train using the template data

    test_features = extract_features(X_test)  # get features from testing faces
    matching_scores = clf.predict_proba(test_features)  # get matching probabilities

    gen_scores = []
    imp_scores = []
    for query_num, actual_label in enumerate(y_test):
        for class_num, class_label in enumerate(clf.classes_):
            score = matching_scores[query_num, class_num]
            if actual_label == class_label:
                gen_scores.append(score)
            else:
                imp_scores.append(score)

    gen_scores = np.array(gen_scores)  # scores for correct identity matches
    imp_scores = np.array(imp_scores)  # scores for all other identities

    print("Caltech 5-landmark biometric authentication — PPA #3")
    print(f"Total samples: {len(X)}, identities: {len(clf.classes_)}")
    print(f"Training templates: {len(X_train)}; testing queries: {len(X_test)} (33%)")
    print(f"Extracted feature shape: {train_features.shape} (25 distances per face)")
    print(f"Matching probability matrix: {matching_scores.shape}")
    print(f"Genuine scores: {len(gen_scores)}; impostor scores: {len(imp_scores)}")

    results = performance.evaluate(gen_scores, imp_scores)  # create the three hw3 plots
    print(f"ROC AUC: {results['auc']:.4f}")
    print(f"Equal Error Rate: {results['eer']:.4f}")
    print(f"d-prime: {results['d_prime']:.4f}")
    print(f"Plots saved to: {results['plot_dir']}")


if __name__ == "__main__":
    main()