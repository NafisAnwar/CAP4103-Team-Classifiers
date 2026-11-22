import numpy as np


class Evaluator:  # reuse the numerical evaluator from the submitted hw3 main.py
    def __init__(self, num_thresholds, genuine_scores, impostor_scores, plot_title, epsilon=1e-12):  # retain the original hw3 threshold-grid constructor and score populations
        self.num_thresholds = num_thresholds
        self.thresholds = np.linspace(-0.1, 1.1, num_thresholds)  # preserve the original homework threshold grid
        self.genuine_scores = genuine_scores
        self.impostor_scores = impostor_scores
        self.plot_title = plot_title
        self.epsilon = epsilon

    def get_dprime(self):  # calculate d-prime with the original homework formula
        x = abs(np.mean(self.genuine_scores) - np.mean(self.impostor_scores))  # distance between the genuine and impostor means
        y = np.sqrt((np.var(self.genuine_scores) + np.var(self.impostor_scores)) / 2)  # pooled population standard deviation
        return x / (y + self.epsilon)

    def get_EER(self, FPR, FNR):  # retain the original closest-rate approximation for homework comparison
        FPR = np.asarray(FPR)
        FNR = np.asarray(FNR)
        index = np.argmin(np.abs(FPR - FNR))  # original hw3 closest-rate approximation
        EER = (FPR[index] + FNR[index]) / 2
        EER_threshold = self.thresholds[index]
        return EER, EER_threshold

    def compute_rates(self):  # count genuine and impostor accept and reject decisions at every threshold
        FPR = []
        FNR = []
        TPR = []
        for threshold in self.thresholds:  # evaluate an accept decision for each supplied threshold
            TP = np.sum(self.genuine_scores >= threshold)  # correctly accepted genuine claims
            FN = np.sum(self.genuine_scores < threshold)  # incorrectly rejected genuine claims
            FP = np.sum(self.impostor_scores >= threshold)  # incorrectly accepted impostor claims
            TN = np.sum(self.impostor_scores < threshold)  # correctly rejected impostor claims
            fpr = FP / (FP + TN + self.epsilon)
            fnr = FN / (FN + TP + self.epsilon)
            tpr = TP / (TP + FN + self.epsilon)
            FPR.append(fpr)
            FNR.append(fnr)
            TPR.append(tpr)
        return FPR, FNR, TPR
