"""Lecture et nettoyage du fichier de vœux exporté par le formulaire en ligne.

Partie A du TP1. Les éléments marqués FOURNI ne doivent pas être modifiés ;
les fonctions qui lèvent NotImplementedError sont à écrire. Vous pouvez ajouter
des fonctions auxiliaires (leur nom commencera par un tiret bas).
"""

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from campus import Etudiant

from .erreurs import VoeuInvalide

# FOURNI
FORMAT_HORODATAGE = "%d/%m/%Y %H:%M"
ENTETE = ("Matricule", "Horodatage", "Choix 1", "Choix 2", "Choix 3")
CHOIX_MAX = 3


@dataclass(frozen=True)
class Signalement:
    """Une ligne du journal de lecture (FOURNI)."""

    ligne: int
    gravite: str  # "correction" ou "erreur"
    message: str

    def __str__(self) -> str:
        return f"ligne {self.ligne} [{self.gravite}] {self.message}"


@dataclass(frozen=True)
class Voeu:
    """Les choix d'un étudiant, par ordre de préférence, validés à la construction.

    Les quatre champs sont FOURNIS ; __post_init__ et rang sont à écrire.
    """

    matricule: str
    horodatage: datetime
    choix: tuple[str, ...]
    ligne: int

    def __post_init__(self) -> None:
        """Question A.2. Lève VoeuInvalide (avec self.ligne) si :
        le matricule ne respecte pas Etudiant.MOTIF_MATRICULE (sans normalisation) ;
        horodatage n'est pas un datetime ; choix n'est pas un tuple ;
        choix compte moins de 1 ou plus de CHOIX_MAX éléments ;
        un même code figure deux fois dans choix."""
        raise NotImplementedError("question A.2")

    def rang(self, code: str) -> int | None:
        """Question A.2. Rang (1, 2 ou 3) de code dans les choix ; None s'il n'y
        figure pas."""
        raise NotImplementedError("question A.2")


def normaliser_code(texte: str) -> str:
    """Question A.1. ' opt   282 ' devient 'OPT 282' : espaces de tête et de queue
    supprimés, suites d'espaces réduites à une seule, majuscules."""
    raise NotImplementedError("question A.1")


def lire_horodatage(texte: str) -> datetime:
    """Question A.1. Convertit 'JJ/MM/AAAA HH:MM' (espaces autour tolérés).
    Lève VoeuInvalide (sans numéro de ligne) si le texte ne respecte pas le format
    ou désigne une date impossible."""
    raise NotImplementedError("question A.1")


def lire_voeux(
    chemin: Path | str, codes_ouverts: set[str], separateur: str = ";"
) -> tuple[list[Voeu], list[Signalement]]:
    """Question A.3. Lit le fichier de vœux selon les règles R1 à R9 de l'énoncé.

    Renvoie (voeux, journal) : les vœux retenus, une seule soumission par matricule,
    triés par numéro de ligne ; le journal trié par numéro de ligne.
    Lève VoeuInvalide si l'en-tête n'est pas ENTETE ou si le fichier n'est pas
    un CSV lisible en UTF-8 (UnicodeDecodeError, csv.Error).
    """
    raise NotImplementedError("question A.3")
