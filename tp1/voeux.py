"""Lecture et nettoyage du fichier de vœux exporté par le formulaire en ligne.

Partie A du TP1. Les éléments marqués FOURNI ne doivent pas être modifiés ;
les fonctions qui lèvent NotImplementedError sont à écrire. Vous pouvez ajouter
des fonctions auxiliaires (leur nom commencera par un tiret bas).
"""

import csv
import re
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
        if not re.fullmatch(Etudiant.MOTIF_MATRICULE,self.matricule):
            raise VoeuInvalide("matricule invalide",self.ligne)

        if not isinstance(self.horodatage, datetime):
            raise VoeuInvalide("horodatage invalide", self.ligne)

        if not isinstance(self.choix, tuple) or not (1 <= len(self.choix) <= CHOIX_MAX):
            raise VoeuInvalide("choix invalide", self.ligne)

        if len(self.choix) != len(set(self.choix)):
            raise VoeuInvalide("choix en double", self.ligne)



    def rang(self, code: str) -> int | None:
        """Question A.2. Rang (1, 2 ou 3) de code dans les choix ; None s'il n'y
        figure pas."""
        try:
            return self.choix.index(code) + 1
        except ValueError:
            return None
    


def normaliser_code(texte: str) -> str:
    """Question A.1. ' opt   282 ' devient 'OPT 282' : espaces de tête et de queue
    supprimés, suites d'espaces réduites à une seule, majuscules."""
    return " ".join(texte.split()).upper()


def lire_horodatage(texte: str) -> datetime:
    """Question A.1. Convertit 'JJ/MM/AAAA HH:MM' (espaces autour tolérés).
    Lève VoeuInvalide (sans numéro de ligne) si le texte ne respecte pas le format
    ou désigne une date impossible."""
    try:
        return datetime.strptime(texte.strip(),FORMAT_HORODATAGE)
    except ValueError:
        raise VoeuInvalide("Horodatage invalide : "+texte.strip())


def lire_voeux(
    chemin: Path | str, codes_ouverts: set[str], separateur: str = ";"
) -> tuple[list[Voeu], list[Signalement]]:
    """Question A.3. Lit le fichier de vœux selon les règles R1 à R9 de l'énoncé.

    Renvoie (voeux, journal) : les vœux retenus, une seule soumission par matricule,
    triés par numéro de ligne ; le journal trié par numéro de ligne.
    Lève VoeuInvalide si l'en-tête n'est pas ENTETE ou si le fichier n'est pas
    un CSV lisible en UTF-8 (UnicodeDecodeError, csv.Error).
    """
    voeux_par_matricule = {}
    journal = []

    try:
        with open(chemin, encoding="utf-8-sig", newline="") as f:
            lecteur = csv.reader(f, delimiter=separateur, strict=True)

            # R1 : vérifier l'en-tête
            try:
                entete = next(lecteur)
            except StopIteration:
                raise VoeuInvalide("fichier vide")

            if tuple(ch.strip() for ch in entete) != ENTETE:
                raise VoeuInvalide("en-tête inattendu")

            for numero_ligne, champs in enumerate(lecteur, start=2):

                # R2 : ignorer ligne entièrement vide 
                if all(ch.strip() == "" for ch in champs):
                    continue

                # R3 : ereur pour nombre de champs incorrect
                if len(champs) != 5:
                    journal.append(Signalement(numero_ligne, "erreur",
                        f"nombre de champs incorrect : '{separateur.join(champs)}'"))
                    continue

                # R4 : normaliser le matricule
                matricule_brut = champs[0]
                matricule = matricule_brut.strip().upper()
                if matricule != matricule_brut:
                    journal.append(Signalement(numero_ligne, "correction",
                        f"matricule '{matricule_brut.strip()}' normalisé en {matricule}"))

                # R5 : lire l'horodatage
                try:
                    horodatage = lire_horodatage(champs[1])
                except VoeuInvalide:
                    journal.append(Signalement(numero_ligne, "erreur",
                        f"horodatage invalide : '{champs[1].strip()}'"))
                    continue

                # R6 : traiter les choix
                choix_retenus = []
                for brut in champs[2:5]:
                    if brut.strip() == "":
                        continue
                    normalise = normaliser_code(brut)
                    if normalise != brut:
                        journal.append(Signalement(numero_ligne, "correction",
                            f"code '{brut.strip()}' normalisé en {normalise}"))
                    if normalise not in codes_ouverts:
                        journal.append(Signalement(numero_ligne, "erreur",
                            f"code '{normalise}' inconnu"))
                        continue
                    if normalise in choix_retenus:
                        journal.append(Signalement(numero_ligne, "correction",
                            f"code '{normalise}' en double, retiré"))
                        continue
                    choix_retenus.append(normalise)

                # R7 : erreur pour aucun choix valide 
                if not choix_retenus:
                    journal.append(Signalement(numero_ligne, "erreur",
                        "aucun choix valide"))
                    continue

                try:
                    voeu = Voeu(matricule, horodatage, tuple(choix_retenus), numero_ligne)
                except VoeuInvalide as e:
                    journal.append(Signalement(numero_ligne, "erreur",
                        f"{e.motif} : '{matricule_brut}'"))
                    continue

                # R8 : cas de doublon de matricule , garder le plus récent
                if matricule in voeux_par_matricule:
                    ancien = voeux_par_matricule[matricule]
                    if (horodatage, numero_ligne) > (ancien.horodatage, ancien.ligne):
                        journal.append(Signalement(ancien.ligne, "correction",
                            f"soumission écartée au profit de la ligne {numero_ligne}"))
                        voeux_par_matricule[matricule] = voeu
                    else:
                        journal.append(Signalement(numero_ligne, "correction",
                            f"soumission écartée au profit de la ligne {ancien.ligne}"))
                else:
                    voeux_par_matricule[matricule] = voeu

    except (UnicodeDecodeError, csv.Error) as e:
        raise VoeuInvalide(str(e))

    # R9 : trier par numéro de ligne
    voeux = sorted(voeux_par_matricule.values(), key=lambda v: v.ligne)
    journal.sort(key=lambda s: s.ligne)
    return voeux, journal

