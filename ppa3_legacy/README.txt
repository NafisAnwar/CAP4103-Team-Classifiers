CAP4103 - Mobile Biometrics
PPA #3: Development of the Project's Matching Module

HOW TO RUN
1. Keep main.py, performance.py, X-5-Caltech.npy, and y-5-Caltech.npy
   together in this folder.
2. Install dependencies if needed: pip install -r requirements.txt
3. Run: python main.py
4. The three updated charts are saved in the plots folder.

IMPLEMENTATION
- Loads original Caltech 5-landmark .npy files used in HW2.
- Splits raw samples into 67% training and 33% testing with
  train_test_split(test_size=0.33, stratify=y, random_state=42).
- extract_features() uses HW2's 25 ordered pairwise Euclidean distances
  per face (including self-distances).
- Fits OneVsRestClassifier(KNeighborsClassifier()) on training features.
- Uses predict_proba() on test features to get one matching score for
  each possible enrolled identity.
- For each test face, the probability assigned to its true identity is
  a genuine score; the remaining identities' scores are impostor scores.
- performance.py adapts the HW3 Evaluator to real scores and saves the
  Score Distribution, DET, and ROC curves as PNG files.

RESULTS FROM THE INCLUDED ORIGINAL CALTECH DATA
Dataset: 375 faces, 20 identities, 5 landmarks per face
Training: 251 faces; Testing: 124 faces
Feature shape: (251, 25) for training
Genuine comparisons: 124; Impostor comparisons: 2,356
ROC AUC: 0.7569
Approximate EER: 0.2612 (HW3's closest-threshold convention)
d-prime: 1.0973

These are baseline biometric matching results, not the same as multiclass
identification accuracy. Results are reproducible using the fixed split seed.

SUBMISSION FILES
main.py                   Matching pipeline
performance.py            Score evaluation and plotting (adapted from HW3)
X-5-Caltech.npy           Original Caltech facial landmarks
y-5-Caltech.npy           Corresponding identity labels
requirements.txt          Python package dependencies
plots/roc_curve.png       Receiver Operating Characteristic
plots/det_curve.png       Detection Error Tradeoff
plots/score_distribution_plot.png  Genuine/impostor score distributions
