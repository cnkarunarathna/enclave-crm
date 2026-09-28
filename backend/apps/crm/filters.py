import django_filters

from .models import Company, Contact


class CompanyFilter(django_filters.FilterSet):
    industry = django_filters.CharFilter(lookup_expr="iexact")
    country = django_filters.CharFilter(lookup_expr="iexact")
    # Dates (YYYY-MM-DD), inclusive.
    created_after = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_before = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = Company
        fields = ["industry", "country"]


class ContactFilter(django_filters.FilterSet):
    # A plain number, not a model choice: another tenant's company id just returns
    # an empty list instead of an error that would confirm the id exists.
    company = django_filters.NumberFilter(field_name="company_id")
    role = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Contact
        fields = ["company", "role"]
