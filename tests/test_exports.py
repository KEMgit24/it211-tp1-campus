"""Partie C : exports et ligne de commande."""

import csv
import json

import affecter
from tp1.campagne import Campagne
from tp1.exports import decimal_fr, exporter_csv, exporter_json, vers_dict
from tp1.priorites import PrioriteMerite
from tp1.voeux import lire_voeux

from conftest import DONNEES


def resultat(registre, options):
    campagne = Campagne(registre, options, PrioriteMerite())
    voeux, journal = lire_voeux(DONNEES / "voeux_brut.csv", campagne.codes)
    return campagne.executer(voeux, journal)


def test_decimal_fr():
    from decimal import Decimal

    assert decimal_fr(Decimal("12.34")) == "12,34"
    assert decimal_fr(None) == ""


def test_export_csv(registre, options, tmp_path):
    res = resultat(registre, options)
    chemin = tmp_path / "affectation.csv"
    assert exporter_csv(res, registre, chemin) == 40
    brut = chemin.read_bytes()
    assert brut.startswith(b"\xef\xbb\xbf") and b"\r\n" in brut
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.reader(f, delimiter=";"))
    assert lignes[0][:2] == ["Rang", "Matricule"]
    assert lignes[1][:2] == ["1", "IPN-2024-0092"] and lignes[1][5] == "17,88"


def test_export_json(registre, options, tmp_path):
    res = resultat(registre, options)
    chemin = tmp_path / "affectation.json"
    exporter_json(res, chemin)
    relu = json.loads(chemin.read_text(encoding="utf-8"))
    assert relu == vers_dict(res)
    assert relu["priorite"] == "merite"
    assert len(relu["options"]["OPT 281"]["affectes"]) == 12


def test_ligne_de_commande(tmp_path, capsys):
    code = affecter.main(
        [
            str(DONNEES / "voeux_brut.csv"),
            "--donnees",
            str(DONNEES),
            "--json",
            str(tmp_path / "r.json"),
        ]
    )
    sortie = capsys.readouterr().out
    assert code == 1  # le fichier fourni contient des erreurs
    assert "non affectés : 6" in sortie
    assert (tmp_path / "r.json").exists()


def test_ligne_de_commande_fichier_absent(tmp_path, capsys):
    code = affecter.main([str(tmp_path / "absent.csv"), "--donnees", str(DONNEES)])
    assert code == 2
    assert "erreur" in capsys.readouterr().err
