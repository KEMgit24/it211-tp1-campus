"""Script d'analyse des résultats de la campagne pour le rapport (Partie D et Bonus)."""

from datetime import datetime

from campus import Scolarite
from tp1.campagne import Campagne, Resultat, lire_options
from tp1.priorites import PrioriteChronologique, PrioriteMerite, PrioriteTirage
from tp1.voeux import Voeu, lire_voeux

DOSSIER_DONNEES = "donnees"
FICHIER_OPTIONS = "donnees/ues_optionnelles.csv"
FICHIER_VOEUX = "donnees/voeux_brut.csv"


def etat_options_avant_rang(resultat: Resultat, rang: int) -> dict[str, int]:
    """Reconstruit les effectifs de chaque option juste avant le rang donné."""
    effectifs = {ue.code: 0 for ue in resultat.options}
    for d in resultat.decisions:
        if d.rang < rang and d.option is not None:
            effectifs[d.option] += 1
    return effectifs


def analyser_a4(voeux: list[Voeu], journal_lecture: list) -> None:
    """Affiche les statistiques de lecture de voeux_brut.csv (question A.4)."""
    corrections = sum(1 for s in journal_lecture if s.gravite == "correction")
    erreurs = sum(1 for s in journal_lecture if s.gravite == "erreur")
    print("=== A.4 Lecture des voeux ===")
    print(f"Voeux retenus : {len(voeux)}")
    print(
        f"Signalements : {len(journal_lecture)} "
        f"({corrections} corrections, {erreurs} erreurs)"
    )
    for s in journal_lecture:
        print(f"  {s}")


def analyser_d1_d2(
    res_m: Resultat,
    res_c: Resultat,
    registre: Scolarite,
    voeux: list[Voeu],
) -> None:
    """Compare les deux règles et détaille les changements (questions D.1 et D.2)."""
    voeux_par_mat = {v.matricule: v for v in voeux}
    print("\n=== D.1 Comparaison des règles ===")
    for nom, res in (("merite", res_m), ("chronologique", res_c)):
        print(
            f"{nom:13s} | effectifs={res.effectifs()} "
            f"| satisfaction={dict(res.satisfaction())}"
        )

    changements = [
        (dm, res_c.decision(dm.matricule))
        for dm in res_m.decisions
        if dm.option != res_c.decision(dm.matricule).option
    ]
    print(f"Candidats dont l'issue change : {len(changements)}")
    for dm, dc in changements:
        m = dm.matricule
        etu = registre.etudiant(m)
        rel = registre.releve(m, 1)
        v = voeux_par_mat[m]
        print(
            f"  {m} ({etu.nom_complet()}, {etu.filiere}, "
            f"moy={rel.moyenne}, cr={rel.credits_acquis}, date={v.horodatage})"
        )
        print(
            f"    mérite : rang={dm.rang}, option={dm.option} "
            f"(choix {dm.rang_choix}), avant={etat_options_avant_rang(res_m, dm.rang)}, "
            f"refus={dm.refus}"
        )
        print(
            f"    chrono : rang={dc.rang}, option={dc.option} "
            f"(choix {dc.rang_choix}), avant={etat_options_avant_rang(res_c, dc.rang)}, "
            f"refus={dc.refus}"
        )

    print("\n=== D.1 Dossier IPN-2024-0073 ===")
    for nom, res in (("mérite", res_m), ("chronologique", res_c)):
        d = res.decision("IPN-2024-0073")
        print(f"  {nom:13s} : rang={d.rang}, option={d.option} (choix {d.rang_choix})")


def analyser_d3(res_m: Resultat, reg_m: Scolarite, options: list) -> None:
    """Analyse les non affectés au mérite et simule un second tour (question D.3)."""
    print("\n=== D.3 Non affectés (priorité mérite) ===")
    places_restantes = {
        ue.code: ue.capacite - len(reg_m.inscrits(ue.code)) for ue in options
    }
    print(f"Places encore disponibles en fin de campagne : {places_restantes}")

    places_second_tour = 0
    for m in res_m.non_affectes():
        d = res_m.decision(m)
        etu = reg_m.etudiant(m)
        rel = reg_m.releve(m, 1)
        compatibles = [u.code for u in options if not reg_m.motifs_refus(etu, u)]
        print(
            f"  {m} ({etu.nom_complet()}, moy={rel.moyenne}, cr={rel.credits_acquis}) "
            f": refus={d.refus} | éligible fin={compatibles}"
        )
        for u in options:
            if not reg_m.motifs_refus(etu, u):
                reg_m.inscrire(m, u.code)
                places_second_tour += 1
                print(f"    -> Second tour (mérite) : affecté à {u.code}")
                break
    print(f"Total placés au second tour (parmi les 6 non affectés) : {places_second_tour}")


def analyser_d4_d6(res_m: Resultat, res_c: Resultat, voeux: list[Voeu]) -> None:
    """Analyse le cas IPN-2024-0067 (D.4) et le coût en appels (D.6)."""
    print("\n=== D.4 Cas IPN-2024-0067 ===")
    dm67 = res_m.decision("IPN-2024-0067")
    dc67 = res_c.decision("IPN-2024-0067")
    cands_set = {d.matricule for d in res_c.decisions}
    premier_depot = datetime(2026, 1, 12, 11, 28)
    rang_sans_doublon = (
        sum(
            1
            for v in voeux
            if v.matricule in cands_set
            and v.matricule != "IPN-2024-0067"
            and (v.horodatage, v.matricule) < (premier_depot, "IPN-2024-0067")
        )
        + 1
    )
    print(f"  Rang si 1er dépôt conservé (chrono) : {rang_sans_doublon}")
    print(f"  Rang réel après 2e dépôt (chrono)   : {dc67.rang} -> {dc67.option}")
    print(f"  Rang réel (mérite)                  : {dm67.rang} -> {dm67.option}")

    print("\n=== D.6 Coût de la campagne ===")
    appels_m = sum(len(d.refus) + (1 if d.affecte else 0) for d in res_m.decisions)
    appels_c = sum(len(d.refus) + (1 if d.affecte else 0) for d in res_c.decisions)
    nb_ins = len(Scolarite.depuis_csv(DOSSIER_DONNEES)._inscriptions)
    print(f"Appels à registre.inscrire : mérite={appels_m}, chronologique={appels_c}")
    print(f"Inscriptions initiales dans le registre : {nb_ins}")


def analyser_bonus(voeux: list[Voeu], journal_lecture: list, options: list) -> None:
    """Simule PrioriteTirage sur les graines 1 à 100 (Bonus)."""
    print("\n=== Bonus : graines 1 à 100 ===")
    premiers_choix = []
    non_affectes = []
    for graine in range(1, 101):
        reg = Scolarite.depuis_csv(DOSSIER_DONNEES)
        camp = Campagne(reg, options, PrioriteTirage(graine))
        res = camp.executer(voeux, journal_lecture)
        sat = res.satisfaction()
        premiers_choix.append(sat[1])
        non_affectes.append(sat[None])
    print(
        f"Premiers choix obtenus en moyenne : {sum(premiers_choix) / 100:.2f} "
        f"(min={min(premiers_choix)}, max={max(premiers_choix)})"
    )
    print(
        f"Non affectés en moyenne           : {sum(non_affectes) / 100:.2f} "
        f"(min={min(non_affectes)}, max={max(non_affectes)})"
    )


def main() -> None:
    options = lire_options(FICHIER_OPTIONS)
    voeux, journal_lecture = lire_voeux(FICHIER_VOEUX, {u.code for u in options})

    reg_m = Scolarite.depuis_csv(DOSSIER_DONNEES)
    res_m = Campagne(reg_m, options, PrioriteMerite()).executer(
        voeux, journal_lecture
    )

    reg_c = Scolarite.depuis_csv(DOSSIER_DONNEES)
    res_c = Campagne(reg_c, options, PrioriteChronologique()).executer(
        voeux, journal_lecture
    )

    analyser_a4(voeux, journal_lecture)
    analyser_d1_d2(res_m, res_c, reg_m, voeux)
    analyser_d3(res_m, reg_m, options)
    analyser_d4_d6(res_m, res_c, voeux)
    analyser_bonus(voeux, journal_lecture, options)


if __name__ == "__main__":
    main()
