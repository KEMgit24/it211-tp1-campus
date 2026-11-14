"""Campagne d'affectation aux UE optionnelles de L2 (TP1 d'IT 211).

Exemple :
    python affecter.py donnees/voeux_brut.csv --priorite merite --csv a.csv

Code de retour : 0 si aucune erreur, 1 si le journal contient des erreurs
(les exports sont produits quand même), 2 si la campagne n'a pas pu avoir lieu.
"""

import argparse
import sys
from pathlib import Path

from campus import ErreurCampus, Scolarite
from tp1.campagne import Campagne, lire_options
from tp1.exports import exporter_csv, exporter_json
from tp1.priorites import PRIORITES, PrioriteTirage
from tp1.voeux import lire_voeux


# FOURNI
def analyser(arguments: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Affecte les étudiants de L2 aux UE optionnelles."
    )
    p.add_argument(
        "voeux", type=Path, help="fichier de vœux exporté par le formulaire"
    )
    p.add_argument(
        "--donnees",
        type=Path,
        default=Path("donnees"),
        help="dossier du jeu de données campus (défaut : donnees)",
    )
    p.add_argument(
        "--options",
        type=Path,
        default=None,
        help="fichier des options (défaut : <donnees>/ues_optionnelles.csv)",
    )
    p.add_argument("--priorite", choices=sorted(PRIORITES), default="merite")
    p.add_argument(
        "--graine",
        type=int,
        default=2026,
        help="graine du tirage au sort (priorité tirage seulement)",
    )
    p.add_argument("--csv", type=Path, help="export pour le tableur")
    p.add_argument("--json", type=Path, help="export JSON")
    p.add_argument(
        "-v", "--verbeux", action="store_true", help="affiche tout le journal"
    )
    return p.parse_args(arguments)


def _afficher_bilan(resultat, verbeux: bool) -> None:
    """Affiche le bilan de la campagne selon le modèle de l'énoncé."""
    print(f"Priorité {resultat.priorite} : {len(resultat.decisions)} candidats")
    effectifs = resultat.effectifs()
    for ue in resultat.options:
        print(f"  {ue.code}  {effectifs[ue.code]:3d} / {ue.capacite}  {ue.intitule}")
    satisfaction = resultat.satisfaction()
    for rang in (1, 2, 3):
        print(f"  choix {rang} obtenu : {satisfaction[rang]}")
    print(f"  non affectés : {satisfaction[None]}")

    corrections = sum(1 for s in resultat.journal if s.gravite == "correction")
    erreurs = resultat.erreurs
    print(f"Journal : {corrections} corrections, {len(erreurs)} erreurs")
    a_afficher = resultat.journal if verbeux else erreurs
    for signalement in a_afficher:
        print(f"  {signalement}")


def main(arguments: list[str] | None = None) -> int:
    """Question C.3. Enchaîne lecture, campagne, affichage et exports ;
    renvoie le code de retour décrit dans l'énoncé (0, 1 ou 2)."""
    args = analyser(arguments)
    chemin_options = args.options or (args.donnees / "ues_optionnelles.csv")
    try:
        registre = Scolarite.depuis_csv(args.donnees)
        options = lire_options(chemin_options)
        cls_prio = PRIORITES[args.priorite]
        priorite = (
            cls_prio(args.graine)
            if cls_prio is PrioriteTirage
            else cls_prio()
        )
        campagne = Campagne(registre, options, priorite)
        voeux, journal_lecture = lire_voeux(args.voeux, campagne.codes)
        resultat = campagne.executer(voeux, journal_lecture)
        _afficher_bilan(resultat, args.verbeux)
        if args.csv:
            n = exporter_csv(resultat, registre, args.csv)
            print(f"{n} lignes écrites dans {args.csv}")
        if args.json:
            exporter_json(resultat, args.json)
            print(f"Résultat écrit dans {args.json}")
    except (OSError, ErreurCampus) as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 2
    return 1 if resultat.erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
