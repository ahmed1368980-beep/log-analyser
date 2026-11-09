import logging

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def _bar_chart(ax, data, title, xlabel, color):
    ax.set_title(title, fontsize=11, fontweight="bold")
    if not data:
        ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return
    labels = [str(row[0]) for row in data][::-1]   # inversé : le plus grand en haut
    values = [row[1] for row in data][::-1]
    ax.barh(labels, values, color=color)
    ax.set_xlabel(xlabel)
    for i, v in enumerate(values):
        ax.text(v, i, f" {v}", va="center", fontsize=9)


def show_dashboard(failed_country, success_user, failed_invalid):
    try:
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle("Analyse des logs d'authentification Linux", fontsize=14, fontweight="bold")

        _bar_chart(axes[0], failed_country, "Tentatives échouées par pays (top 10)",
                   "Nombre de tentatives", "tab:red")
        _bar_chart(axes[1], success_user, "Tentatives réussies par utilisateur (top 10)",
                   "Nombre de connexions", "tab:green")
        _bar_chart(axes[2], failed_invalid, "Échecs avec utilisateur invalide (top 10)",
                   "Nombre de tentatives", "tab:orange")

        plt.tight_layout()
        logger.info("Affichage du dashboard")
        plt.show()
    except Exception:
        logger.exception("Erreur pendant l'affichage du dashboard")
        raise