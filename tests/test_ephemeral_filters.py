from datetime import date

from django.http import QueryDict
from django.test import SimpleTestCase
from rest_framework import exceptions

from dynamic_rest import fields
from dynamic_rest.ephemeral import build_ephemeral_serializer
from dynamic_rest.serializers import DynamicEphemeralSerializer, EphemeralObject
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
    cases_assigned = fields.DynamicIntegerField(read_only=True, sortable=True)
    officer_name = fields.DynamicCharField(read_only=True)
    unfilterable = fields.DynamicCharField(read_only=True)


class SyntheticReportViewSet(DynamicModelViewSet):
    serializer_class = SyntheticReportSerializer


class TestEphemeralFilterMixin(SimpleTestCase):
    def get_view(self, query_string=''):
        request = type(
            'Request',
            (),
            {
                'query_params': QueryDict(query_string),
                'accepted_renderer': None,
            },
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

    def test_supports_case_insensitive_exact_string_filter(self):
        view, request = self.get_view('filter%7Bofficer_name.iexact%7D=Jane')
        specs = view._get_ephemeral_filter_specs(request)

        self.assertEqual(
            view._build_ephemeral_filter(
                *specs[0], view.get_ephemeral_filter_fields()
            ).children,
            [('officer_name__iexact', 'Jane')],
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

    def test_builds_serializer_from_ephemeral_schema(self):
        serializer_class = build_ephemeral_serializer(
            name='uploaded_dataset_row',
            plural_name='uploaded_dataset_rows',
            icon='table',
            description='Rows imported from a user dataset',
            id_field='id',
            name_field='row_number',
            meta_options={
                'default_fields': ('row_number', 'amount'),
            },
            fields={
                'id': {'type': 'integer', 'sortable': False},
                'row_number': {'type': 'integer', 'sortable': True},
                'amount': {
                    'type': 'decimal',
                    'label': 'Amount',
                    'filterable': True,
                    'filter_source': '_dataset_amount',
                    'filter_type': 'decimal',
                    'filter_operators': ('eq', 'gte', 'lte'),
                    'sortable': True,
                },
                'hidden': {'type': 'string', 'include': False},
            },
        )
        view, _request = self.get_view()
        metadata = view.get_ephemeral_resource_metadata(serializer_class)
        fields_metadata = metadata['fields']

        self.assertEqual(metadata['type'], 'resource')
        self.assertEqual(metadata['name'], 'uploaded_dataset_rows')
        self.assertEqual(metadata['singular'], 'uploaded_dataset_row')
        self.assertEqual(metadata['default_fields'], ['row_number', 'amount'])
        self.assertEqual(
            metadata['default_view']['data']['fields'],
            {
                'row_number': True,
                'amount': True,
            },
        )
        self.assertEqual(
            serializer_class.Meta.filter_fields['amount']['source'],
            '_dataset_amount',
        )
        self.assertNotIn('hidden', fields_metadata)
        self.assertEqual(fields_metadata['amount']['type'], 'decimal')
        self.assertTrue(fields_metadata['amount']['filterable'])
        self.assertTrue(fields_metadata['amount']['sortable'])
        self.assertTrue(fields_metadata['row_number']['sortable'])
        self.assertFalse(fields_metadata['id']['sortable'])

    def test_builds_ephemeral_ordering_and_requested_queryset_fields(self):
        view, request = self.get_view(
            'filter%7Bcohort_month%7D=2026-01-01'
            '&sort%5B%5D=-cases_assigned'
        )
        filter_fields = view.get_ephemeral_filter_fields()
        ordering = view.get_ephemeral_ordering(
            SyntheticReportSerializer,
            request=request,
            filter_fields=filter_fields,
        )

        self.assertEqual(ordering, ['-cases_assigned'])
        self.assertEqual(
            view.get_ephemeral_requested_queryset_fields(
                request=request,
                filter_fields=filter_fields,
                ordering=ordering,
            ),
            {'cohort_month_date', 'cases_assigned'},
        )

    def test_list_can_include_ephemeral_resource_metadata(self):
        view, request = self.get_view()
        view.filter_ephemeral_queryset = lambda queryset, **kwargs: queryset
        view.get_ephemeral_ordering = lambda **kwargs: []
        view.get_ephemeral_requested_queryset_fields = lambda **kwargs: set()
        view.paginate_queryset = lambda queryset: None

        response = view.list_ephemeral_queryset(
            [
                EphemeralObject({
                    'pk': '2026-01',
                    'cohort_month': date(2026, 1, 1),
                    'cases_assigned': 2,
                    'officer_name': 'Jane Doe',
                    'unfilterable': 'value',
                }),
            ],
            serializer_class=SyntheticReportSerializer,
            request=request,
            include_resource_metadata=True,
        )

        self.assertIn('resource', response.data)
        self.assertEqual(response.data['resource']['name'], 'synthetic_reports')
        self.assertIn('cohort_month', response.data['resource']['fields'])

    def test_rejects_unknown_ephemeral_ordering_fields(self):
        view, request = self.get_view('sort%5B%5D=unfilterable')

        with self.assertRaises(exceptions.ParseError):
            view.get_ephemeral_ordering(
                SyntheticReportSerializer,
                request=request,
                filter_fields=view.get_ephemeral_filter_fields(),
            )
