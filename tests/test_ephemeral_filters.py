from datetime import date

from django.http import QueryDict
from django.test import SimpleTestCase
from rest_framework import exceptions

from dynamic_rest import fields
from dynamic_rest.serializers import DynamicEphemeralSerializer
from dynamic_rest.viewsets import DynamicModelViewSet


class SyntheticReportSerializer(DynamicEphemeralSerializer):
    class Meta:
        name = 'synthetic_report'
        fields = (
            'pk',
            'cohort_month',
            'cases_assigned',
            'officer_name',
            'unfilterable',
        )
        filter_fields = {
            'cohort_month': ('cohort_month_date', 'date'),
            'cases_assigned': ('cases_assigned', 'integer'),
            'officer_name': ('officer_name', 'string'),
        }

    pk = fields.DynamicCharField(read_only=True)
    cohort_month = fields.DynamicDateField(read_only=True)
    cases_assigned = fields.DynamicIntegerField(read_only=True)
    officer_name = fields.DynamicCharField(read_only=True)
    unfilterable = fields.DynamicCharField(read_only=True)


class SyntheticReportViewSet(DynamicModelViewSet):
    serializer_class = SyntheticReportSerializer


class TestEphemeralFilterMixin(SimpleTestCase):
    def get_view(self, query_string=''):
        request = type(
            'Request',
            (),
            {'query_params': QueryDict(query_string)},
        )()
        view = SyntheticReportViewSet()
        view.request = request
        return view, request

    def test_builds_filters_for_ephemeral_aliases(self):
        view, request = self.get_view(
            'filter%7Bcohort_month%7D=2026-01-01'
            '&filter%7Bcases_assigned.gte%7D=2'
        )
        filter_fields = view.get_ephemeral_filter_fields()
        specs = view._get_ephemeral_filter_specs(request)

        self.assertEqual(
            view._build_ephemeral_filter(*specs[0], filter_fields).children,
            [('cohort_month_date', date(2026, 1, 1))],
        )
        self.assertEqual(
            view._build_ephemeral_filter(*specs[1], filter_fields).children,
            [('cases_assigned__gte', 2)],
        )

    def test_keeps_comma_in_string_equality_filter(self):
        view, request = self.get_view(
            'filter%7Bofficer_name%7D=Doe%2C%20Jane'
        )
        specs = view._get_ephemeral_filter_specs(request)

        self.assertEqual(
            view._build_ephemeral_filter(
                *specs[0], view.get_ephemeral_filter_fields()
            ).children,
            [('officer_name', 'Doe, Jane')],
        )

    def test_rejects_unknown_ephemeral_filter_fields(self):
        view, request = self.get_view('filter%7Bmissing_field%7D=value')
        specs = view._get_ephemeral_filter_specs(request)

        with self.assertRaises(exceptions.ParseError):
            view._build_ephemeral_filter(
                *specs[0],
                view.get_ephemeral_filter_fields(),
            )

    def test_ephemeral_metadata_uses_filter_fields(self):
        view, _request = self.get_view()
        metadata = view.get_ephemeral_resource_metadata(SyntheticReportSerializer)
        fields_metadata = metadata['fields']
        field_permissions = metadata['permissions']['fields']

        self.assertTrue(fields_metadata['cohort_month']['filterable'])
        self.assertEqual(fields_metadata['cohort_month']['filter_type'], 'date')
        self.assertIn('gte', fields_metadata['cohort_month']['filter_operators'])
        self.assertTrue(fields_metadata['cases_assigned']['filterable'])
        self.assertFalse(fields_metadata['unfilterable']['filterable'])
        self.assertFalse(fields_metadata['unfilterable']['sortable'])
        for field_name, field_metadata in fields_metadata.items():
            self.assertTrue(field_metadata['ui'], field_name)
            self.assertTrue(field_permissions[field_name]['read'], field_name)
