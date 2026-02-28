# Database Schema Changes

## 2026-02-28: Filter Approach Update

### Changes Made

 #### 1. Filter Logic (`rules/filters.py`)
- **Issue Found**: INCLUDE_PATTERNS were defined but not checked in the logic
- **Fix Applied**: Restored INCLUDE patterns check:
```python
# 2. Include check (MUST match at least one leadership keyword)
if INCLUDE_PATTERNS:
    if not any(p.search(combined) for p in INCLUDE_PATTERNS):
        return False
```

**Current Logic** (working correctly):
1. **EXCLUDE check** - reject if matches internship/junior/unpaid/volunteer
2. **INCLUDE check** - must match at least one data/AI/ML/leadership keyword
3. **REMOTE check** - accept from anywhere if remote
4. **LOCAL check** - must match Rheinland cities if not remote

 **Result**: Jobs are saved if they pass EXCLUDE AND match at least one INCLUDE pattern.

#### 2. Pipeline Summary (`scraper/pipeline.py`)
- **Current Logic**: Jobs saved if they pass EXCLUDE filters AND match INCLUDE patterns
- **Summary Format**: `Done. Found: X | Excluded: Y | New: Z`
- **Changes**:
  - `total_matched` → `total_excluded` (tracked in ScrapeRun model)
  - Summary message updated to show excluded count
  - Stored jobs = all jobs that pass EXCLUDE filters AND match INCLUDE patterns

#### 3. Database Model Comments (`db/models.py`)
- Added module docstring explaining the new filter approach
- Clarified `jobs_matched` column now tracks jobs that pass EXCLUDE filters

### Database Columns

| Column | Type | Description |
|---------|------|-------------|
| jobs_found | Integer | Total jobs parsed from pages |
| jobs_matched | Integer | Jobs that passed EXCLUDE filters (stored to DB) |
| jobs_new | Integer | New jobs inserted (not duplicates) |

### EXCLUDE Filters (still active)

- `internship|praktikum|werkstudent|working*student|pflichtpraktikum`
- `junior|trainee|azubi|ausbildung`
- `unpaid|volunteer|ehrenamt`

Jobs matching any EXCLUDE pattern are rejected. All others are saved to database.

### Location Filters (still active)

- **Remote jobs** (80-100%) - accepted from anywhere
- **Local jobs** - must match Rheinland ~50km from Monheim:
  - Düsseldorf, Köln, Bonn, Leverkusen, Wuppertal, Solingen
  - Neuss, Dormagen, Moers, Krefeld, Mönchengladbach
  - Bergisch Gladbach, Remscheid, Siegen
  - NRW (North Rhine-Westphalia)

### Migration Note

No database migration required. Column names preserved for backwards compatibility.
- `jobs_matched` now represents "jobs passing EXCLUDE filters AND matching INCLUDE patterns (stored to DB)"
- Old `jobs_matched` data would still be valid (semantic shift, not data loss)

### Expected Results

With restored INCLUDE patterns:
- **Amazon**: Expected to save few leadership/management roles in data/AI/ML/engineering
- **Apple**: Expected to save more leadership/management roles (data/AI/ML/engineering, Germany-based)
- **Excluded jobs**: Only those matching EXCLUDE patterns (internship, junior, unpaid)
- **Behavior**:
  - Jobs like "Data Engineer", "ML Manager" → Pass EXCLUDE ✓ + Pass INCLUDE ✓ → **SAVED**
  - Jobs like "Specialist", "Retail" → Pass EXCLUDE ✓ + Fail INCLUDE ✗ → **NOT SAVED**
## 2026-02-28: Filter Approach Update

### Changes Made
#### 1. Filter Logic (`rules/filters.py`)
- **Change**: Removed INCLUDE patterns check from scraping stage
- **Two-Stage Approach**: EXCLUDE-only scraping, INCLUDE-based refinement

**Rationale**: Collect broader dataset while blocking unwanted jobs.
### Two-Stage Workflow

1. **Scraping Stage** (`main.py scrape`):
   - Apply EXCLUDE patterns only
   - Save all non-excluded jobs to DB
   - Collect broad dataset

2. **Refinement Stage** (future - to be implemented):
   - Query DB with INCLUDE patterns
   - Identify leadership/management roles
   - Scrape detail pages for identified roles
   - Enrich with additional data
   - Update records in DB

This approach allows data-driven refinement while still filtering clearly unwanted positions at the scrape stage.
