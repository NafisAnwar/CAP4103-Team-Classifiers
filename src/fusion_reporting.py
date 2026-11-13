"""One evaluation convention for all three study conditions."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.evaluation import evaluate_labeled
from src.files import write_csv


def evaluate_conditions(rows, artifacts, condition, sigma):
    output = []
    for modality in ['face', 'palm', 'fusion']:
        field = 'fusion_score' if modality == 'fusion' else modality + '_score_raw'
        description = {'score_type': 'equal_weight_validation_zscore_fusion',
                       'score_label': 'Equal-weight normalized fusion score (higher is better)'} if modality == 'fusion' else {}
        evaluator = evaluate_labeled([float(r[field]) for r in rows],
                                     [int(r['is_genuine']) for r in rows], **description)
        metrics = evaluator.export(artifacts.metrics_dir, artifacts.figures_dir, f'{condition}_{modality}')
        output.append(dict(condition=condition, blur_sigma=sigma, modality=modality, **metrics))
    return output


def verify_metrics(rows, summary):
    for record in summary:
        m = record['modality']
        field = 'fusion_score' if m == 'fusion' else m + '_score_raw'
        actual = evaluate_labeled([float(r[field]) for r in rows], [int(r['is_genuine']) for r in rows]).metrics()
        for field in ['eer', 'auc', 'd_prime', 'genuine_count', 'impostor_count']:
            if actual[field] is None or record[field] is None:
                if actual[field] != record[field]:
                    raise ValueError('Exported metrics disagree')
            elif not np.isclose(float(actual[field]), float(record[field]), rtol=0, atol=1e-12):
                raise ValueError('Exported metrics disagree')


def comparison_plot(summary, path, title):
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    for ax, field, label in zip(axes, ['eer', 'auc', 'd_prime'], ['EER (%)', 'ROC AUC', "d-prime"]):
        for modality in ['face', 'palm', 'fusion']:
            selected = sorted([r for r in summary if r['modality'] == modality], key=lambda r: r['blur_sigma'])
            x = [r['blur_sigma'] for r in selected]
            y = [np.nan if r[field] is None else r[field] * (100 if field == 'eer' else 1) for r in selected]
            ax.plot(x, y, marker='o', label=modality.capitalize())
        ax.set(xlabel='Gaussian sigma (source pixels)', ylabel=label)
        ax.grid(alpha=.25)
    axes[0].legend()
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def rq2_comparison(summary, path):
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
    labels = [r['modality'].capitalize() for r in summary]
    for ax, field, label in zip(axes, ['eer','auc','d_prime'], ['EER (%)','ROC AUC','d-prime']):
        values = [r[field] * (100 if field == 'eer' else 1) for r in summary]
        ax.bar(labels, values, color=['#2463a6','#b77819','#198568'])
        for i, value in enumerate(values):
            ax.annotate(f'{value:.3f}', (i,value), xytext=(0,4), textcoords='offset points', ha='center',fontsize=9)
        ax.set_ylabel(label)
        ax.set_ylim(0, max(values)*1.18)
    fig.suptitle('RQ2: held-out scores, validation-fitted normalization')
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
