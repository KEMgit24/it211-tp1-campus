"""Exceptions du TP1 (fichier fourni, à ne pas modifier)."""

from campus import ErreurCampus


class VoeuInvalide(ErreurCampus, ValueError):
    """Un vœu, ou le fichier qui les contient, ne respecte pas le format attendu."""

    def __init__(self, motif: str, ligne: int | None = None) -> None:
        prefixe = f"ligne {ligne} : " if ligne is not None else ""
        super().__init__(prefixe + motif)
        self.motif = motif
        self.ligne = ligne


class CampagneDejaExecutee(ErreurCampus):
    """Une campagne inscrit des étudiants : elle ne s'exécute qu'une fois."""
