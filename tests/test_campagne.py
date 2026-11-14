"""Partie B : la campagne."""

import pytest

from tp1.campagne import Campagne
from tp1.erreurs import CampagneDejaExecutee
from tp1.priorites import PrioriteChronologique, PrioriteMerite
from tp1.voeux import lire_voeux

from conftest import CODES, DONNEES, voeu


def lancer(registre, options, priorite):
    campagne = Campagne(registre, options, priorite)
    voeux, journal = lire_voeux(DONNEES / "voeux_brut.csv", campagne.codes)
    return campagne, campagne.executer(voeux, journal)


def test_candidats_ecarte_inconnu_et_l3(registre, options):
    campagne = Campagne(registre, options, PrioriteMerite())
    voeux = [
        voeu("IPN-2024-0073", "13/01/2026 08:16", "OPT 282", ligne=2),
        voeu("IPN-2023-0099", "13/01/2026 09:41", "OPT 283", ligne=3),
        voeu("IPN-2024-9999", "14/01/2026 16:02", "OPT 281", ligne=4),
    ]
    candidats, journal = campagne.candidats(voeux)
    assert [c.matricule for c in candidats] == ["IPN-2024-0073"]
    assert (
        str(candidats[0].moyenne) == "11.49" and candidats[0].credits_acquis == 14
    )
    assert [(s.ligne, s.gravite) for s in journal] == [(3, "erreur"), (4, "erreur")]


def test_places_restantes(registre, options):
    campagne = Campagne(registre, options, PrioriteMerite())
    assert campagne.places_restantes("OPT 282") == 12
    campagne.executer([voeu("IPN-2024-0073", "13/01/2026 08:16", "OPT 282")])
    assert campagne.places_restantes("OPT 282") == 11


def test_premier_choix_possible(registre, options):
    # IPN-2024-0074 n'a pas validé RES 231 : son premier choix est refusé
    campagne = Campagne(registre, options, PrioriteMerite())
    res = campagne.executer(
        [voeu("IPN-2024-0074", "12/01/2026 20:00", "OPT 282", "OPT 281")]
    )
    d = res.decision("IPN-2024-0074")
    assert (d.option, d.rang_choix) == ("OPT 281", 2)
    assert d.refus[0][0] == "OPT 282"
    assert "RES 231" in " ".join(d.refus[0][1])


def test_resultat_merite(registre, options):
    _, res = lancer(registre, options, PrioriteMerite())
    assert len(res.decisions) == 40
    assert res.effectifs() == {"OPT 281": 12, "OPT 282": 11, "OPT 283": 11}
    assert res.satisfaction() == {1: 26, 2: 4, 3: 4, None: 6}
    assert res.decisions[0].matricule == "IPN-2024-0092"
    assert [d.rang for d in res.decisions] == list(range(1, 41))


def test_resultat_chronologique(registre, options):
    _, res = lancer(registre, options, PrioriteChronologique())
    assert res.effectifs() == {"OPT 281": 12, "OPT 282": 11, "OPT 283": 12}
    assert len(res.non_affectes()) == 5


def test_capacite_jamais_depassee(registre, options):
    _, res = lancer(registre, options, PrioriteChronologique())
    for ue in res.options:
        assert (
            len(registre.inscrits(ue.code))
            == res.effectifs()[ue.code]
            <= ue.capacite
        )


def test_inscriptions_dans_le_registre(registre, options):
    _, res = lancer(registre, options, PrioriteMerite())
    d = res.decision("IPN-2024-0073")
    assert d.option == "OPT 282"
    codes = {i.ue.code for i in registre.inscriptions_de("IPN-2024-0073")}
    assert "OPT 282" in codes


def test_journal_complet(registre, options):
    _, res = lancer(registre, options, PrioriteMerite())
    assert len(res.journal) == 10
    assert len(res.erreurs) == 5
    assert [s.ligne for s in res.journal] == sorted(s.ligne for s in res.journal)


def test_une_seule_execution(registre, options):
    campagne, _ = lancer(registre, options, PrioriteMerite())
    with pytest.raises(CampagneDejaExecutee):
        campagne.executer([])
