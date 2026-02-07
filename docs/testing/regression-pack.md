# Regression Test Pack

This document defines manual E2E tests to verify system functionality. An agent executes these tests after each phase to catch regressions and verify the system works as expected.

---

## How to Use This Document

### For Agents Executing Tests

1. Read this entire document to understand the test structure
2. Execute each test scenario in order, starting from Phase 1
3. For each test:
   - Follow the steps exactly as written
   - Verify the expected outcome matches actual behavior
   - Record PASS or FAIL with details
4. Report results in the format specified below
5. If any test fails, do NOT close the regression task - create a blocking bug

### For Agents Adding Tests

After completing a phase, add new test scenarios to this document:
1. Create a new section for the phase if it doesn't exist
2. Add tests that verify the phase's key functionality
3. Tests should be:
   - Reproducible (clear steps)
   - Verifiable (clear expected outcomes)
   - Independent (don't depend on prior test state, except where noted)
4. Use the test ID format: `R{phase}-{number}` (e.g., R1-01, R2-03)

### Result Reporting Format

```
## Regression Test Results - [Date]

### Summary
- Total: X tests
- Passed: Y
- Failed: Z

### Details

R1-01: PASS
- Executed: [timestamp]
- Notes: Video uploaded and processed in 45 seconds

R1-02: FAIL
- Executed: [timestamp]
- Expected: Search returns video with timestamp links
- Actual: Search returned 0 results
- Error: OpenSearch index appears empty
```

---

## Prerequisites

Before running regression tests:

1. **Services Running**
   ```bash
   docker compose up -d
   # Verify all services healthy
   curl -s http://localhost:8000/api/health
   curl -s http://localhost:9200/_cluster/health
   ```

2. **Test Data Available**
   - `/data/test/videos/test_meeting_primary.mkv` exists
   - `/data/test/videos/test_meeting_long.mkv` exists (for multi-speaker tests)

3. **Clean State** (optional, for isolated testing)
   ```bash
   # Reset database to clean state
   docker compose exec backend alembic downgrade base
   docker compose exec backend alembic upgrade head
   ```

---

## Phase 1 Tests

### R1-01: Upload Video with Metadata

**Objective**: Verify video upload flow works end-to-end

**Steps**:
1. Navigate to http://localhost:3000/upload
2. Select file: `/data/test/videos/test_meeting_primary.mkv`
3. Enter metadata:
   - Title: "Regression Test Video"
   - Date: Today's date
   - Participants: "Alice, Bob"
   - Notes: "Regression test upload"
4. Click Upload
5. Observe upload progress

**Expected Outcome**:
- Upload completes without error
- Redirected to video page or library
- Video appears with status "processing" or "uploaded"

---

### R1-02: Video Processing Completes

**Objective**: Verify video processing pipeline works

**Precondition**: R1-01 completed successfully

**Steps**:
1. Navigate to the video detail page or library
2. Wait for status to change (poll every 10 seconds, max 5 minutes)
3. Observe final status

**Expected Outcome**:
- Status progresses: uploaded → processing → transcribing → chunking → indexing → ready
- Final status is "ready"
- No error status
- Thumbnail is visible

---

### R1-03: Transcript Generated with Speakers

**Objective**: Verify transcription with speaker diarization

**Precondition**: R1-02 completed (status = ready)

**Steps**:
1. Navigate to video page: http://localhost:3000/videos/{id}
2. Scroll through transcript panel
3. Look for speaker labels

**Expected Outcome**:
- Transcript text is visible
- Speaker labels present (e.g., "SPEAKER_00:", "SPEAKER_01:")
- Timestamps visible for segments
- Transcript content roughly matches audio content

---

### R1-04: Search Finds Video Content

**Objective**: Verify hybrid search works

**Precondition**: R1-02 completed (video indexed)

**Steps**:
1. Navigate to http://localhost:3000/search
2. Enter a search term that appears in the test video transcript
3. Submit search
4. Review results

**Expected Outcome**:
- Search returns at least one result
- Result shows video title
- Result shows matching text snippet
- Result shows timestamp

---

### R1-05: Timestamp Navigation Works

**Objective**: Verify clicking timestamps navigates video

**Precondition**: R1-04 completed (search result available)

**Steps**:
1. From search results, click on a timestamp link
2. Observe video player

**Expected Outcome**:
- Navigated to video page
- Video player seeks to correct timestamp (±2 seconds)
- URL includes timestamp parameter (e.g., ?t=123)

---

### R1-06: Transcript Sync During Playback

**Objective**: Verify transcript highlights sync with video

**Precondition**: Video page loaded with transcript

**Steps**:
1. Click play on video
2. Observe transcript panel during playback
3. Let video play for 30+ seconds

**Expected Outcome**:
- Current segment is highlighted
- Highlight moves as video progresses
- Transcript auto-scrolls to keep current segment visible

---

### R1-07: Click Transcript to Seek

**Objective**: Verify clicking transcript segment seeks video

**Precondition**: Video page loaded

**Steps**:
1. Click on a segment in the middle of the transcript
2. Observe video player

**Expected Outcome**:
- Video seeks to that segment's start time
- Clicked segment becomes highlighted

---

### R1-08: Library Displays Videos

**Objective**: Verify library view works

**Precondition**: At least one video uploaded

**Steps**:
1. Navigate to http://localhost:3000/ or /library
2. Observe video list

**Expected Outcome**:
- Video cards displayed
- Each card shows: thumbnail, title, status, date
- Status badges have appropriate colors

---

### R1-09: Library Filtering Works

**Objective**: Verify library filtering

**Precondition**: Videos in various states (or at least one ready video)

**Steps**:
1. On library page, use status filter to select "Ready"
2. Observe filtered results

**Expected Outcome**:
- Only videos with status "ready" are shown
- Filter UI reflects current selection

---

### R1-10: Error Handling - Corrupted Video

**Objective**: Verify graceful error handling

**Steps**:
1. Navigate to upload page
2. Upload `/data/test/videos/test_corrupted.mkv`
3. Enter valid metadata
4. Submit and wait for processing

**Expected Outcome**:
- Upload succeeds
- Processing eventually fails
- Status shows "error"
- Error message is displayed (descriptive, not stack trace)
- System remains stable (other operations still work)

---

## Phase 2 Tests

*To be added after Phase 2 implementation*

---

## Phase 3 Tests

*To be added after Phase 3 implementation*

---

## Notes

- Tests are cumulative: when running Phase N regression, run all tests from Phase 1 through Phase N
- If a test fails, document exactly what happened before creating a bug report
- Some tests have preconditions - run tests in order within a phase
- After fixing a regression, re-run the full regression pack to ensure no new issues
