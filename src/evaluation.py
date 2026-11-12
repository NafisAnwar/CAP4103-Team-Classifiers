from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve
from src.files import write_csv, write_json


class Evaluator:
    def __init__(self, genuine_scores, impostor_scores, score_type='cosine_similarity_higher_is_better',
                 score_label='Cosine similarity (higher is better)'):
        if not isinstance(score_type, str) or not score_type.strip() or not isinstance(score_label, str) or not score_label.strip():
            raise ValueError('Score type and label must be nonempty strings')
        self.score_type, self.score_label = score_type, score_label #fusion callers can describe their own scale
        self.genuine_scores = np.asarray(genuine_scores, dtype=float)
        self.impostor_scores = np.asarray(impostor_scores, dtype=float)
        for values in [self.genuine_scores, self.impostor_scores]:
            if values.ndim != 1 or len(values) == 0 or not np.isfinite(values).all():
                raise ValueError('Genuine and impostor scores must be nonempty finite vectors')

    def get_dprime(self):
        difference = float(self.genuine_scores.mean() - self.impostor_scores.mean()) #keep the ppa3 pooled-variance definition
        pooled = np.sqrt((self.genuine_scores.var() + self.impostor_scores.var()) / 2)
        return float(abs(difference) / pooled) if pooled > 0 else 0.0 if difference == 0 else None

    def compute_rates(self):
        labels = np.r_[np.ones(len(self.genuine_scores)), np.zeros(len(self.impostor_scores))]
        scores = np.r_[self.genuine_scores, self.impostor_scores]
        fpr, tpr, thresholds = roc_curve(labels, scores, drop_intermediate=False) #keep every empirical threshold for the crossing
        return fpr, 1 - tpr, tpr, thresholds

    @staticmethod
    def get_eer(fpr, fnr):
        difference = fpr - fnr
        crossing = np.flatnonzero(difference >= 0)
        if not len(crossing):
            raise ValueError('ROC does not span the FAR/FRR crossing')
        index = int(crossing[0])
        if difference[index] == 0:
            return float(fpr[index])
        if index == 0:
            raise ValueError('Invalid ROC endpoints')
        weight = -difference[index - 1] / (difference[index] - difference[index - 1]) #interpolate between the two neighboring rates
        return float(fpr[index - 1] + weight * (fpr[index] - fpr[index - 1]))

    def metrics(self):
        labels = np.r_[np.ones(len(self.genuine_scores)), np.zeros(len(self.impostor_scores))]
        scores = np.r_[self.genuine_scores, self.impostor_scores]
        genuine_mean, impostor_mean = float(self.genuine_scores.mean()), float(self.impostor_scores.mean())
        fpr, fnr, _, _ = self.compute_rates()
        return {'auc': float(roc_auc_score(labels, scores)), 'eer': self.get_eer(fpr, fnr),
                'd_prime': self.get_dprime(), 'genuine_count': len(self.genuine_scores),
                'impostor_count': len(self.impostor_scores), 'genuine_mean': genuine_mean,
                'impostor_mean': impostor_mean,
                'score_direction_check': 'passed' if genuine_mean > impostor_mean else 'equal_means' if genuine_mean == impostor_mean else 'reversed_means',
                'eer_method': 'linear_interpolation_empirical_roc',
                'score_type': self.score_type}

    def export(self, metrics_dir, figures_dir, name):
        metrics_dir, figures_dir = Path(metrics_dir), Path(figures_dir)
        metrics_dir.mkdir(parents=True, exist_ok=True)
        figures_dir.mkdir(parents=True, exist_ok=True)
        metrics = self.metrics()
        fpr, fnr, tpr, thresholds = self.compute_rates()
        write_json(metrics_dir / f'{name}_metrics.json', metrics)
        write_csv(metrics_dir / f'{name}_rates.csv',
                  [{'threshold': threshold, 'far': far, 'frr': frr, 'tar': tar}
                   for threshold, far, frr, tar in zip(thresholds, fpr, fnr, tpr)])
        title = name.replace('_', ' ').title()
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(fpr, tpr, label=f'AUC = {metrics["auc"]:.4f}')
        ax.plot([0, 1], [0, 1], '--', color='gray')
        ax.set(xlabel='False accept rate', ylabel='True accept rate', title=title + ': ROC')
        ax.legend()
        fig.tight_layout()
        fig.savefig(figures_dir / f'{name}_roc.png', dpi=180)
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(fpr, fnr, label=f'EER = {100 * metrics["eer"]:.2f}%')
        ax.plot([0, 1], [0, 1], '--', color='gray')
        ax.set(xlabel='False accept rate', ylabel='False reject rate', title=title + ': FAR/FRR tradeoff')
        ax.legend()
        fig.tight_layout()
        fig.savefig(figures_dir / f'{name}_far_frr.png', dpi=180)
        plt.close(fig)
        low, high = min(self.genuine_scores.min(), self.impostor_scores.min()), max(self.genuine_scores.max(), self.impostor_scores.max())
        bins = np.linspace(low - 1e-6, high + 1e-6, 31)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(self.genuine_scores, bins=bins, density=True, histtype='step', label='Genuine')
        ax.hist(self.impostor_scores, bins=bins, density=True, histtype='step', label='Impostor')
        ax.set(xlabel=self.score_label, ylabel='Density', title=title + ': scores')
        ax.legend()
        fig.tight_layout()
        fig.savefig(figures_dir / f'{name}_scores.png', dpi=180)
        plt.close(fig)
        return metrics


def evaluate_labeled(scores, labels, **score_description):
    scores, labels = np.asarray(scores, dtype=float), np.asarray(labels)
    if scores.ndim != 1 or labels.shape != scores.shape or not np.isin(labels, [0, 1]).all():
        raise ValueError('Scores and binary labels need matching one-dimensional shapes')
    return Evaluator(scores[labels == 1], scores[labels == 0], **score_description) #all callers still use higher-is-better scores
