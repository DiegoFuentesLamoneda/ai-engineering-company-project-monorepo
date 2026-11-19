"""El vocabulario del gestor, comparado con el briefing literalmente.

docs/contexts/proyectos/centralized-incident-manager.es.md. Si un valor cambia
aquí sin cambiar en el briefing, la API aceptaría datos que la empresa no
reconoce: por eso los valores se escriben a mano y no se derivan del código.
"""

import itertools
import unittest

from incident_analysis import (
    ALLOWED_TRANSITIONS,
    BRANCH_LABELS,
    DEFAULT_BRANCH,
    FINAL_STATUSES,
    Branch,
    IncidentCategory,
    IncidentOrigin,
    IncidentStatus,
    can_transition,
)


class VocabularyTest(unittest.TestCase):
    def test_statuses(self):
        self.assertEqual(
            [s.value for s in IncidentStatus],
            ["open", "in_progress", "resolved", "discarded"],
        )

    def test_categories(self):
        self.assertEqual(
            [c.value for c in IncidentCategory],
            [
                "technical_failure",
                "process_error",
                "client_complaint",
                "candidate_issue",
                "staff_issue",
                "sla_breach",
                "data_quality",
                "other",
            ],
        )

    def test_origins(self):
        self.assertEqual([o.value for o in IncidentOrigin], ["customer", "branch", "internal"])

    def test_branches_and_labels(self):
        self.assertEqual(
            {b.value: BRANCH_LABELS[b] for b in Branch},
            {
                "central": "Central — Sede Valencia",
                "valencia_operations": "Valencia — Operaciones",
                "miami_office": "Miami Office",
                "remote": "Remoto (empleado sin sede fija)",
            },
        )

    def test_default_branch_is_central(self):
        self.assertEqual(DEFAULT_BRANCH, "central")

    def test_enums_are_plain_strings(self):
        # Se guardan en TinyDB y viajan en JSON como texto.
        self.assertEqual(IncidentStatus.OPEN, "open")
        self.assertIsInstance(Branch.REMOTE, str)


class TransitionsTest(unittest.TestCase):
    VALID = {
        ("open", "in_progress"),
        ("open", "discarded"),
        ("in_progress", "resolved"),
        ("in_progress", "discarded"),
    }

    def test_every_pair_of_statuses(self):
        # Las 16 combinaciones: solo las 4 del briefing son válidas.
        for current, target in itertools.product(IncidentStatus, repeat=2):
            with self.subTest(current=current.value, target=target.value):
                self.assertEqual(
                    can_transition(current, target),
                    (current.value, target.value) in self.VALID,
                )

    def test_accepts_plain_strings(self):
        self.assertTrue(can_transition("open", "in_progress"))
        self.assertFalse(can_transition("resolved", "open"))

    def test_unknown_values_are_not_transitions(self):
        self.assertFalse(can_transition("open", "closed"))
        self.assertFalse(can_transition("CLOSED", "resolved"))
        self.assertFalse(can_transition("", ""))

    def test_final_statuses(self):
        self.assertEqual(FINAL_STATUSES, {IncidentStatus.RESOLVED, IncidentStatus.DISCARDED})
        for status in FINAL_STATUSES:
            self.assertEqual(ALLOWED_TRANSITIONS[status], frozenset())

    def test_every_status_has_an_entry(self):
        self.assertEqual(set(ALLOWED_TRANSITIONS), set(IncidentStatus))


if __name__ == "__main__":
    unittest.main()
