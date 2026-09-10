"""
DRF serializers for RBI Registry models.

For now these are read-only — every endpoint is GET. When we add
write endpoints (Phase 4, editor workflow), we'll add validation
logic to these classes.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import WorkingUnit, UnitMembership, MDOwnership, DraftAmendment

User = get_user_model()


class WorkingUnitSerializer(serializers.ModelSerializer):
    """Full detail for a working unit, including derived is_group_level."""
    is_group_level = serializers.SerializerMethodField()
    division_display = serializers.CharField(source='get_division_display', read_only=True)

    class Meta:
        model = WorkingUnit
        fields = [
            'id', 'name', 'short_code',
            'division', 'division_display',
            'group_name',
            'is_group_level',
        ]

    def get_is_group_level(self, obj):
        return obj.is_group_level()


class UserBriefSerializer(serializers.ModelSerializer):
    """Compact user representation for nesting inside drafts."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class WorkBriefSerializer(serializers.Serializer):
    """Compact Work representation. Not a ModelSerializer because
    indigo_api.Work is Indigo's model — we don't want to entangle
    our serializer layer with Indigo's."""
    id = serializers.IntegerField()
    frbr_uri = serializers.CharField()
    numbered_title = serializers.CharField()
    title = serializers.CharField()
    publication_date = serializers.DateField()


class MDOwnershipSerializer(serializers.ModelSerializer):
    """MD + its nodal owner, with just enough Work info to avoid a second fetch."""
    work = WorkBriefSerializer(read_only=True)
    nodal_unit = WorkingUnitSerializer(read_only=True)
    draft_count = serializers.SerializerMethodField()
    conflict_count = serializers.SerializerMethodField()

    class Meta:
        model = MDOwnership
        fields = [
            'id', 'work', 'nodal_unit', 'edit_restricted',
            'draft_count', 'conflict_count',
            'created_at', 'updated_at',
        ]

    def get_draft_count(self, obj):
        """Count of drafts on this MD that aren't withdrawn/rejected."""
        return obj.work.draft_amendments.exclude(
            status__in=['withdrawn', 'rejected']
        ).count()

    def get_conflict_count(self, obj):
        """Count of eIds on this MD with more than one active draft."""
        from django.db.models import Count
        conflicts = (
            obj.work.draft_amendments
            .exclude(status__in=['withdrawn', 'rejected'])
            .values('target_eid')
            .annotate(n=Count('id'))
            .filter(n__gt=1)
        )
        return conflicts.count()


class DraftAmendmentSerializer(serializers.ModelSerializer):
    """Full detail for a draft. Includes nested author + unit + work info."""
    work = WorkBriefSerializer(read_only=True)
    author_user = UserBriefSerializer(read_only=True)
    author_unit = WorkingUnitSerializer(read_only=True)
    change_type_display = serializers.CharField(source='get_change_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = DraftAmendment
        fields = [
            'id',
            'work',
            'target_eid',
            'change_type', 'change_type_display',
            'proposed_text', 'rationale',
            'status', 'status_display',
            'author_user', 'author_unit',
            'created_at', 'updated_at', 'submitted_at',
        ]