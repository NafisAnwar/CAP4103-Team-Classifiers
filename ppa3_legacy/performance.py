from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # save plots without opening a separate window
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import roc_auc_score


PLOT_DIR = Path(__file__).resolve().parent / "plots"


class Evaluator:
    def __init__(self, genuine_scores, impostor_scores, num_thresholds=500):
        self.genuine_scores = np.asarray(genuine_scores, dtype=float)
        self.impostor_scores = np.asarray(impostor_scores, dtype=float)
        self.thresholds = np.linspace(-0.1, 1.1, num_thresholds)  # same range as hw3

        if not self.genuine_scores.size or not self.impostor_scores.size:
            raise ValueError("Both genuine and impostor score lists must be nonempty.")
        if not np.all(np.isfinite(self.genuine_scores)) or not np.all(
            np.isfinite(self.impostor_scores)
        ):
            raise ValueError("Matching scores must be finite numbers.")

    def get_dprime(self):
        difference = abs(np.mean(self.genuine_scores) - np.mean(self.impostor_scores))
        pooled_std = np.sqrt(
            (np.var(self.genuine_scores) + np.var(self.impostor_scores)) / 2
        )
        return float(difference / (pooled_std + 1e-12))  # measure score separation

    def compute_rates(self):
        fpr, fnr, tpr = [], [], []
        for threshold in self.thresholds:
            tp = np.sum(self.genuine_scores >= threshold)  # genuine matches accepted
            fn = np.sum(self.genuine_scores < threshold)  # genuine matches rejected
            fp = np.sum(self.impostor_scores >= threshold)  # impostor matches accepted
            tn = np.sum(self.impostor_scores < threshold)  # impostor matches rejected
            fpr.append(fp / (fp + tn))  # false positive rate
            fnr.append(fn / (fn + tp))  # false negative rate
            tpr.append(tp / (tp + fn))  # true positive rate
        return np.asarray(fpr), np.asarray(fnr), np.asarray(tpr)

    def get_eer(self, fpr, fnr):
        index = int(np.argmin(np.abs(fpr - fnr)))  # find where both error rates are closest
        eer = float((fpr[index] + fnr[index]) / 2)  # average the two error rates
        return eer, float(self.thresholds[index]), index

    @staticmethod
    def save_plot(filename):
        PLOT_DIR.mkdir(parents=True, exist_ok=True)
        plt.savefig(PLOT_DIR / filename, dpi=300, bbox_inches="tight")
        plt.close()

    def plot_score_distribution(self):
        plt.figure(figsize=(8, 5.5))
        bins = np.linspace(0, 1, 31)  # use the same bins for both score groups
        plt.hist(
            self.genuine_scores, bins=bins, density=True, histtype="step",
            lw=2, color="green", label="Genuine scores"
        )
        plt.hist(
            self.impostor_scores, bins=bins, density=True, histtype="step",
            lw=2, color="red", label="Impostor scores"
        )
        plt.xlim(-0.05, 1.05)
        plt.xlabel("Matching probability")
        plt.ylabel("Probability density")
        plt.title("Score Distribution — Caltech (5 landmarks)\n"
                  f"d-prime = {self.get_dprime():.3f}")
        plt.legend()
        plt.grid(alpha=0.3)
        self.save_plot("score_distribution_plot.png")

    def plot_det_curve(self, fpr, fnr, eer, threshold, eer_index):
        plt.figure(figsize=(8, 5.5))
        plt.plot(fpr, fnr, color="black", lw=2, label="DET")
        plt.plot([0, 1], [0, 1], "--", color="gray", lw=1)
        plt.scatter([fpr[eer_index]], [fnr[eer_index]], color="darkorange",
                    zorder=3, label=f"Approx. EER = {eer:.3f}")
        plt.xlim(-0.05, 1.05)
        plt.ylim(-0.05, 1.05)
        plt.xlabel("False Positive Rate (FAR)")
        plt.ylabel("False Negative Rate (FRR)")
        plt.title("Detection Error Tradeoff — Caltech (5 landmarks)\n"
                  f"EER = {eer:.3f} at threshold = {threshold:.3f}")
        plt.legend()
        plt.grid(alpha=0.3)
        self.save_plot("det_curve.png")

    def plot_roc_curve(self, fpr, tpr, auc):
        plt.figure(figsize=(8, 5.5))
        plt.plot(fpr, tpr, color="black", lw=2, label=f"ROC (AUC = {auc:.3f})")
        plt.plot([0, 1], [0, 1], "--", color="gray", lw=1, label="Chance")
        plt.xlim(-0.05, 1.05)
        plt.ylim(-0.05, 1.05)
        plt.xlabel("False Positive Rate (FAR)")
        plt.ylabel("True Positive Rate (TAR)")
        plt.title("Receiver Operating Characteristic — Caltech (5 landmarks)")
        plt.legend(loc="lower right")
        plt.grid(alpha=0.3)
        self.save_plot("roc_curve.png")


def evaluate(gen_scores, imp_scores):
    evaluator = Evaluator(gen_scores, imp_scores)
    fpr, fnr, tpr = evaluator.compute_rates()
    eer, threshold, index = evaluator.get_eer(fpr, fnr)

    true_binary_labels = np.concatenate(
        [np.ones(len(gen_scores), dtype=int), np.zeros(len(imp_scores), dtype=int)]
    )
    all_scores = np.concatenate([gen_scores, imp_scores])
    auc = float(roc_auc_score(true_binary_labels, all_scores))  # calculate roc area

    evaluator.plot_score_distribution()
    evaluator.plot_det_curve(fpr, fnr, eer, threshold, index)
    evaluator.plot_roc_curve(fpr, tpr, auc)

    return {
        "auc": auc,
        "eer": eer,
        "d_prime": evaluator.get_dprime(),
        "plot_dir": PLOT_DIR,
    }