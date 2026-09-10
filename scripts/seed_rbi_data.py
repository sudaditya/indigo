"""
Seed RBI-specific reference and dummy data.

Populates:
- WorkingUnits from the DoR organogram (~34 units)
- 10 dummy users
- UnitMemberships (each user has one primary unit)
- MDOwnerships for the 3 loaded MDs
- 7 dummy DraftAmendments, deliberately including conflict scenarios

Safe to re-run: deletes existing RBI-app data first (leaves Indigo data alone).
Runs INSIDE the Docker container:

    docker compose exec web python scripts/seed_rbi_data.py
"""
import os
import sys
from pathlib import Path

# Add /app to sys.path so Django can find rbi_registry_app.
# (indigo_api is pip-installed and always importable; rbi_registry_app
# is just a folder in the repo, so its parent must be on sys.path.)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'indigo.settings')
django.setup()

from django.contrib.auth import get_user_model
from indigo_api.models import Work
from rbi_registry_app.models import (
    WorkingUnit, UnitMembership, MDOwnership, DraftAmendment
)

User = get_user_model()


# ----------------------------------------------------------------------
# WorkingUnit definitions — sourced from Organogram.xlsx
# Format: (name, short_code, division, group_name)
# When a Group has no sub-Sections, we register the Group itself as the
# working unit — in those rows, name == group_name.
# ----------------------------------------------------------------------
WORKING_UNITS = [
    # === Prudential Regulation Division (PRD) ===
    # Internal Services Group
    ('HR Section', 'HR', 'PRD', 'Internal Services Group'),
    ('Information Section', 'INFO', 'PRD', 'Internal Services Group'),
    ('RIA Section', 'RIA', 'PRD', 'Internal Services Group'),
    ('Rajbhasha Section', 'RAJ', 'PRD', 'Internal Services Group'),
    ('Regulatory Review Cell', 'RRC', 'PRD', 'Internal Services Group'),
    ('Parliament Matters Coordination Cell', 'PMCC', 'PRD', 'Internal Services Group'),

    # Specialized Institutions Group
    ('Financial Institutions Section – NBFCs', 'FIS-N', 'PRD', 'Specialized Institutions Group'),
    ('Financial Institutions Section – CIC', 'FIS-C', 'PRD', 'Specialized Institutions Group'),

    # Market & Liquidity Risk Group — group-level (no sub-sections)
    ('Market & Liquidity Risk Group', 'MLR', 'PRD', 'Market & Liquidity Risk Group'),

    # Balance Sheet Group
    ('Capital Section', 'CAP', 'PRD', 'Balance Sheet Group'),
    ('Accounting Section', 'ACC', 'PRD', 'Balance Sheet Group'),

    # Group-level units
    ('Strategy, Research & Analysis Group', 'SRA', 'PRD', 'Strategy, Research & Analysis Group'),
    ('Operational Risk Group', 'OPR', 'PRD', 'Operational Risk Group'),
    ('New Tech and Model Risk Group', 'NRG', 'PRD', 'New Tech and Model Risk Group'),
    ('Sustainable Finance Group', 'SFG', 'PRD', 'Sustainable Finance Group'),

    # Credit Risk Group
    ('Credit Risk Section', 'CRS', 'PRD', 'Credit Risk Group'),
    ('Stressed Assets Section', 'STA', 'PRD', 'Credit Risk Group'),

    # === Conduct and Operations Division (COD) ===
    # Holding & Governance Group
    ('Holding Section', 'HOLD', 'COD', 'Holding & Governance Group'),
    ('Governance Section (Banks)', 'GOV-B', 'COD', 'Holding & Governance Group'),
    ('Governance Section (Cooperative Banks & NBFCs)', 'GOV-CN', 'COD', 'Holding & Governance Group'),
    ('Nodal Team for UCBs', 'NT-UCB', 'COD', 'Holding & Governance Group'),

    # Registration & Authorization Group
    ('Registration & Licensing Section (Banks)', 'RL-B', 'COD', 'Registration & Authorization Group'),
    ('Authorization Section', 'AUTH', 'COD', 'Registration & Authorization Group'),
    ('Registration, Licensing & Authorization Section (NBFCs)', 'RLA-N', 'COD', 'Registration & Authorization Group'),
    ('Registration & Licensing Section (Cooperative Banks)', 'RL-C', 'COD', 'Registration & Authorization Group'),

    # Statutory Operations Group
    ('Returns Section', 'RET', 'COD', 'Statutory Operations Group'),
    ('Special Operation Section', 'SPO', 'COD', 'Statutory Operations Group'),
    ('Legislation Section', 'LEG', 'COD', 'Statutory Operations Group'),
    ('DEA Fund Section', 'DEA', 'COD', 'Statutory Operations Group'),

    # Resolution Group
    ('Monitoring Section', 'MON', 'COD', 'Resolution Group'),
    ('Merger & Acquisition Section', 'MNA', 'COD', 'Resolution Group'),
    ('Liquidation Section', 'LIQ', 'COD', 'Resolution Group'),

    # Regulatory Co-ordination Group — group-level
    ('Regulatory Co-ordination Group', 'RCG', 'COD', 'Regulatory Co-ordination Group'),

    # Business Conduct Group
    ('Market Conduct Section', 'MCS', 'COD', 'Business Conduct Group'),
    ('AML Section', 'AML', 'COD', 'Business Conduct Group'),
]


# ----------------------------------------------------------------------
# Dummy users — realistic-looking Indian names, one per key unit for demo
# Format: (username, first_name, last_name, email, primary_unit_short_code)
# ----------------------------------------------------------------------
DUMMY_USERS = [
    ('priya.kulkarni',  'Priya',   'Kulkarni',  'priya.kulkarni@rbi.org.in',  'ACC'),      # MD 290 author
    ('arjun.iyer',      'Arjun',   'Iyer',      'arjun.iyer@rbi.org.in',      'GOV-CN'),   # MD 290 conflicting author
    ('rohan.mehta',     'Rohan',   'Mehta',     'rohan.mehta@rbi.org.in',     'SFG'),      # MD 172 primary author (2 drafts)
    ('nisha.rao',       'Nisha',   'Rao',       'nisha.rao@rbi.org.in',       'CRS'),      # MD 172 + MD 356 conflicting author
    ('vikram.singh',    'Vikram',  'Singh',     'vikram.singh@rbi.org.in',    'STA'),      # MD 356 nodal author
    ('kavya.nair',      'Kavya',   'Nair',      'kavya.nair@rbi.org.in',      'FIS-N'),    # secondary NBFC person
    ('rajesh.patel',    'Rajesh',  'Patel',     'rajesh.patel@rbi.org.in',    'CAP'),      # non-authoring — for coordinator dashboard
    ('ananya.desai',    'Ananya',  'Desai',     'ananya.desai@rbi.org.in',    'MCS'),
    ('siddharth.gupta', 'Siddharth', 'Gupta',   'siddharth.gupta@rbi.org.in', 'RRC'),
    ('divya.sharma',    'Divya',   'Sharma',    'divya.sharma@rbi.org.in',    'LEG'),
]


def wipe_existing():
    """Delete all RBI-app data. Leaves Indigo data alone."""
    print("Wiping existing RBI-app data...")
    DraftAmendment.objects.all().delete()
    MDOwnership.objects.all().delete()
    UnitMembership.objects.all().delete()
    # Delete only OUR dummy users, leave the real sudaditya user alone
    dummy_usernames = [u[0] for u in DUMMY_USERS]
    User.objects.filter(username__in=dummy_usernames).delete()
    WorkingUnit.objects.all().delete()
    print("  Cleared.")


def seed_units():
    print(f"\nSeeding {len(WORKING_UNITS)} WorkingUnits...")
    for name, code, division, group in WORKING_UNITS:
        WorkingUnit.objects.create(
            name=name, short_code=code, division=division, group_name=group
        )
    print(f"  Created {WorkingUnit.objects.count()} units")


def seed_users_and_memberships():
    print(f"\nSeeding {len(DUMMY_USERS)} dummy users + primary memberships...")
    for username, first, last, email, unit_code in DUMMY_USERS:
        user = User.objects.create_user(
            username=username,
            first_name=first,
            last_name=last,
            email=email,
            password='demo1234',  # dummy password, dev only
        )
        unit = WorkingUnit.objects.get(short_code=unit_code)
        UnitMembership.objects.create(user=user, unit=unit, is_primary=True)
    print(f"  Created {User.objects.count()} total users "
          f"({UnitMembership.objects.count()} memberships)")


def seed_mdownerships():
    print("\nSeeding MDOwnership for 3 loaded MDs...")
    # (Work id, nodal unit short_code) — Work IDs verified from API earlier
    assignments = [
        (7,  'ACC'),   # MD 290 — Accounting Section
        (12, 'SFG'),   # MD 172 — Sustainable Finance Group
        (13, 'STA'),   # MD 356 — Stressed Assets Section
    ]
    for work_id, unit_code in assignments:
        work = Work.objects.get(id=work_id)
        unit = WorkingUnit.objects.get(short_code=unit_code)
        MDOwnership.objects.create(work=work, nodal_unit=unit)
        print(f"  {work.numbered_title} → {unit.short_code} ({unit.name})")


def seed_drafts():
    """Seed 7 dummy drafts including 2 deliberate conflict scenarios."""
    print("\nSeeding 7 dummy DraftAmendments...")

    # Fetch users and units we'll need
    priya   = User.objects.get(username='priya.kulkarni')     # ACC — MD 290 nodal
    arjun   = User.objects.get(username='arjun.iyer')         # GOV-CN — same-target conflict on MD 290
    rohan   = User.objects.get(username='rohan.mehta')        # SFG — MD 172 nodal
    nisha   = User.objects.get(username='nisha.rao')          # CRS — cross-unit input on 172 + 356
    vikram  = User.objects.get(username='vikram.singh')       # STA — MD 356 nodal

    md_290 = Work.objects.get(id=7)
    md_172 = Work.objects.get(id=12)
    md_356 = Work.objects.get(id=13)

    def unit_of(user):
        return UnitMembership.objects.get(user=user, is_primary=True).unit

    drafts = [
        # === MD 290: SAME-TARGET CONFLICT (both drafts modifying same clause) ===
        {
            'work': md_290,
            'target_eid': 'chp_II__para_6__ii',
            'change_type': 'modify',
            'proposed_text': 'NNPA ratio shall be less than four per cent, after making all '
                             'necessary provisions (including provisions required as per assessment '
                             'made by the Reserve Bank in the last inspection report), for the '
                             'financial year for which dividend is proposed;',
            'rationale': 'Tightening NNPA threshold in line with proposed capital adequacy revisions.',
            'status': 'in_review',
            'author_user': priya,
        },
        {
            'work': md_290,
            'target_eid': 'chp_II__para_6__ii',
            'change_type': 'modify',
            'proposed_text': 'NNPA ratio shall be less than three per cent, after making all '
                             'necessary provisions (including provisions required as per assessment '
                             'made by the Reserve Bank in the last inspection report), for the '
                             'financial year for which dividend is proposed;',
            'rationale': 'Governance perspective — stricter threshold aligned with cooperative bank '
                         'sector risk profile observed in 2026 supervisory cycle.',
            'status': 'draft',
            'author_user': arjun,
        },

        # === MD 172: 3 non-conflicting drafts (different paragraphs) ===
        {
            'work': md_172,
            'target_eid': 'chp_I__sec_C__para_4__n1',
            'change_type': 'modify',
            'proposed_text': "'green activities / projects' means activities / projects meeting "
                             "the requirements prescribed in paragraph 14 of these Directions, "
                             "including projects certified under the ICMA Green Bond Principles.",
            'rationale': 'Add explicit reference to international certification standards.',
            'status': 'draft',
            'author_user': rohan,
        },
        {
            'work': md_172,
            'target_eid': 'chp_III__sec_C__para_10',
            'change_type': 'insert',
            'proposed_text': 'Banks shall also disclose the geographical distribution of green '
                             'deposits raised, at the state level, in their annual disclosures.',
            'rationale': 'Enhance regional visibility of green finance flows for policy analysis.',
            'status': 'in_review',
            'author_user': rohan,
        },
        {
            'work': md_172,
            'target_eid': 'chp_III__sec_F__para_17',
            'change_type': 'modify',
            'proposed_text': 'A bank shall, with the assistance of external firms accredited by '
                             'the RBI, assess annually the impact associated of the funds lent for '
                             'or invested in green finance activities / projects during a financial '
                             'year through an Impact Assessment Report.',
            'rationale': 'Restrict impact-assessment firms to those on an RBI accreditation list, '
                         'consistent with credit-risk oversight practice.',
            'status': 'draft',
            'author_user': nisha,
        },

        # === MD 356: DELETE-VS-EDIT CONFLICT ===
        {
            'work': md_356,
            'target_eid': 'chp_II__para_5',
            'change_type': 'modify',
            'proposed_text': 'An NBFC shall recognize income on its non-performing assets only on '
                             'realization basis, in accordance with the norms specified herein and '
                             'updated Reserve Bank inspection observations from time to time.',
            'rationale': 'Codify current supervisory practice explicitly in the direction text.',
            'status': 'in_review',
            'author_user': vikram,
        },
        {
            'work': md_356,
            'target_eid': 'chp_II__para_5',
            'change_type': 'delete',
            'proposed_text': '',
            'rationale': 'This provision has been superseded by the consolidated framework '
                         'notified in the Prudential Framework for Stressed Assets. Recommend '
                         'deletion to avoid overlap.',
            'status': 'draft',
            'author_user': nisha,
        },
    ]

    for d in drafts:
        DraftAmendment.objects.create(
            work=d['work'],
            target_eid=d['target_eid'],
            change_type=d['change_type'],
            proposed_text=d['proposed_text'],
            rationale=d['rationale'],
            status=d['status'],
            author_user=d['author_user'],
            author_unit=unit_of(d['author_user']),
        )

    print(f"  Created {DraftAmendment.objects.count()} drafts")


def summary():
    print("\n" + "=" * 60)
    print("SEED COMPLETE")
    print("=" * 60)
    print(f"WorkingUnits:     {WorkingUnit.objects.count()}")
    print(f"Users:            {User.objects.count()} (incl. non-dummy)")
    print(f"UnitMemberships:  {UnitMembership.objects.count()}")
    print(f"MDOwnerships:     {MDOwnership.objects.count()}")
    print(f"DraftAmendments:  {DraftAmendment.objects.count()}")

    print("\nDrafts by MD:")
    for work in [Work.objects.get(id=7), Work.objects.get(id=12), Work.objects.get(id=13)]:
        drafts = DraftAmendment.objects.filter(work=work)
        print(f"  {work.numbered_title}: {drafts.count()} drafts")
        for d in drafts:
            print(f"    - {d.get_change_type_display()} {d.target_eid} "
                  f"by {d.author_unit.short_code} [{d.status}]")


if __name__ == '__main__':
    wipe_existing()
    seed_units()
    seed_users_and_memberships()
    seed_mdownerships()
    seed_drafts()
    summary()