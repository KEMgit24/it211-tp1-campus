"""Question B.5 : vos propres tests (au moins huit, voir l'énoncé).

Chaque test commence par une ligne de commentaire qui dit ce qu'il vérifie
et pourquoi ce cas n'est pas couvert par les tests publics.
"""

import csv

from campus import UE
from tp1.campagne import Campagne
from tp1.exports import exporter_csv
from tp1.priorites import PrioriteMerite, PrioriteTirage
from tp1.voeux import lire_voeux

from conftest import CODES, DONNEES, candidat, voeu  # noqa: F401


def test_ligne_correction_puis_erreur(fichier_voeux):
    # Vérifie qu'une ligne recevant une correction (matricule en minuscules) puis une erreur (code inconnu) conserve les deux signalements dans l'ordre ; les tests publics ne combinent pas ces deux gravités sur une même ligne.
    chemin = fichier_voeux("ipn-2024-0073;13/01/2026 08:16;OPT 284;OPT 281;")
    voeux, journal = lire_voeux(chemin, CODES)
    assert len(voeux) == 1
    assert voeux[0].matricule == "IPN-2024-0073"
    assert voeux[0].choix == ("OPT 281",)
    assert [(s.ligne, s.gravite) for s in journal] == [
        (2, "correction"),
        (2, "erreur"),
    ]
    assert "OPT 284" in journal[1].message


def test_double_soumission_plus_recente_avant(fichier_voeux):
    # Vérifie que lors d'une double soumission où la plus récente apparaît avant l'autre dans le fichier, la première ligne est gardée et la seconde reçoit le signalement citant la ligne retenue ; le test public ne couvre que l'ordre inverse.
    chemin = fichier_voeux(
        "IPN-2024-0073;15/01/2026 10:00;OPT 281;;",
        "IPN-2024-0073;12/01/2026 08:00;OPT 282;;",
    )
    voeux, journal = lire_voeux(chemin, CODES)
    assert [v.ligne for v in voeux] == [2]
    assert voeux[0].choix == ("OPT 281",)
    assert [(s.ligne, s.gravite) for s in journal] == [(3, "correction")]
    assert "2" in journal[0].message


def test_trou_dans_les_choix(fichier_voeux):
    # Vérifie qu'un trou dans les choix (choix 1 vide, choix 2 rempli) n'émet pas de signalement et décale le choix rempli au rang 1 ; les tests publics supposent toujours le choix 1 rempli.
    chemin = fichier_voeux("IPN-2024-0073;13/01/2026 08:16;;OPT 281;")
    voeux, journal = lire_voeux(chemin, CODES)
    assert journal == []
    assert voeux[0].choix == ("OPT 281",)
    assert voeux[0].rang("OPT 281") == 1


def test_departage_matricule_au_merite(registre):
    # Vérifie que deux candidats ayant même moyenne, mêmes crédits et même horodatage sont départagés au mérite par ordre croissant de matricule ; les tests publics s'arrêtent au départage par date.
    a = candidat(
        registre, "IPN-2024-0073", "12/01/2026 08:00", moyenne="14.00", credits=18
    )
    b = candidat(
        registre, "IPN-2024-0056", "12/01/2026 08:00", moyenne="14.00", credits=18
    )
    assert PrioriteMerite().ordonner([a, b]) == [b, a]


def test_option_capacite_un_deux_candidats(registre):
    # Vérifie qu'une option de capacité 1 demandée par deux candidats n'accepte que le premier et refuse le second pour capacité atteinte ; permet d'isoler la gestion de capacité sur un cas minimal.
    option = UE("OPT 299", "Option limitée", 3, "L2", 2, capacite=1)
    campagne = Campagne(registre, [option], PrioriteMerite())
    res = campagne.executer(
        [
            voeu("IPN-2024-0073", "12/01/2026 08:00", "OPT 299", ligne=2),
            voeu("IPN-2024-0092", "12/01/2026 09:00", "OPT 299", ligne=3),
        ]
    )
    assert res.decision("IPN-2024-0092").option == "OPT 299"
    refuse = res.decision("IPN-2024-0073")
    assert not refuse.affecte
    assert refuse.refus[0][0] == "OPT 299"
    assert "capacité" in " ".join(refuse.refus[0][1])
    assert campagne.places_restantes("OPT 299") == 0


def test_candidat_tous_choix_refuses(registre, options):
    # Vérifie qu'un candidat dont tous les choix sont refusés obtient une décision non affectée avec option et rang_choix à None et ses motifs conservés ; les tests publics vérifient surtout un repli sur le 2e choix.
    campagne = Campagne(registre, options, PrioriteMerite())
    res = campagne.executer(
        [voeu("IPN-2024-0074", "12/01/2026 20:00", "OPT 282")]
    )
    d = res.decision("IPN-2024-0074")
    assert d.affecte is False
    assert d.option is None
    assert d.rang_choix is None
    assert len(d.refus) == 1
    assert d.refus[0][0] == "OPT 282"
    assert "RES 231" in " ".join(d.refus[0][1])


def test_registre_inchange_apres_refus_general(registre, options):
    # Vérifie que le registre reste strictement inchangé (aucune inscription ajoutée pour l'étudiant ni pour les options) lorsqu'un candidat essuie un refus sur tous ses choix ; garantit l'absence d'effet de bord.
    campagne = Campagne(registre, options, PrioriteMerite())
    inscriptions_avant = {i.cle for i in registre.inscriptions_de("IPN-2024-0074")}
    effectifs_avant = {ue.code: len(registre.inscrits(ue.code)) for ue in options}

    campagne.executer([voeu("IPN-2024-0074", "12/01/2026 20:00", "OPT 282")])

    assert {
        i.cle for i in registre.inscriptions_de("IPN-2024-0074")
    } == inscriptions_avant
    assert {
        ue.code: len(registre.inscrits(ue.code)) for ue in options
    } == effectifs_avant


def test_export_csv_ligne_non_affecte(registre, options, tmp_path):
    # Vérifie le formatage d'un candidat non affecté dans l'export CSV ('non affecté', choix vide, motifs renseignés) ; le test public ne vérifie que la première ligne qui correspond à un affecté.
    campagne = Campagne(registre, options, PrioriteMerite())
    res = campagne.executer(
        [voeu("IPN-2024-0074", "12/01/2026 20:00", "OPT 282")]
    )
    chemin = tmp_path / "non_affecte.csv"
    assert exporter_csv(res, registre, chemin) == 1
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.reader(f, delimiter=";"))
    ligne = lignes[1]
    assert ligne[1] == "IPN-2024-0074"
    assert ligne[6] == "non affecté"
    assert ligne[7] == ""
    assert ligne[8].startswith("OPT 282 : ") and "RES 231" in ligne[8]


def test_tirage_reproductible_independant_ordre(registre):
    # Vérifie que PrioriteTirage avec une même graine produit exactement le même ordre quel que soit l'ordre de présentation des candidats ; critère clé du bonus non couvert par les tests publics.
    matricules = [
        "IPN-2024-0055",
        "IPN-2024-0056",
        "IPN-2024-0073",
        "IPN-2024-0074",
        "IPN-2024-0092",
    ]
    cands = [candidat(registre, m) for m in matricules]
    desordre = [cands[4], cands[2], cands[0], cands[3], cands[1]]
    prio = PrioriteTirage(graine=42)
    assert [c.matricule for c in prio.ordonner(cands)] == [
        c.matricule for c in prio.ordonner(desordre)
    ]


def test_tirage_graines_differentes(registre):
    # Vérifie que deux graines distinctes produisent des ordres différents sur un groupe de candidats ; évite qu'une implémentation constante passe le test de reproductibilité.
    matricules = [
        "IPN-2024-0055",
        "IPN-2024-0056",
        "IPN-2024-0073",
        "IPN-2024-0074",
        "IPN-2024-0092",
    ]
    cands = [candidat(registre, m) for m in matricules]
    ordre1 = [c.matricule for c in PrioriteTirage(graine=1).ordonner(cands)]
    ordre2 = [c.matricule for c in PrioriteTirage(graine=2).ordonner(cands)]
    assert ordre1 != ordre2
