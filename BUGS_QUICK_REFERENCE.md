# Quick Reference Bug List

## 🚨 CRITICAL - Fix Immediately

1. **Exposed Strava API Credentials** - `explored_unused_solutions/strava/strava_dat.py:8`
   - Revoke key, use environment variables

2. **Missing Dependencies for Runtime** - Backend won't run without pip install
   - Improve setup documentation
   - Add dependency checker

## 🔴 HIGH PRIORITY - Fix This Sprint

### Security Issues
3. **Unsafe eval() usage** - `explored_unused_solutions/Garmin/process_data.py:133, 137`
   - Replace with ast.literal_eval()

4-6. **Dangerous function usage** - Multiple QA test files
   - Review __import__ usage in test code

### Error Handling
7-24. **Missing exception handling** (18 instances)
   - `backend/app/tasks.py:18, 52, 93`
   - `backend/app/api/routes/explainability.py:73, 122, 207, 279, 372, 478`
   - `backend/app/services/explainability.py:64, 118, 199, 266, 324, 448`
   - `backend/app/services/validation_service.py:86`
   - Add try/except/finally blocks

25-27. **Bare except clauses** (3 instances)
   - `backend/app/services/preprocessing_service.py:196, 210`
   - `backend/app/services/validation_service.py:315, 338`
   - Specify exception types

### API Design
28-34. **Missing HTTP status codes** (7 instances)
   - `backend/app/api/routes/preprocessing.py` (3)
   - `backend/app/api/routes/validation.py` (1)
   - `backend/app/api/routes/data_generation.py` (3)
   - Add status codes: 400, 404, 500

## 🟡 MEDIUM PRIORITY - Fix Next Sprint

35. **Frontend error handling** - `frontend/src/api/index.js`
    - Add axios error interceptor

36-40. **Services returning None** (5 instances)
    - `backend/app/services/*_service.py`
    - Add None checks in callers

41. **DEBUG=True in config** - `backend/app/config.py`
    - Ensure production config uses DEBUG=False

42-241. **Debug print() statements** (200+ instances)
    - Replace with proper logging

## 🟢 LOW PRIORITY - Technical Debt

242. **TODO/FIXME comments** - Various files
     - Review and create tickets

243. **Missing input validation** - Some API routes
     - Add additional validation

244. **File path security** - File operations
     - Add path traversal protection

## Summary by Numbers
- **Total Bugs:** 244 (including 200+ print statements)
- **Critical:** 2
- **High:** 27
- **Medium:** 212 (mostly print statements)
- **Low:** 3

## Quick Fix Commands

### Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Setup environment variables
```bash
# Create .env file
cat > .env << EOF
STRAVA_CLIENT_SECRET=your_secret_here
FLASK_ENV=development
DEBUG=True
EOF
```

### Replace print with logging (example)
```python
# Old
print(f"Processing {item}")

# New
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing {item}")
```

### Add exception handling (example)
```python
# Old
try:
    result = process()
finally:
    cleanup()

# New
try:
    result = process()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
finally:
    cleanup()
```

### Add HTTP status codes (example)
```python
# Old
return jsonify({'error': 'Not found'})

# New
return jsonify({'error': 'Not found'}), 404
```

## Files to Review

### Critical Files
- `explored_unused_solutions/strava/strava_dat.py` - Exposed credentials
- `backend/requirements.txt` - Dependencies
- `backend/app/config.py` - Configuration
- `.env.example` - Should exist for reference

### High Priority Files
- `backend/app/tasks.py` - Task error handling
- `backend/app/api/routes/explainability.py` - Route error handling
- `backend/app/services/explainability.py` - Service error handling
- `backend/app/services/preprocessing_service.py` - Bare except
- `backend/app/services/validation_service.py` - Bare except

### Medium Priority Files
- `frontend/src/api/index.js` - Frontend error handling
- All service files - None return handling
- All Python files - Replace print() with logging

## Test Commands

### Run QA tests
```bash
python qa_test_suite.py
python code_analysis_test.py
```

### Check for hardcoded secrets
```bash
grep -r "secret\s*=\s*['\"]" --include="*.py" .
grep -r "password\s*=\s*['\"]" --include="*.py" .
grep -r "api.*key\s*=\s*['\"]" --include="*.py" .
```

### Find print statements
```bash
grep -n "print(" --include="*.py" -r backend/ | wc -l
```

### Find bare except clauses
```bash
grep -n "except\s*:" --include="*.py" -r backend/
```
