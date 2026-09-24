"""
DRF views for RBI Registry endpoints.

Read-only for now. Write operations come with Phase 4 (editor workflow).
"""
from collections import defaultdict
from django.db.models import Count
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rbi_registry_app.pipeline import (
    run_full_pipeline, MDMetadata, PipelineError
)

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


class DraftAmendmentViewSet(viewsets.ModelViewSet):
    """GET    /api/rbi/drafts/       — list all drafts
       GET    /api/rbi/drafts/{id}/  — one draft
       POST   /api/rbi/drafts/       — create a new draft
       PUT    /api/rbi/drafts/{id}/  — replace an existing draft
       PATCH  /api/rbi/drafts/{id}/  — partial update
       DELETE /api/rbi/drafts/{id}/  — delete a draft

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
class ViewablePersonasView(APIView):
    """GET /api/rbi/personas/

    Returns the list of dummy users available for "Viewing as" persona switching.
    Each persona bundles user + their primary WorkingUnit info in one call,
    so the frontend dropdown doesn't need multiple fetches.

    Not a general "list users" endpoint — deliberately narrow for the POC's
    persona-switching use case.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Only dummy users (those with an @rbi.org.in email) — exclude the
        # superuser sudaditya. In production, this whole endpoint goes away
        # once we have real auth.
        users = User.objects.filter(
            email__endswith='@rbi.org.in'
        ).prefetch_related('unit_memberships__unit').order_by('first_name')

        personas = []
        for user in users:
            primary = user.unit_memberships.filter(is_primary=True).first()
            if not primary:
                continue
            personas.append({
                'user_id': user.id,
                'username': user.username,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'unit_id': primary.unit.id,
                'unit_name': primary.unit.name,
                'unit_short_code': primary.unit.short_code,
                'division': primary.unit.division,
                'division_display': primary.unit.get_division_display(),
            })

        return Response({'personas': personas})
    

class UploadMDView(APIView):
    """POST /api/rbi/upload-md/

    Multi-part upload endpoint. Accepts:
      - pdf_file:  PDF file (multipart)
      - number:    MD number (form field, e.g. "290")
      - date:      publication date, YYYY-MM-DD (form field)
      - title:     full RBI title (form field)

    Runs the full pipeline (PDF → text → AKN → Work), returns the created Work.

    Timing note: Gemini call can take 30-60s. Frontend must show a spinner.
    Django's default request timeout is fine (0 = no timeout for dev server).

    Errors are returned as JSON with a 'detail' key. Common cases:
      - 400: missing fields, bad PDF, invalid date, duplicate FRBR URI
      - 429: Gemini daily quota exhausted (mapped from pipeline)
      - 503: Gemini temporarily unavailable
      - 500: unexpected pipeline failure
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        # --- Validate required fields ---
        pdf_file = request.FILES.get('pdf_file')
        number = request.data.get('number', '').strip()
        date = request.data.get('date', '').strip()
        title = request.data.get('title', '').strip()

        errors = {}
        if not pdf_file:
            errors['pdf_file'] = 'PDF file is required.'
        if not number:
            errors['number'] = 'MD number is required.'
        if not date:
            errors['date'] = 'Publication date is required (YYYY-MM-DD).'
        if not title:
            errors['title'] = 'Title is required.'
        if errors:
            return Response(
                {'detail': 'Missing required fields.', 'errors': errors},
                status=400,
            )

        # --- Basic validation ---
        if not pdf_file.name.lower().endswith('.pdf'):
            return Response(
                {'detail': 'File must be a PDF.'},
                status=400,
            )
        # Reasonable size cap: 25 MB. RBI MDs are typically 5-50 pages.
        if pdf_file.size > 25 * 1024 * 1024:
            return Response(
                {'detail': f'File too large ({pdf_file.size} bytes). Max 25 MB.'},
                status=400,
            )

        # --- Run the pipeline ---
        meta = MDMetadata(number=number, date=date, title=title)
        pdf_bytes = pdf_file.read()

        try:
            work = run_full_pipeline(pdf_bytes, meta)
        except PipelineError as e:
            # Map known pipeline errors to appropriate HTTP status
            msg = str(e)
            if 'quota' in msg.lower() or 'exhausted' in msg.lower():
                status = 429
            elif 'temporarily unavailable' in msg.lower():
                status = 503
            elif 'already exists' in msg.lower():
                status = 400
            else:
                status = 400
            return Response({'detail': msg}, status=status)
        except Exception as e:
            # Unexpected — log the full traceback for debugging
            import logging
            logging.getLogger(__name__).exception('Upload pipeline crashed')
            return Response(
                {'detail': f'Unexpected error: {e}'},
                status=500,
            )

        # --- Success — return the new Work's info ---
        return Response({
            'id': work.id,
            'frbr_uri': work.frbr_uri,
            'numbered_title': work.numbered_title,
            'title': work.title,
            'publication_date': str(work.publication_date),
        }, status=201)