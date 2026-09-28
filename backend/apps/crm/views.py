"""
Thin views: validate with the serializer -> call the service -> return the result.
Tenant scoping and RBAC come from OrganizationScopedViewSet.
"""

from django.db.models import Count, Q
from rest_framework import status
from rest_framework.response import Response

from apps.core.viewsets import OrganizationScopedViewSet

from . import services
from .filters import CompanyFilter, ContactFilter
from .models import Company, Contact
from .serializers import CompanySerializer, ContactSerializer


def deleted_response(message):
    return Response({"success": True, "message": message, "data": None})


class CompanyViewSet(OrganizationScopedViewSet):
    model = Company
    permission_resource = "company"
    serializer_class = CompanySerializer
    filterset_class = CompanyFilter
    search_fields = ["name", "industry", "country"]
    ordering_fields = ["name", "industry", "country", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(contacts_count=Count("contacts", filter=Q(contacts__is_deleted=False)))
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = services.create_company(user=request.user, data=serializer.validated_data)
        return Response(self._representation(company), status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        company = self.get_object()
        serializer = self.get_serializer(
            company, data=request.data, partial=kwargs.get("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        company = services.update_company(
            user=request.user, company=company, data=serializer.validated_data
        )
        return Response(self._representation(company))

    def destroy(self, request, *args, **kwargs):
        services.delete_company(user=request.user, company=self.get_object())
        return deleted_response("Company deleted.")

    def _representation(self, company):
        # Re-read through get_queryset() so contacts_count is included.
        return self.get_serializer(self.get_queryset().get(pk=company.pk)).data


class ContactViewSet(OrganizationScopedViewSet):
    model = Contact
    permission_resource = "contact"
    serializer_class = ContactSerializer
    filterset_class = ContactFilter
    search_fields = ["full_name", "email", "phone", "role"]
    ordering_fields = ["full_name", "email", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return super().get_queryset().select_related("company")  # for company_name

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = services.create_contact(user=request.user, data=serializer.validated_data)
        return Response(self.get_serializer(contact).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        contact = self.get_object()
        serializer = self.get_serializer(
            contact, data=request.data, partial=kwargs.get("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        contact = services.update_contact(
            user=request.user, contact=contact, data=serializer.validated_data
        )
        return Response(self.get_serializer(contact).data)

    def destroy(self, request, *args, **kwargs):
        services.delete_contact(user=request.user, contact=self.get_object())
        return deleted_response("Contact deleted.")
