from django.db.models import Count
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.models import ActivityLog
from apps.activity.serializers import ActivityLogSerializer
from apps.core.permissions import HasOrganization
from apps.crm.models import Company, Contact
from apps.organizations.roles import PERMISSION_MATRIX


class DashboardStatsView(APIView):
    """Headline numbers for the user's organization. Every query is org-scoped."""

    permission_classes = [IsAuthenticated, HasOrganization]

    @extend_schema(
        tags=["dashboard"],
        responses=inline_serializer(
            "DashboardStats",
            {
                "organization": inline_serializer(
                    "DashboardOrganization",
                    {"name": serializers.CharField(), "subscription_plan": serializers.CharField()},
                ),
                "totals": inline_serializer(
                    "DashboardTotals",
                    {
                        "companies": serializers.IntegerField(),
                        "contacts": serializers.IntegerField(),
                    },
                ),
                "companies_by_industry": inline_serializer(
                    "IndustryCount",
                    {"industry": serializers.CharField(), "count": serializers.IntegerField()},
                    many=True,
                ),
                "recent_activity": ActivityLogSerializer(many=True),
            },
        ),
    )
    def get(self, request):
        user = request.user
        org = user.organization
        companies = Company.objects.for_org(org)
        by_industry = (
            companies.values("industry").annotate(count=Count("id")).order_by("-count", "industry")
        )[:8]

        # Recent activity follows the same rule as the activity log endpoint.
        recent_activity = []
        if user.role in PERMISSION_MATRIX["activity_log"]["read"]:
            logs = ActivityLog.objects.for_org(org).select_related("user")[:5]
            recent_activity = ActivityLogSerializer(logs, many=True).data

        return Response(
            {
                "organization": {"name": org.name, "subscription_plan": org.subscription_plan},
                "totals": {
                    "companies": companies.count(),
                    "contacts": Contact.objects.for_org(org).count(),
                },
                "companies_by_industry": [
                    {"industry": row["industry"] or "Unspecified", "count": row["count"]}
                    for row in by_industry
                ],
                "recent_activity": recent_activity,
            }
        )
