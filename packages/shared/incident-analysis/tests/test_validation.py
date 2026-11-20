"""Una prueba por regla del briefing, más los casos límite de cada una."""

import unittest

from incident_analysis import validate_record

from helpers import VALID_ROW, row


class ValidRecordTest(unittest.TestCase):
    def test_valid_row_has_no_errors(self):
        self.assertEqual(validate_record(VALID_ROW), [])

    def test_surrounding_spaces_are_ignored(self):
        self.assertEqual(validate_record(row(category=" BILLING ", agent_id="AGT-03 ")), [])

    def test_open_and_discarded_do_not_need_score(self):
        self.assertEqual(validate_record(row(status="OPEN", satisfaction_score="")), [])
        self.assertEqual(validate_record(row(status="DISCARDED", satisfaction_score="")), [])

    def test_open_ticket_may_carry_a_score(self):
        self.assertEqual(validate_record(row(status="OPEN", satisfaction_score="3")), [])


class RuleTest(unittest.TestCase):
    def assertRules(self, record, expected):
        self.assertEqual(validate_record(record), expected)

    def test_missing_client_company(self):
        self.assertRules(row(client_company=""), ["missing_client_company"])
        self.assertRules(row(client_company="   "), ["missing_client_company"])

    def test_category_missing_or_unknown(self):
        self.assertRules(row(category=""), ["invalid_category"])
        self.assertRules(row(category="SALES"), ["invalid_category"])
        # Los valores del briefing son literales: en minúsculas no valen.
        self.assertRules(row(category="technical"), ["invalid_category"])

    def test_description_shorter_than_five_characters(self):
        self.assertRules(row(description=""), ["invalid_description"])
        self.assertRules(row(description="Fail"), ["invalid_description"])
        self.assertRules(row(description="Fails"), [])

    def test_agent_id_format(self):
        self.assertRules(row(agent_id=""), ["invalid_agent_id"])
        self.assertRules(row(agent_id="AGT-7"), ["invalid_agent_id"])
        self.assertRules(row(agent_id="agt-07"), ["invalid_agent_id"])
        self.assertRules(row(agent_id="AGT-007"), ["invalid_agent_id"])

    def test_email_missing_or_without_at_sign(self):
        self.assertRules(row(customer_email=""), ["invalid_email"])
        self.assertRules(row(customer_email="persona.example.com"), ["invalid_email"])

    def test_closed_without_score(self):
        self.assertRules(row(status="CLOSED", satisfaction_score=""), ["closed_without_score"])

    def test_score_out_of_range_or_not_an_integer(self):
        for bad in ("0", "6", "-1", "4.5", "4.0", "cinco"):
            with self.subTest(score=bad):
                self.assertRules(row(satisfaction_score=bad), ["score_out_of_range"])

    def test_score_bounds_are_inclusive(self):
        self.assertRules(row(satisfaction_score="1"), [])
        self.assertRules(row(satisfaction_score="5"), [])

    def test_ticket_id_format(self):
        self.assertRules(row(ticket_id=""), ["invalid_ticket_id"])
        self.assertRules(row(ticket_id="NXV-1"), ["invalid_ticket_id"])

    def test_date_format_and_real_date(self):
        self.assertRules(row(date=""), ["invalid_date"])
        self.assertRules(row(date="18/01/2024"), ["invalid_date"])
        self.assertRules(row(date="2024-1-8"), ["invalid_date"])
        self.assertRules(row(date="2024-02-30"), ["invalid_date"])

    def test_status_missing_or_unknown(self):
        self.assertRules(row(status="", satisfaction_score=""), ["invalid_status"])
        self.assertRules(row(status="PENDING", satisfaction_score=""), ["invalid_status"])

    def test_one_row_can_break_several_rules(self):
        self.assertRules(
            row(client_company="", customer_email="", satisfaction_score=""),
            ["missing_client_company", "invalid_email", "closed_without_score"],
        )

    def test_short_row_missing_columns_counts_as_empty_fields(self):
        # csv.DictReader rellena con None las columnas que faltan en una fila corta.
        short = {key: value for key, value in VALID_ROW.items() if key != "customer_email"}
        short["customer_email"] = None
        self.assertRules(short, ["invalid_email"])


if __name__ == "__main__":
    unittest.main()
