"""
RBI Registry — data models for cross-team amendment coordination.

These sit alongside Indigo's models (indigo_api.Work, indigo_api.Document)
and reference them via ForeignKey. Structure:

    WorkingUnit          — DoR Section or group-level unit
    UnitMembership       — Users belong to WorkingUnits (M2M with primary)
    MDOwnership          — Nodal WorkingUnit for each Master Direction
    DraftAmendment       — In-flight proposed changes to MDs (core entity)

The dashboard consumes these via read-only endpoints in views.py.
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class WorkingUnit(models.Model):
    """A DoR working unit — either a Section (leaf) or a Group (if the Group has no sub-Sections).

    RBI DoR structure:
      Department
        ├── Prudential Regulation Division (PRD)
        │     ├── Group 1
        │     │     ├── Section A       ← working unit
        │     │     └── Section B       ← working unit
        │     └── Group 2               ← working unit (no sub-Sections)
        └── Conduct and Operations Division (COD)
              └── ... (similar structure)
    """

    DIVISION_CHOICES = [
        ('PRD', 'Prudential Regulation Division'),
        ('COD', 'Conduct and Operations Division'),
    ]

    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Full display name, e.g. 'Accounting Section' or 'Sustainable Finance Group'"
    )
    short_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Short identifier for URLs / compact display, e.g. 'ACC' or 'SFG'"
    )
    division = models.CharField(max_length=3, choices=DIVISION_CHOICES)
    group_name = models.CharField(
        max_length=200,
        help_text="Parent Group name. Equal to `name` when this unit IS the group (no sub-Sections)."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['division', 'group_name', 'name']

    def __str__(self):
        return f"{self.name} ({self.short_code})"

    def is_group_level(self):
        """True if this WorkingUnit represents a Group with no sub-Sections."""
        return self.name == self.group_name


class UnitMembership(models.Model):
    """User's membership in a WorkingUnit.

    Users can belong to multiple units (secondments, dual roles).
    Exactly one membership per user should be marked is_primary=True
    (enforced by application code, not DB constraint — Django doesn't
    support conditional unique_together easily).
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unit_memberships')
    unit = models.ForeignKey(WorkingUnit, on_delete=models.CASCADE, related_name='memberships')
    is_primary = models.BooleanField(default=False)
    joined_at = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'unit')]
        indexes = [
            models.Index(fields=['user', 'is_primary']),
        ]

    def __str__(self):
        marker = " (primary)" if self.is_primary else ""
        return f"{self.user.username} @ {self.unit.short_code}{marker}"


class MDOwnership(models.Model):
    """Nodal WorkingUnit for each Master Direction.

    By default, any working unit may propose amendments to any MD
    (RBI DoR practice — cross-unit input is common). To restrict,
    set edit_restricted=True and populate denied_units.

    One-to-one with Indigo's Work: exactly one nodal owner per MD.
    """

    work = models.OneToOneField(
        'indigo_api.Work',
        on_delete=models.CASCADE,
        related_name='md_ownership'
    )
    nodal_unit = models.ForeignKey(
        WorkingUnit,
        on_delete=models.PROTECT,
        related_name='nodal_for_mds',
        help_text="The unit responsible for this MD; typically leads amendment reviews."
    )
    edit_restricted = models.BooleanField(
        default=False,
        help_text="If False, any working unit can edit. If True, edits are blocked "
                  "for units listed in denied_units."
    )
    denied_units = models.ManyToManyField(
        WorkingUnit,
        blank=True,
        related_name='denied_from_mds',
        help_text="Units explicitly denied edit rights. Only consulted if edit_restricted=True."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.work.numbered_title} — nodal: {self.nodal_unit.short_code}"


class DraftAmendment(models.Model):
    """A proposed change to a Master Direction, authored by a WorkingUnit.

    Core entity for the Coordination Dashboard. Enables:
    - Same-target conflict detection (multiple drafts on same eId)
    - Delete-vs-edit conflict detection (DELETE + MODIFY on same target)
    - Cross-team visibility (who's drafting what across the department)

    Held distinct from Indigo's Amendment model, which represents
    completed, approved amendments. Drafts here graduate to Indigo
    Amendments only after approval (Phase 4+ workflow, not yet built).
    """

    CHANGE_TYPES = [
        ('insert', 'Insert new provision'),
        ('modify', 'Modify existing text'),
        ('delete', 'Delete provision'),
        ('renumber', 'Renumber provisions'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    work = models.ForeignKey(
        'indigo_api.Work',
        on_delete=models.CASCADE,
        related_name='draft_amendments'
    )
    target_eid = models.CharField(
        max_length=200,
        help_text="AKN element ID being modified, e.g. 'chp_II__para_6__ii'. "
                  "Not a DB FK — validated as-existing in current MD by application logic."
    )
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    proposed_text = models.TextField(
        blank=True,
        help_text="The new content. Empty for change_type='delete'."
    )
    rationale = models.TextField(
        blank=True,
        help_text="Optional explanation of why this change is proposed."
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    author_user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='authored_amendments'
    )
    author_unit = models.ForeignKey(
        WorkingUnit,
        on_delete=models.PROTECT,
        related_name='amendments',
        help_text="Denormalized from author_user's primary UnitMembership at creation time. "
                  "Preserves historical attribution when users move between units."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['work', 'target_eid', 'status']),
            models.Index(fields=['author_unit', 'status']),
        ]

    def __str__(self):
        return f"{self.get_change_type_display()} on {self.target_eid} "\
               f"({self.work.numbered_title}) — {self.status}"