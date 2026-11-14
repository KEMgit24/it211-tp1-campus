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
    return "" if valeur is None else str(valeur).replace(".", ",")


def exporter_csv(
    resultat: Resultat, registre: Scolarite, chemin: Path | str
) -> int:
    """Question C.1. Écrit une ligne par décision, dans l'ordre de passage,
    au format du tableau 4 de l'énoncé ; renvoie le nombre de lignes de données."""
    with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";", lineterminator="\r\n")
        writer.writerow(ENTETE_CSV)
        for d in resultat.decisions:
            etudiant = registre.etudiant(d.matricule)
            moyenne = decimal_fr(registre.releve(d.matricule, 1).moyenne)
            option = d.option if d.affecte else "non affecté"
            choix_obtenu = d.rang_choix if d.affecte else ""
            motifs = " | ".join(
                f"{code} : {', '.join(m)}" for code, m in d.refus
            )
            writer.writerow(
                [
                    d.rang,
                    d.matricule,
                    etudiant.nom,
                    etudiant.prenom,
                    etudiant.filiere,
                    moyenne,
                    option,
                    choix_obtenu,
                    motifs,
                ]
            )
    return len(resultat.decisions)


def vers_dict(resultat: Resultat) -> dict:
    """Question C.2. Le résultat en types JSON, selon la structure de l'énoncé."""
    return {
        "priorite": resultat.priorite,
        "options": {
            ue.code: {
                "intitule": ue.intitule,
                "capacite": ue.capacite,
                "affectes": resultat.affectes(ue.code),
            }
            for ue in resultat.options
        },
        "decisions": [
            {
                "rang": d.rang,
                "matricule": d.matricule,
                "option": d.option,
                "rang_choix": d.rang_choix,
                "refus": {code: list(motifs) for code, motifs in d.refus},
            }
            for d in resultat.decisions
        ],
        "journal": [
            {"ligne": s.ligne, "gravite": s.gravite, "message": s.message}
            for s in resultat.journal
        ],
    }


def exporter_json(resultat: Resultat, chemin: Path | str) -> None:
    """Question C.2. Écrit vers_dict(resultat) en UTF-8, accents non échappés,
    indenté de 2 espaces."""
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(vers_dict(resultat), f, ensure_ascii=False, indent=2)
