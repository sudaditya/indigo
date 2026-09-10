"""
DRF views for RBI Registry endpoints.

Read-only for now. Write operations come with Phase 4 (editor workflow).
"""
from collections import defaultdict
from django.db.models import Count
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from indigo_api.models import Work
from .models import WorkingUnit, MDOwnership, DraftAmendment
from .serializers import (
    WorkingUnitSerializer,
    MDOwnershipSerializer,
    DraftAmendmentSerializer,
    WorkBriefSerializer,
)


class WorkingUnitViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/rbi/units/         — list all working units
       GET /api/rbi/units/{id}/    — one unit
    """
    queryset = WorkingUnit.objects.all()
    serializer_class = WorkingUnitSerializer
    permission_classes = [permissions.IsAuthenticated]


class MDOwnershipViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/rbi/mds/         — list MDs with ownership + draft/conflict counts
       GET /api/rbi/mds/{id}/    — one MD's ownership
    """
    queryset = MDOwnership.objects.select_related('work', 'nodal_unit').all()
    serializer_class = MDOwnershipSerializer
    permission_classes = [permissions.IsAuthenticated]


class DraftAmendmentViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/rbi/drafts/       — list all drafts
       GET /api/rbi/drafts/{id}/  — one draft

    Supports filtering via query params:
      ?work=<id>            — drafts for a specific MD
      ?status=<value>       — drafts by status
      ?author_unit=<id>     — drafts by authoring unit
    """
    serializer_class = DraftAmendmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = DraftAmendment.objects.select_related(
            'work', 'author_user', 'author_unit'
        ).all()

        # Optional filters
        work_id = self.request.query_params.get('work')
        if work_id:
            qs = qs.filter(work_id=work_id)

        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)

        author_unit_id = self.request.query_params.get('author_unit')
        if author_unit_id:
            qs = qs.filter(author_unit_id=author_unit_id)

        return qs


class ConflictsView(APIView):
    """GET /api/rbi/conflicts/

    Compute conflicts across all MDs and return a structured list.

    Two conflict types surfaced:
    - same_target: multiple drafts on same eId
    - delete_vs_edit: DELETE + MODIFY (or other) on same eId

    Not stored — computed on demand. Fast enough for POC scale
    (7 drafts). Would move to cached view or materialized query
    at production scale.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Only active drafts count for conflicts
        active_drafts = DraftAmendment.objects.exclude(
            status__in=['withdrawn', 'rejected']
        ).select_related('work', 'author_unit', 'author_user')

        # Group drafts by (work_id, target_eid)
        by_target = defaultdict(list)
        for draft in active_drafts:
            by_target[(draft.work_id, draft.target_eid)].append(draft)

        conflicts = []
        for (work_id, eid), drafts in by_target.items():
            if len(drafts) < 2:
                continue  # No conflict — only one draft on this target

            change_types = {d.change_type for d in drafts}

            # Classify conflict type — delete-vs-edit is more urgent
            if 'delete' in change_types and change_types - {'delete'}:
                conflict_type = 'delete_vs_edit'
                severity = 'high'
            else:
                conflict_type = 'same_target'
                severity = 'medium'

            # Use the first draft's Work info (all share the same Work)
            work_info = WorkBriefSerializer(drafts[0].work).data

            conflicts.append({
                'conflict_type': conflict_type,
                'severity': severity,
                'work': work_info,
                'target_eid': eid,
                'draft_count': len(drafts),
                'drafts': DraftAmendmentSerializer(drafts, many=True).data,
            })

        # Sort by severity (high first), then by draft count
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        conflicts.sort(key=lambda c: (severity_order[c['severity']], -c['draft_count']))

        return Response({
            'count': len(conflicts),
            'conflicts': conflicts,
        })