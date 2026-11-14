"""Exports du résultat : CSV pour le tableur, JSON pour les programmes.

Partie C du TP1. ENTETE_CSV est FOURNI ; les fonctions sont à écrire.
"""

import csv
import json
from pathlib import Path

from campus import Scolarite

from .campagne import Resultat

# FOURNI
ENTETE_CSV = (
    "Rang",
    "Matricule",
    "Nom",
    "Prénom",
    "Filière",
    "Moyenne S1",
    "Option",
    "Choix obtenu",
    "Motifs",
)


def decimal_fr(valeur) -> str:
    """Question C.1. Decimal('12.34') devient '12,34' ; None devient ''."""
    raise NotImplementedError("question C.1")


def exporter_csv(
    resultat: Resultat, registre: Scolarite, chemin: Path | str
) -> int:
    """Question C.1. Écrit une ligne par décision, dans l'ordre de passage,
    au format du tableau 4 de l'énoncé ; renvoie le nombre de lignes de données."""
    raise NotImplementedError("question C.1")


def vers_dict(resultat: Resultat) -> dict:
    """Question C.2. Le résultat en types JSON, selon la structure de l'énoncé."""
    raise NotImplementedError("question C.2")


def exporter_json(resultat: Resultat, chemin: Path | str) -> None:
    """Question C.2. Écrit vers_dict(resultat) en UTF-8, accents non échappés,
    indenté de 2 espaces."""
    raise NotImplementedError("question C.2")
