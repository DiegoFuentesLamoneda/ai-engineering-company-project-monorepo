"""Pruebas HTTP del gestor de incidencias: alta, consulta, ciclo de vida y resumen.

Cada prueba usa ficheros temporales, nunca storage/. Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from incident_analysis import Branch, IncidentCategory, IncidentOrigin, IncidentStatus, plan_seed_file
from pydantic import SecretStr

from app.config import Settings
from app.domains.auth.security import create_access_token
from app.domains.incidents import service
from app.domains.incidents.database import IncidentRepository
from app.domains.incidents.exceptions import StatusChangedError
from app.domains.incidents.schemas import Incident, IncidentCreate
from app.domains.incidents.seed import seed_incidents
from app.domains.profiles.database import ProfileRepository
from app.domains.users import service as users_service
from app.domains.users.database import UserRepository
from app.domains.users.schemas import UserCreate
from app.errors import GENERIC_ERROR
from app.main import create_app
from http_client import request

SECRET = SecretStr("s" * 40)
REPO_ROOT = Path(__file__).resolve().parents[3]
BRIEFING_CSV = REPO_ROOT / "scripts" / "incidents-nexova.csv"
FRONTEND = "http://localhost:3000"

VALID = {
    "title": "La VPN de Miami se cae cada mañana",
    "description": "Desde el lunes, la VPN se desconecta a las 9:00 y tarda diez minutos en volver.",
    "category": "technical_failure",
    "origin": "branch",
    "branch": "miami_office",
}


class IncidentRoutesTestCase(unittest.TestCase):
    """Una app con el gestor vacío y una cuenta con token."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        directory = Path(tmp.name)
        self.incidents = IncidentRepository(directory / "incidents.json")
        self.addCleanup(self.incidents.close)
        users = UserRepository(directory / "users.json")
        self.addCleanup(users.close)
        profiles = ProfileRepository(directory / "profiles.json")
        self.addCleanup(profiles.close)

        settings = Settings(
            cors_origins=[FRONTEND],
            max_upload_mb=10,
            jwt_secret_key=SECRET,
            access_token_expire_minutes=30,
        )
        self.app = create_app(settings)
        self.app.state.incidents = self.incidents
        self.app.state.users = users
        self.app.state.profiles = profiles

        account = UserCreate(email="ana@nexova.es", password="contraseña-segura")
        ana, _ = users_service.create_user(users, profiles, account)
        self.token = create_access_token(ana.id, SECRET, 30)

    def call(self, method, path, **kwargs):
        kwargs.setdefault("token", self.token)
        return request(self.app, method, path, **kwargs)

    def create(self, **changes):
        response = self.call("POST", "/api/incidents", json_body=VALID | changes)
        self.assertEqual(response.status_code, 201, response.body)
        return response.json()

    def assert_field_error(self, response, field, code):
        self.assertEqual(response.status_code, 400, response.body)
        body = response.json()
        self.assertIn((field, code), [(e["field"], e["code"]) for e in body["errors"]])
        # El mensaje legible también nombra el campo.
        self.assertIn(f"'{field}'" if field != "body" else "cuerpo", body["detail"])
        return body


class CreateIncidentTests(IncidentRoutesTestCase):
    def test_a_valid_incident_is_created_open(self):
        response = self.call("POST", "/api/incidents", json_body=VALID | {"title": "  Con espacios  "})
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["status"], "open")
        self.assertEqual(body["title"], "Con espacios")
        self.assertEqual(body["created_at"], body["updated_at"])
        self.assertEqual(response.headers["location"], f"/api/incidents/{body['id']}")
        # Queda guardada: se puede leer por su ID.
        self.assertEqual(self.call("GET", response.headers["location"]).json(), body)

    def test_remote_is_a_valid_branch(self):
        self.assertEqual(self.create(branch="remote")["branch"], "remote")

    def test_a_missing_branch_is_400_naming_the_field(self):
        data = {k: v for k, v in VALID.items() if k != "branch"}
        response = self.call("POST", "/api/incidents", json_body=data)
        body = self.assert_field_error(response, "branch", "missing")
        self.assertEqual(body["detail"], "El campo 'branch' es obligatorio.")

    def test_a_blank_title_is_400(self):
        response = self.call("POST", "/api/incidents", json_body=VALID | {"title": "   "})
        self.assert_field_error(response, "title", "blank")

    def test_a_too_long_title_says_the_limit_without_echoing_it(self):
        long_title = "x" * 500
        response = self.call("POST", "/api/incidents", json_body=VALID | {"title": long_title})
        body = self.assert_field_error(response, "title", "too_long")
        self.assertIn("120", body["detail"])
        self.assertNotIn(long_title, response.body.decode())

    def test_an_unknown_category_lists_the_valid_ones(self):
        response = self.call("POST", "/api/incidents", json_body=VALID | {"category": "urgent"})
        body = self.assert_field_error(response, "category", "invalid_choice")
        self.assertIn("'urgent'", body["detail"])
        self.assertIn("sla_breach", body["detail"])

    def test_every_wrong_field_is_reported(self):
        response = self.call("POST", "/api/incidents", json_body={"title": "", "origin": "nowhere"})
        fields = {e["field"] for e in response.json()["errors"]}
        self.assertEqual(fields, {"title", "description", "category", "origin", "branch"})

    def test_the_status_is_not_chosen_by_the_caller(self):
        response = self.call("POST", "/api/incidents", json_body=VALID | {"status": "resolved"})
        self.assert_field_error(response, "status", "not_allowed")

    def test_no_body_or_a_non_object_body_is_400(self):
        self.assert_field_error(self.call("POST", "/api/incidents"), "body", "invalid_body")
        response = self.call("POST", "/api/incidents", json_body=[VALID])
        self.assert_field_error(response, "body", "invalid_body")

    def test_nothing_is_stored_when_it_fails(self):
        self.call("POST", "/api/incidents", json_body=VALID | {"branch": "madrid"})
        self.assertEqual(self.incidents.count(), 0)


class ListIncidentTests(IncidentRoutesTestCase):
    def test_an_empty_manager_returns_an_empty_list(self):
        response = self.call("GET", "/api/incidents")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_filters_combine(self):
        self.create()
        sla = self.create(category="sla_breach", origin="customer", branch="central")
        self.create(category="sla_breach", origin="internal", branch="remote")

        def ids(query):
            response = self.call("GET", f"/api/incidents?{query}")
            self.assertEqual(response.status_code, 200)
            return [i["id"] for i in response.json()]

        self.assertEqual(len(ids("category=sla_breach")), 2)
        self.assertEqual(ids("category=sla_breach&origin=customer"), [sla["id"]])
        self.assertEqual(len(ids("status=open&branch=remote")), 1)
        self.assertEqual(ids("status=resolved"), [])

    def test_the_newest_comes_first(self):
        # Reloj fijo: dos altas seguidas pueden caer en el mismo instante.
        t0 = datetime(2026, 11, 19, 9, 0, tzinfo=UTC)
        data = IncidentCreate.model_validate(VALID)
        first = service.create_incident(self.incidents, data, now=lambda: t0)
        second = service.create_incident(self.incidents, data, now=lambda: t0 + timedelta(minutes=1))
        listed = [i["id"] for i in self.call("GET", "/api/incidents").json()]
        self.assertEqual(listed, [str(second.id), str(first.id)])

    def test_an_unknown_filter_value_is_400(self):
        response = self.call("GET", "/api/incidents?status=closed")
        body = self.assert_field_error(response, "status", "invalid_choice")
        self.assertTrue(body["detail"].startswith("El filtro 'status'"))


class GetIncidentTests(IncidentRoutesTestCase):
    def test_an_unknown_id_is_404(self):
        missing = uuid4()
        response = self.call("GET", f"/api/incidents/{missing}")
        self.assertEqual(response.status_code, 404)
        self.assertIn(str(missing), response.json()["detail"])

    def test_an_id_that_is_not_a_uuid_is_400(self):
        self.assert_field_error(self.call("GET", "/api/incidents/42"), "incident_id", "invalid_id")


class ChangeStatusTests(IncidentRoutesTestCase):
    def patch(self, incident_id, status):
        return self.call("PATCH", f"/api/incidents/{incident_id}/status", json_body={"status": status})

    def test_the_whole_happy_path(self):
        incident = self.create()
        moved = self.patch(incident["id"], "in_progress")
        self.assertEqual(moved.status_code, 200)
        self.assertEqual(moved.json()["status"], "in_progress")
        self.assertEqual(moved.json()["created_at"], incident["created_at"])
        self.assertGreaterEqual(moved.json()["updated_at"], incident["updated_at"])
        self.assertEqual(self.patch(incident["id"], "resolved").json()["status"], "resolved")

    def test_every_allowed_transition(self):
        for path in (["in_progress", "resolved"], ["in_progress", "discarded"], ["discarded"]):
            with self.subTest(path=path):
                incident = self.create()
                for target in path:
                    self.assertEqual(self.patch(incident["id"], target).status_code, 200)

    def test_a_skipped_step_is_409_and_explains_why(self):
        incident = self.create()
        response = self.patch(incident["id"], "resolved")
        self.assertEqual(response.status_code, 409)
        self.assertIn("in_progress, discarded", response.json()["detail"])
        # No ha cambiado nada.
        self.assertEqual(self.call("GET", f"/api/incidents/{incident['id']}").json(), incident)

    def test_final_statuses_do_not_move(self):
        incident = self.create()
        self.patch(incident["id"], "discarded")
        for target in ("open", "in_progress", "resolved"):
            with self.subTest(target=target):
                response = self.patch(incident["id"], target)
                self.assertEqual(response.status_code, 409)
                self.assertIn("estado final", response.json()["detail"])

    def test_the_same_status_is_409(self):
        incident = self.create()
        self.assertEqual(self.patch(incident["id"], "open").status_code, 409)

    def test_an_unknown_incident_is_404(self):
        self.assertEqual(self.patch(uuid4(), "in_progress").status_code, 404)

    def test_an_unknown_status_is_400(self):
        incident = self.create()
        self.assert_field_error(self.patch(incident["id"], "closed"), "status", "invalid_choice")

    def test_a_concurrent_change_is_409(self):
        incident = self.create()
        # Otra persona la descarta justo después de que la leamos.
        original_update = self.incidents.update_status

        def someone_else_first(incident_id, **kwargs):
            original_update(
                incident_id,
                expected=IncidentStatus.OPEN,
                target=IncidentStatus.DISCARDED,
                updated_at=kwargs["updated_at"],
            )
            return original_update(incident_id, **kwargs)

        self.incidents.update_status = someone_else_first
        response = self.patch(incident["id"], "in_progress")
        self.assertEqual(response.status_code, 409)
        self.assertIn("mientras tanto", response.json()["detail"])
        self.assertEqual(self.incidents.get(incident["id"]).status, IncidentStatus.DISCARDED)


class SummaryTests(IncidentRoutesTestCase):
    def test_an_empty_manager_returns_zeros_for_every_value(self):
        response = self.call("GET", "/api/incidents/summary")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 0)
        for key, values in (
            ("by_status", IncidentStatus),
            ("by_category", IncidentCategory),
            ("by_origin", IncidentOrigin),
            ("by_branch", Branch),
        ):
            with self.subTest(breakdown=key):
                # Todos los valores, en el orden del briefing.
                self.assertEqual(list(body[key]), [v.value for v in values])
                self.assertEqual(set(body[key].values()), {0})

    def test_after_the_seed_it_matches_the_briefing(self):
        seed_incidents(self.incidents, plan_seed_file(BRIEFING_CSV))
        body = self.call("GET", "/api/incidents/summary").json()
        self.assertEqual(body["total"], 96)
        self.assertEqual(
            {k: v for k, v in body["by_status"].items() if v}, {"open": 27, "resolved": 56, "discarded": 13}
        )
        self.assertEqual(
            {k: v for k, v in body["by_category"].items() if v},
            {"technical_failure": 49, "process_error": 35, "client_complaint": 12},
        )
        self.assertEqual(body["by_origin"]["customer"], 96)
        self.assertEqual(body["by_branch"]["central"], 96)

    def test_new_incidents_and_status_changes_are_counted(self):
        incident = self.create(branch="remote", category="sla_breach")
        self.call("PATCH", f"/api/incidents/{incident['id']}/status", json_body={"status": "in_progress"})
        body = self.call("GET", "/api/incidents/summary").json()
        self.assertEqual(body["by_status"]["in_progress"], 1)
        self.assertEqual(body["by_category"]["sla_breach"], 1)
        self.assertEqual(body["by_branch"]["remote"], 1)
        self.assertEqual(body["by_origin"]["branch"], 1)


class AuthAndScopeTests(IncidentRoutesTestCase):
    def test_every_manager_route_needs_a_token(self):
        routes = [
            ("POST", "/api/incidents", VALID),
            ("GET", "/api/incidents", None),
            ("GET", "/api/incidents/summary", None),
            ("GET", f"/api/incidents/{uuid4()}", None),
            ("PATCH", f"/api/incidents/{uuid4()}/status", {"status": "in_progress"}),
        ]
        for method, path, body in routes:
            with self.subTest(route=f"{method} {path}"):
                self.assertEqual(self.call(method, path, json_body=body, token=None).status_code, 401)

    def test_the_analyzer_keeps_its_422(self):
        # El 400 es solo del gestor: el contrato del analizador no cambia.
        self.assertEqual(self.call("POST", "/api/incidents/analyze").status_code, 422)


class BrokenRepository:
    """Un repositorio que falla como fallaría un disco lleno o un JSON corrupto."""

    def __getattr__(self, name):
        def fail(*_args, **_kwargs):
            raise RuntimeError("detalle interno: C:/storage/incidents.json corrupto")

        return fail


class UnexpectedErrorTests(IncidentRoutesTestCase):
    def setUp(self):
        super().setUp()
        self.app.state.incidents = BrokenRepository()

    def test_a_500_is_generic_json_without_the_stack_trace(self):
        with self.assertLogs("nexova.errors", level="ERROR") as logs:
            response = self.call("GET", "/api/incidents")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": GENERIC_ERROR})
        self.assertNotIn("Traceback", response.body.decode())
        self.assertNotIn("corrupto", response.body.decode())
        # El detalle no se pierde: va al log del servidor.
        self.assertIn("corrupto", "\n".join(logs.output))

    def test_the_500_carries_the_cors_header(self):
        # Si no, el navegador lo oculta y el frontend solo ve "Failed to fetch".
        with self.assertLogs("nexova.errors", level="ERROR"):
            response = self.call("GET", "/api/incidents/summary", headers={"Origin": FRONTEND})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers.get("access-control-allow-origin"), FRONTEND)


class ServiceTests(unittest.TestCase):
    """Lo que la HTTP no deja fijar: el reloj y el ID."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = IncidentRepository(Path(tmp.name) / "incidents.json")
        self.addCleanup(self.repo.close)
        self.t0 = datetime(2026, 11, 19, 9, 0, tzinfo=UTC)

    def test_create_uses_the_clock_and_the_id_it_is_given(self):
        fixed_id = uuid4()
        data = IncidentCreate.model_validate(VALID)
        incident = service.create_incident(self.repo, data, now=lambda: self.t0, new_id=lambda: fixed_id)
        self.assertEqual(incident.id, fixed_id)
        self.assertEqual((incident.created_at, incident.updated_at), (self.t0, self.t0))

    def test_change_status_moves_updated_at_only(self):
        data = IncidentCreate.model_validate(VALID)
        incident = service.create_incident(self.repo, data, now=lambda: self.t0)
        later = self.t0 + timedelta(hours=2)
        moved = service.change_status(self.repo, incident.id, IncidentStatus.IN_PROGRESS, now=lambda: later)
        self.assertEqual((moved.created_at, moved.updated_at), (self.t0, later))

    def test_a_lost_race_raises_status_changed(self):
        incident = service.create_incident(self.repo, IncidentCreate.model_validate(VALID))
        self.repo.update_status = lambda *_a, **_k: None  # la otra petición ganó
        with self.assertRaises(StatusChangedError):
            service.change_status(self.repo, incident.id, IncidentStatus.IN_PROGRESS)

    def test_summary_of_one_incident(self):
        self.repo.insert(
            Incident(
                id=uuid4(),
                status=IncidentStatus.RESOLVED,
                created_at=self.t0,
                updated_at=self.t0,
                **IncidentCreate.model_validate(VALID).model_dump(),
            )
        )
        summary = service.summarize(self.repo)
        self.assertEqual(summary.total, 1)
        self.assertEqual(summary.by_status[IncidentStatus.RESOLVED], 1)
        self.assertEqual(summary.by_branch[Branch.MIAMI_OFFICE], 1)


if __name__ == "__main__":
    unittest.main()
