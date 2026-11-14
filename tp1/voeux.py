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
        if not isinstance(
            self.matricule, str
        ) or not Etudiant.MOTIF_MATRICULE.fullmatch(self.matricule):
            raise VoeuInvalide(
                f"matricule invalide : '{self.matricule}'", self.ligne
            )
        if not isinstance(self.horodatage, datetime):
            raise VoeuInvalide("horodatage attendu", self.ligne)
        if not isinstance(self.choix, tuple) or not (
            1 <= len(self.choix) <= CHOIX_MAX
        ):
            taille = len(self.choix) if isinstance(self.choix, tuple) else "?"
            raise VoeuInvalide(
                f"nombre de choix invalide ({taille})", self.ligne
            )
        if len(set(self.choix)) != len(self.choix):
            raise VoeuInvalide("choix en double", self.ligne)

    def rang(self, code: str) -> int | None:
        """Question A.2. Rang (1, 2 ou 3) de code dans les choix ; None s'il n'y
        figure pas."""
        return self.choix.index(code) + 1 if code in self.choix else None


def normaliser_code(texte: str) -> str:
    """Question A.1. ' opt   282 ' devient 'OPT 282' : espaces de tête et de queue
    supprimés, suites d'espaces réduites à une seule, majuscules."""
    return " ".join(texte.split()).upper()


def lire_horodatage(texte: str) -> datetime:
    """Question A.1. Convertit 'JJ/MM/AAAA HH:MM' (espaces autour tolérés).
    Lève VoeuInvalide (sans numéro de ligne) si le texte ne respecte pas le format
    ou désigne une date impossible."""
    try:
        return datetime.strptime(texte.strip(), FORMAT_HORODATAGE)
    except ValueError as exc:
        raise VoeuInvalide(f"horodatage invalide : '{texte}'") from exc


def _lire_lignes_csv(chemin: Path | str, separateur: str) -> list[list[str]]:
    """Lit et valide l'en-tête du fichier CSV des vœux (règle R1)."""
    try:
        with open(chemin, encoding="utf-8-sig", newline="") as f:
            lignes = list(csv.reader(f, delimiter=separateur, strict=True))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise VoeuInvalide(str(exc)) from exc
    if not lignes:
        raise VoeuInvalide("fichier de vœux vide")
    if tuple(c.strip() for c in lignes[0]) != ENTETE:
        raise VoeuInvalide(f"en-tête invalide : {lignes[0]!r}", 1)
    return lignes


def _analyser_choix(
    num_ligne: int,
    cellules: list[str],
    codes_ouverts: set[str],
    journal: list[Signalement],
) -> tuple[str, ...]:
    """Nettoie, normalise et dédoublonne les choix d'une ligne (règle R6)."""
    choix: list[str] = []
    for brut in cellules:
        if not brut.strip():
            continue
        code = normaliser_code(brut)
        if code != brut:
            journal.append(
                Signalement(
                    num_ligne, "correction", f"choix '{brut}' normalisé en {code}"
                )
            )
        if code not in codes_ouverts:
            journal.append(
                Signalement(num_ligne, "erreur", f"code '{code}' inconnu")
            )
        elif code in choix:
            journal.append(
                Signalement(
                    num_ligne, "correction", f"choix '{code}' en double retiré"
                )
            )
        else:
            choix.append(code)
    return tuple(choix)


def _analyser_ligne(
    num_ligne: int,
    champs: list[str],
    codes_ouverts: set[str],
    separateur: str,
    journal: list[Signalement],
) -> Voeu | None:
    """Analyse une ligne de données du fichier de vœux (règles R2 à R7)."""
    if all(not c.strip() for c in champs):
        return None
    if len(champs) != len(ENTETE):
        contenu = separateur.join(champs)
        journal.append(
            Signalement(
                num_ligne,
                "erreur",
                f"nombre de champs invalide ({len(champs)}) : '{contenu}'",
            )
        )
        return None

    brut_matricule, brut_horodatage = champs[0], champs[1]
    matricule = brut_matricule.strip().upper()
    if matricule != brut_matricule:
        journal.append(
            Signalement(
                num_ligne,
                "correction",
                f"matricule '{brut_matricule}' normalisé en {matricule}",
            )
        )

    try:
        horodatage = lire_horodatage(brut_horodatage)
    except VoeuInvalide:
        journal.append(
            Signalement(
                num_ligne, "erreur", f"horodatage '{brut_horodatage}' invalide"
            )
        )
        return None

    choix = _analyser_choix(num_ligne, champs[2:], codes_ouverts, journal)
    if not choix:
        journal.append(
            Signalement(
                num_ligne, "erreur", f"aucun choix valide pour '{matricule}'"
            )
        )
        return None

    try:
        return Voeu(matricule, horodatage, choix, num_ligne)
    except VoeuInvalide:
        journal.append(
            Signalement(
                num_ligne, "erreur", f"matricule '{brut_matricule}' mal formé"
            )
        )
        return None


def lire_voeux(
    chemin: Path | str, codes_ouverts: set[str], separateur: str = ";"
) -> tuple[list[Voeu], list[Signalement]]:
    """Question A.3. Lit le fichier de vœux selon les règles R1 à R9 de l'énoncé.

    Renvoie (voeux, journal) : les vœux retenus, une seule soumission par matricule,
    triés par numéro de ligne ; le journal trié par numéro de ligne.
    Lève VoeuInvalide si l'en-tête n'est pas ENTETE ou si le fichier n'est pas
    un CSV lisible en UTF-8 (UnicodeDecodeError, csv.Error).
    """
    lignes = _lire_lignes_csv(chemin, separateur)
    journal: list[Signalement] = []
    par_matricule: dict[str, list[Voeu]] = {}

    for num_ligne, champs in enumerate(lignes[1:], start=2):
        voeu = _analyser_ligne(
            num_ligne, champs, codes_ouverts, separateur, journal
        )
        if voeu is not None:
            par_matricule.setdefault(voeu.matricule, []).append(voeu)

    voeux_retenus: list[Voeu] = []
    for groupe in par_matricule.values():
        retenu = max(groupe, key=lambda v: (v.horodatage, v.ligne))
        voeux_retenus.append(retenu)
        for v in groupe:
            if v is not retenu:
                msg = (
                    f"soumission de {v.matricule} écartée "
                    f"au profit de la ligne {retenu.ligne}"
                )
                journal.append(Signalement(v.ligne, "correction", msg))

    voeux_retenus.sort(key=lambda v: v.ligne)
    journal.sort(key=lambda s: s.ligne)
    return voeux_retenus, journal
