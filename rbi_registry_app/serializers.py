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
    """Read/write serializer for DraftAmendment.

    On READ: returns nested work/author_user/author_unit objects with
    full detail (no follow-up API calls needed by frontend).

    On WRITE (POST/PATCH): accepts work_id, author_user_id, author_unit_id
    to identify relationships. The nested objects on read are read-only.
    """
    # Nested representations for GET responses (read-only)
    work = WorkBriefSerializer(read_only=True)
    author_user = UserBriefSerializer(read_only=True)
    author_unit = WorkingUnitSerializer(read_only=True)

    # Display versions of the choice fields (read-only)
    change_type_display = serializers.CharField(source='get_change_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Write-only fields for creating / updating relationships.
    # These are declared as generic IntegerFields, then validate_* methods
    # look up and attach the corresponding model instances during save.
    # This avoids DRF's PrimaryKeyRelatedField requiring a queryset at
    # class-definition time (which forces early imports).
    work_id = serializers.IntegerField(write_only=True)
    author_user_id = serializers.IntegerField(write_only=True)
    author_unit_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = DraftAmendment
        fields = [
            'id',
            'work', 'work_id',
            'target_eid',
            'change_type', 'change_type_display',
            'proposed_text', 'rationale',
            'status', 'status_display',
            'author_user', 'author_user_id',
            'author_unit', 'author_unit_id',
            'created_at', 'updated_at', 'submitted_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_work_id(self, value):
        from indigo_api.models import Work
        if not Work.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Work id={value} does not exist.")
        return value

    def validate_author_user_id(self, value):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"User id={value} does not exist.")
        return value

    def validate_author_unit_id(self, value):
        from .models import WorkingUnit
        if not WorkingUnit.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"WorkingUnit id={value} does not exist.")
        return value

    def create(self, validated_data):
        """Turn *_id fields into actual FK relationships on the model."""
        from indigo_api.models import Work
        from django.contrib.auth import get_user_model
        from .models import WorkingUnit

        # Pop the *_id fields and resolve to model instances
        work = Work.objects.get(id=validated_data.pop('work_id'))
        author_user = get_user_model().objects.get(id=validated_data.pop('author_user_id'))
        author_unit = WorkingUnit.objects.get(id=validated_data.pop('author_unit_id'))

        return DraftAmendment.objects.create(
            work=work,
            author_user=author_user,
            author_unit=author_unit,
            **validated_data,
        )

    def update(self, instance, validated_data):
        """Same treatment for PATCH/PUT: resolve *_id → instance if present."""
        from indigo_api.models import Work
        from django.contrib.auth import get_user_model
        from .models import WorkingUnit

        if 'work_id' in validated_data:
            instance.work = Work.objects.get(id=validated_data.pop('work_id'))
        if 'author_user_id' in validated_data:
            instance.author_user = get_user_model().objects.get(id=validated_data.pop('author_user_id'))
        if 'author_unit_id' in validated_data:
            instance.author_unit = WorkingUnit.objects.get(id=validated_data.pop('author_unit_id'))

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance