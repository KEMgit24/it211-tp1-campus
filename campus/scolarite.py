"""Le registre de la scolarité : regroupe étudiants, enseignants, UE et inscriptions."""

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from . import regles
from .erreurs import (
    DoublonInterdit,
    ErreurCampus,
    InscriptionRefusee,
    NotesVerrouillees,
)
from .inscription import Inscription
from .personnes import Enseignant, Etudiant
from .ue import UE


@dataclass(frozen=True)
class LigneReleve:
    code: str
    intitule: str
    credits: int
    note_cc: Decimal | None
    note_examen: Decimal | str | None
    note_finale: Decimal | None
    decision: str


@dataclass(frozen=True)
class Releve:
    etudiant: Etudiant
    semestre: int
    lignes: tuple[LigneReleve, ...]
    moyenne: Decimal
    mention: str
    credits_acquis: int
    credits_total: int


class Scolarite:
    """Registre d'une année universitaire ; point d'entrée des modifications."""

    CREDITS_MAX = 30

    def __init__(self, annee: str = "2025-2026") -> None:
        self.annee = annee
        self._etudiants: dict[str, Etudiant] = {}
        self._enseignants: dict[str, Enseignant] = {}
        self._ues: dict[str, UE] = {}
        self._inscriptions: dict[tuple[str, str, str], Inscription] = {}
        self._courriels: set[str] = set()
        self.journal: list[dict] = []

    # ---- ajout et consultation
    def _reserver_courriel(self, personne: Etudiant | Enseignant) -> None:
        if personne.courriel in self._courriels:
            raise DoublonInterdit(f"courriel déjà utilisé : {personne.courriel}")
        self._courriels.add(personne.courriel)

    def ajouter_etudiant(self, etudiant: Etudiant) -> Etudiant:
        if etudiant.matricule in self._etudiants:
            raise DoublonInterdit(f"matricule déjà attribué : {etudiant.matricule}")
        self._reserver_courriel(etudiant)
        self._etudiants[etudiant.matricule] = etudiant
        return etudiant

    def ajouter_enseignant(self, enseignant: Enseignant) -> Enseignant:
        if enseignant.code in self._enseignants:
            raise DoublonInterdit(f"code déjà attribué : {enseignant.code}")
        self._reserver_courriel(enseignant)
        self._enseignants[enseignant.code] = enseignant
        return enseignant

    def ajouter_ue(self, ue: UE) -> UE:
        if ue.code in self._ues:
            raise DoublonInterdit(f"code d'UE déjà utilisé : {ue.code}")
        self._ues[ue.code] = ue
        return ue

    def etudiant(self, matricule: str) -> Etudiant:
        return self._etudiants[matricule.strip().upper()]

    def enseignant(self, code: str) -> Enseignant:
        return self._enseignants[code.strip().upper()]

    def ue(self, code: str) -> UE:
        return self._ues[" ".join(code.split()).upper()]

    @property
    def etudiants(self) -> list[Etudiant]:
        return list(self._etudiants.values())

    @property
    def ues(self) -> list[UE]:
        return list(self._ues.values())

    def __contains__(self, element: object) -> bool:
        if isinstance(element, Etudiant):
            return element.matricule in self._etudiants
        if isinstance(element, UE):
            return element.code in self._ues
        return False

    def __repr__(self) -> str:
        return (
            f"Scolarite({self.annee!r} : {len(self._etudiants)} étudiants, "
            f"{len(self._enseignants)} enseignants, {len(self._ues)} UE, "
            f"{len(self._inscriptions)} inscriptions)"
        )

    def inscriptions_de(self, matricule: str) -> list[Inscription]:
        m = matricule.strip().upper()
        return [i for i in self._inscriptions.values() if i.etudiant.matricule == m]

    def inscrits(self, code_ue: str) -> list[Inscription]:
        c = self.ue(code_ue).code
        return [i for i in self._inscriptions.values() if i.ue.code == c]

    def ues_validees(self, matricule: str) -> set[str]:
        return {
            i.ue.code
            for i in self.inscriptions_de(matricule)
            if i.decision == "validée"
        }

    # ---- inscription (RG09, RG10)
    def motifs_refus(self, etudiant: Etudiant, ue: UE) -> list[str]:
        """Raisons de refuser l'inscription ; liste vide si elle est permise."""
        motifs = []
        if ue.niveau != etudiant.niveau:
            motifs.append(f"UE de {ue.niveau}, étudiant en {etudiant.niveau}")
        if ue.filiere not in ("", etudiant.filiere):
            motifs.append(f"UE réservée à la filière {ue.filiere}")
        if (etudiant.matricule, ue.code, self.annee) in self._inscriptions:
            motifs.append("déjà inscrit pour l'année")
        if len(self.inscrits(ue.code)) >= ue.capacite:
            motifs.append(f"capacité atteinte ({ue.capacite})")
        validees = self.ues_validees(etudiant.matricule)
        manquants = sorted(
            p
            for p in ue.prerequis
            if self._ues[p].niveau == ue.niveau and p not in validees
        )
        if manquants:
            motifs.append("prérequis non validés : " + ", ".join(manquants))
        charge = sum(
            i.ue.credits
            for i in self.inscriptions_de(etudiant.matricule)
            if i.ue.semestre == ue.semestre
        )
        if charge + ue.credits > self.CREDITS_MAX:
            motifs.append(
                f"{charge + ue.credits} crédits au semestre {ue.semestre}, "
                f"maximum {self.CREDITS_MAX}"
            )
        return motifs

    def inscrire(
        self, matricule: str, code_ue: str, controler: bool = True
    ) -> Inscription:
        etudiant, ue = self.etudiant(matricule), self.ue(code_ue)
        if controler:
            motifs = self.motifs_refus(etudiant, ue)
            if motifs:
                raise InscriptionRefusee(etudiant.matricule, ue.code, motifs)
        ins = Inscription(etudiant, ue, self.annee)
        self._inscriptions[ins.cle] = ins
        return ins

    def anomalies_prerequis(self) -> list[tuple[str, str, list[str]]]:
        """Inscriptions qui violent les prérequis du même niveau (RG09)."""
        res = []
        for i in self._inscriptions.values():
            validees = self.ues_validees(i.etudiant.matricule)
            manque = sorted(
                p
                for p in i.ue.prerequis
                if self._ues[p].niveau == i.ue.niveau and p not in validees
            )
            if manque:
                res.append((i.etudiant.matricule, i.ue.code, manque))
        return sorted(res)

    # ---- notes (RG11)
    def publier(self, code_ue: str) -> int:
        """Publie les notes d'une UE complète ; renvoie le nombre d'inscriptions."""
        inscrits = self.inscrits(code_ue)
        incompletes = [i.etudiant.matricule for i in inscrits if not i.complete]
        if incompletes:
            raise ErreurCampus(
                f"{len(incompletes)} inscriptions sans note : "
                f"{', '.join(incompletes[:3])}..."
            )
        for i in inscrits:
            i.publier()
        return len(inscrits)

    def corriger(
        self,
        matricule: str,
        code_ue: str,
        champ: str,
        valeur: object,
        auteur: str,
        motif: str,
        quand: datetime | None = None,
    ) -> dict:
        """Corrige une note publiée (RG11) et inscrit la correction au journal."""
        if champ not in ("note_cc", "note_examen"):
            raise ValueError(f"champ inconnu : {champ}")
        if not motif.strip():
            raise ErreurCampus("motif obligatoire pour corriger une note publiée")
        ins = self._inscriptions[
            (matricule.strip().upper(), self.ue(code_ue).code, self.annee)
        ]
        if not ins.publiee:
            raise ErreurCampus(
                "notes non publiées : l'enseignant les modifie directement"
            )
        ancienne = getattr(ins, champ)
        ins._ecrire_corrigee(
            champ, valeur
        )  # seule voie d'écriture après publication
        entree = {
            "horodatage": (quand or datetime.now(timezone.utc)).isoformat(
                timespec="seconds"
            ),
            "auteur": auteur,
            "cle": list(ins.cle),
            "champ": champ,
            "ancienne": str(ancienne),
            "nouvelle": str(getattr(ins, champ)),
            "motif": motif,
        }
        self.journal.append(entree)
        return entree

    # ---- relevé (RG07, RG08)
    def releve(self, matricule: str, semestre: int) -> Releve:
        etudiant = self.etudiant(matricule)
        lignes = tuple(
            LigneReleve(
                i.ue.code,
                i.ue.intitule,
                i.ue.credits,
                i.note_cc,
                i.note_examen,
                i.note_finale,
                i.decision,
            )
            for i in self.inscriptions_de(etudiant.matricule)
            if i.ue.semestre == semestre
        )
        if not lignes:
            raise ErreurCampus(f"aucune inscription au semestre {semestre}")
        moyenne = regles.moyenne_ponderee(
            [(ligne.note_finale, ligne.credits) for ligne in lignes]
        )
        acquis = sum(
            ligne.credits for ligne in lignes if ligne.decision == "validée"
        )
        return Releve(
            etudiant,
            semestre,
            lignes,
            moyenne,
            regles.mention(moyenne),
            acquis,
            sum(ligne.credits for ligne in lignes),
        )

    # ---- chargement et sauvegarde
    @classmethod
    def depuis_csv(
        cls, dossier: Path | str, annee: str = "2025-2026"
    ) -> "Scolarite":
        """Construit le registre depuis le jeu de données (sans contrôle RG09)."""
        d = Path(dossier)

        def lire(nom: str) -> list[dict]:
            with open(d / nom, encoding="utf-8", newline="") as f:
                return list(csv.DictReader(f))

        s = cls(annee)
        for e in lire("enseignants.csv"):
            s.ajouter_enseignant(
                Enseignant(
                    e["code"], e["nom"], e["prenom"], e["courriel"], e["grade"]
                )
            )
        prerequis: dict[str, set[str]] = {}
        for p in lire("prerequis.csv"):
            prerequis.setdefault(p["code_ue"], set()).add(p["code_prerequis"])
        for u in lire("ue.csv"):
            s.ajouter_ue(
                UE(
                    u["code"],
                    u["intitule"],
                    int(u["credits"]),
                    u["niveau"],
                    int(u["semestre"]),
                    u["filiere"],
                    int(u["capacite"]),
                    s.enseignant(u["responsable"]),
                    prerequis.get(u["code"], set()),
                )
            )
        for e in lire("etudiants.csv"):
            s.ajouter_etudiant(
                Etudiant(
                    e["matricule"],
                    e["nom"],
                    e["prenom"],
                    e["courriel"],
                    e["filiere"],
                    e["niveau"],
                    e["date_naissance"],
                )
            )
        for i in lire("inscriptions.csv"):
            if i["annee"] != annee:
                continue
            ins = s.inscrire(i["matricule"], i["code_ue"], controler=False)
            ins.note_cc = i["note_cc"] or None
            ins.note_examen = i["note_examen"] or None
        return s

    def vers_dict(self) -> dict:
        """Représentation en types JSON (les Decimal deviennent des chaînes)."""
        texte = lambda v: None if v is None else str(v)
        return {
            "annee": self.annee,
            "enseignants": [
                {
                    "code": e.code,
                    "nom": e.nom,
                    "prenom": e.prenom,
                    "courriel": e.courriel,
                    "grade": e.grade,
                }
                for e in self._enseignants.values()
            ],
            "ues": [
                {
                    "code": u.code,
                    "intitule": u.intitule,
                    "credits": u.credits,
                    "niveau": u.niveau,
                    "semestre": u.semestre,
                    "filiere": u.filiere,
                    "capacite": u.capacite,
                    "responsable": u.responsable.code if u.responsable else None,
                    "prerequis": sorted(u.prerequis),
                }
                for u in self._ues.values()
            ],
            "etudiants": [
                {
                    "matricule": e.matricule,
                    "nom": e.nom,
                    "prenom": e.prenom,
                    "courriel": e.courriel,
                    "filiere": e.filiere,
                    "niveau": e.niveau,
                    "date_naissance": e.date_naissance.isoformat(),
                    "archive": e.archive,
                }
                for e in self._etudiants.values()
            ],
            "inscriptions": [
                {
                    "matricule": i.etudiant.matricule,
                    "code_ue": i.ue.code,
                    "note_cc": texte(i.note_cc),
                    "note_examen": texte(i.note_examen),
                    "publiee": i.publiee,
                }
                for i in self._inscriptions.values()
            ],
            "journal": self.journal,
        }

    @classmethod
    def depuis_dict(cls, donnees: dict) -> "Scolarite":
        s = cls(donnees["annee"])
        for e in donnees["enseignants"]:
            s.ajouter_enseignant(Enseignant(**e))
        for u in donnees["ues"]:
            resp = u["responsable"]
            s.ajouter_ue(
                UE(
                    **{
                        **u,
                        "responsable": s.enseignant(resp) if resp else None,
                        "prerequis": set(u["prerequis"]),
                    }
                )
            )
        for e in donnees["etudiants"]:
            et = Etudiant(**{k: v for k, v in e.items() if k != "archive"})
            et.archive = e.get("archive", False)
            s.ajouter_etudiant(et)
        for i in donnees["inscriptions"]:
            ins = s.inscrire(i["matricule"], i["code_ue"], controler=False)
            ins.note_cc = i["note_cc"]
            ins.note_examen = i["note_examen"]
            if i["publiee"]:
                ins.publier()
        s.journal = list(donnees.get("journal", []))
        return s

    def sauvegarder(self, chemin: Path | str) -> None:
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(self.vers_dict(), f, ensure_ascii=False, indent=1)

    @classmethod
    def charger(cls, chemin: Path | str) -> "Scolarite":
        with open(chemin, encoding="utf-8") as f:
            return cls.depuis_dict(json.load(f))
