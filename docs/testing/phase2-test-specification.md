# Phase 2 Test Specification

**Phase**: Conversational AI (Quick Mode)
**Goal**: Pre-fetched context, quick answers, results workspace
**Stories Covered**: S7, S8, S9, S2, S10, V4

---

## Table of Contents

1. [Test Strategy Overview](#1-test-strategy-overview)
2. [Test Data Baseline](#2-test-data-baseline)
3. [Test Resources](#3-test-resources)
4. [Story-by-Story Test Specifications](#4-story-by-story-test-specifications)
5. [E2E Verification (MCP Interactive)](#5-e2e-verification-mcp-interactive)
6. [Test Data Management](#6-test-data-management)
7. [Success Criteria](#7-success-criteria)

---

## 1. Test Strategy Overview

### Phase 2 Focus Areas

Phase 2 introduces the conversational AI layer with these critical components:

| Component | Criticality | Testing Focus |
|-----------|-------------|---------------|
| Claude Wrapper Module | **CRITICAL** | Unit tests, integration tests, error handling |
| Chat API Endpoint | High | Request/response validation, conversation state |
| Context Preparation | High | File management, prompt construction |
| Three-Panel UI | High | Layout, state management, interaction flow |
| Document Generation | Medium | Creation, storage, download |
| Results Accumulation | Medium | State persistence, click handling |

### Test Pyramid

```
                    ┌─────────────────┐
                    │   MCP E2E       │  ← Interactive browser verification (PRIMARY GATE)
                    │   (Manual, Few) │
                   ─┼─────────────────┼─
                  / │ Integration     │ \  ← API + Claude + Services (15-20 tests)
                 /  │ Tests           │  \
               ─────┼─────────────────┼─────
              /     │ Unit Tests      │     \  ← Pure logic tests (40+ tests)
             /      │ (Fast, Many)    │      \
            ────────┴─────────────────┴────────
```

### Testing Frameworks

| Layer | Backend | Frontend |
|-------|---------|----------|
| Unit | pytest | vitest |
| Integration | pytest + TestClient | vitest + MSW |
| **E2E (primary)** | - | **Playwright MCP (interactive verification)** |
| E2E (future automation) | pytest (API only) | Playwright scripted tests |
| LLM Verification | Claude CLI subprocess | - |

### E2E Verification Strategy

**Playwright MCP is the primary E2E gate.** Interactive browser verification against the live running system catches issues that automated DOM assertions miss — layout problems, video playback, real Claude responses, actual search results.

Automated Playwright test scripts (`e2e/phase2.spec.ts`) may be added later for regression automation once functionality is verified and stable.

### Claude Wrapper Testing Strategy

The Claude Wrapper Module (`services/claude.py`) is the most critical component. Testing approach:

1. **Unit Tests**: Test command construction, response parsing, error handling (with mocked subprocess)
2. **Integration Tests**: Test actual CLI invocation with controlled prompts
3. **E2E Verification**: Interactive MCP verification of full conversation flow through the web UI

---

## 2. Test Data Baseline

### Purpose

E2E verification requires a **known, reproducible dataset**. Ad-hoc uploaded videos, leftover data from development, or integration tests that wipe OpenSearch will produce unreliable results. Before running any E2E verification, the system must be reset to a defined baseline.

### Test Video

| Property | Value |
|----------|-------|
| **Filename** | `test_meeting_full.mkv` |
| **Location** | `/data/test/videos/test_meeting_full.mkv` |
| **Ground Truth** | `/data/test/expected/test_meeting_full_ground_truth.json` |
| **Content** | Backdrop CMS Weekly Meeting, January 5, 2023 |
| **Duration** | 803 seconds (13m 23s) |
| **Words** | ~2216 |
| **Speakers** | 7 (Jen Lampton, Martin, Robert, Justin, Greg, Luke McCormick, Tim Erickson) |
| **Expected Segments** | 5-10 (semantic chunking produces ~7 at default settings) |
| **Topics** | Team intros, community contributions, Backdrop 1.24 features (permissions filter, role descriptions, back-to-site button, search index rebuild, database log config), htaccess/PHP 8 changes, UI updater notifications |

This video was chosen because:
- At 2216 words, semantic chunking produces multiple segments with meaningful timestamp boundaries
- Rich topic diversity enables testing search across different timestamps
- Multiple speakers (though diarization is a Phase 3 concern)
- Real technical meeting content matches the system's intended use case

### Data Reset Procedure

Run this before E2E verification to establish a clean baseline. Services stay running; only data is cleared.

**Step 1: Clear existing data**

```bash
# Clear PostgreSQL (cascade deletes segments, transcripts)
docker compose exec -T postgres psql -U whedifaqaui -d whedifaqaui -c "
  TRUNCATE videos CASCADE;
"

# Delete OpenSearch index and recreate
docker compose exec -T backend python -c "
from app.services.opensearch_client import get_opensearch_client
from app.services.indexing import SEGMENTS_INDEX
client = get_opensearch_client()
client.indices.delete(index=SEGMENTS_INDEX, ignore=[404])
"

# Clear video and transcript files
docker compose exec -T backend sh -c "rm -rf /data/videos/original/* /data/videos/processed/* /data/transcripts/*"

# Clear Celery task queue
docker compose exec -T redis redis-cli FLUSHALL
```

**Step 2: Upload test video and wait for processing**

```bash
# Upload via API
curl -X POST http://localhost:8000/api/videos \
  -F "file=@data/test/videos/test_meeting_full.mkv" \
  -F "title=Backdrop CMS Weekly Meeting" \
  -F "recording_date=2023-01-05"

# Poll until status=ready (processing takes several minutes on CPU)
VIDEO_ID=$(curl -s http://localhost:8000/api/videos | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")
while [ "$(curl -s http://localhost:8000/api/videos/$VIDEO_ID | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')" != "ready" ]; do
  echo "Processing..."
  sleep 10
done
echo "Video ready: $VIDEO_ID"
```

**Step 3: Verify baseline**

```bash
# Confirm segment count in OpenSearch
curl -s "http://localhost:9200/segments_index/_count" | python3 -c "import sys,json; c=json.load(sys.stdin)['count']; print(f'Segments indexed: {c}'); assert c >= 5, f'Expected >=5 segments, got {c}'"

# Confirm video status
curl -s http://localhost:8000/api/videos/$VIDEO_ID | python3 -c "import sys,json; v=json.load(sys.stdin); print(f'Status: {v[\"status\"]}, Duration: {v[\"duration\"]}s')"
```

### Expected Baseline State

After setup, the system should contain:
- **1 video** ("Backdrop CMS Weekly Meeting", status=ready, 803s)
- **5-10 segments** in PostgreSQL (from semantic chunking)
- **5-10 documents** in OpenSearch `segments_index` (all segments indexed)
- **1 transcript** JSON file in `/data/transcripts/`
- **1 processed** MP4 in `/data/videos/processed/`

### Search Verification Queries

These queries validate that the baseline is correctly indexed:

| Query | Expected | Timestamp Range |
|-------|----------|----------------|
| "permission filter" | Match | 3:00 - 6:40 |
| "back to site" | Match | 7:55 - 10:37 |
| "search index rebuild" | Match | 7:55 - 10:37 |
| "htaccess PHP" | Match | 10:38 - 13:22 |
| "quantum computing" | No match | - |

---

## 3. Test Resources

### 3.1 Test Conversation Scenarios

Pre-defined conversation scenarios for testing multi-turn interactions:

**Location**: `/data/test/conversations/`

#### Scenario: Backdrop CMS Weekly Meeting

```json
// /data/test/conversations/backdrop_meeting.json
{
  "scenario_id": "backdrop_meeting",
  "description": "Multi-turn conversation about Backdrop CMS weekly meeting (Jan 5, 2023)",
  "test_video": "test_meeting_full.mkv (Backdrop CMS Weekly Meeting, 803s, 7 indexed segments)",
  "turns": [
    {
      "turn": 1,
      "user_message": "What new features were added to Backdrop 1.24?",
      "expected_topics": ["permission filter", "role descriptions", "back-to-site", "search index rebuild", "database log"],
      "expected_citations_min": 1
    },
    {
      "turn": 2,
      "user_message": "Who contributed the back-to-site button?",
      "requires_context": true,
      "expected_topics": ["Justin", "first core contribution"],
      "expected_citations_min": 1
    },
    {
      "turn": 3,
      "user_message": "What other issues did they discuss after the feature review?",
      "requires_context": true,
      "expected_topics": ["htaccess", "PHP 8", "UI updater", "notification"],
      "expected_citations_min": 1
    }
  ]
}
```

#### Scenario: Document Generation

```json
// /data/test/conversations/document_generation.json
{
  "scenario_id": "document_generation",
  "description": "Generate summary document from conversation",
  "preconditions": ["video_processed"],
  "turns": [
    {
      "turn": 1,
      "user_message": "What was discussed in the Backdrop CMS weekly meeting?",
      "expected_citations_min": 2
    },
    {
      "turn": 2,
      "action": "generate_document",
      "request": "Summarize the Backdrop 1.24 features discussion",
      "expected_document": {
        "format": "markdown",
        "min_length": 200,
        "has_citations": true
      }
    }
  ]
}
```

### 3.2 Mock Claude Responses

For unit and integration testing without actual Claude CLI calls:

**Location**: `/data/test/mock_responses/`

```json
// /data/test/mock_responses/chat_responses.json
{
  "simple_answer": {
    "input_pattern": "What.*features.*Backdrop 1.24.*",
    "response": "Backdrop 1.24 introduced several new features: an instant search filter on the permissions page (modeled after the modules page search), descriptions for user roles with separate admin and assignment contexts, a back-to-site button in the administration bar, a rebuild search index process, and a configuration option for database log message length. [Backdrop CMS Weekly Meeting @ 5:48] [Backdrop CMS Weekly Meeting @ 7:55]",
    "expected_citations": [
      {
        "video_title": "Backdrop CMS Weekly Meeting",
        "timestamp": "5:48"
      },
      {
        "video_title": "Backdrop CMS Weekly Meeting",
        "timestamp": "7:55"
      }
    ]
  },
  "follow_up_answer": {
    "input_pattern": "Who contributed.*back-to-site.*",
    "requires_context": true,
    "response": "The back-to-site button was Justin's first core contribution to Backdrop. Jen Lampton mentioned this during the feature review, and the team congratulated him on the contribution. [Backdrop CMS Weekly Meeting @ 7:55]",
    "expected_citations": [
      {
        "video_title": "Backdrop CMS Weekly Meeting",
        "timestamp": "7:55"
      }
    ]
  },
  "no_results": {
    "input_pattern": ".*nonexistent.*",
    "response": "I couldn't find any relevant information about this topic in the video archive."
  }
}
```

### 3.3 Test Context Files

Sample context files for testing prompt construction:

```json
// /data/test/context/sample_context.json
{
  "query": "What new features were added to Backdrop 1.24?",
  "segments": [
    {
      "video_id": "8399a812-aff7-404c-8fb2-17f2e0cfd722",
      "video_title": "Backdrop CMS Weekly Meeting",
      "timestamp": 348.6,
      "text": "We don't have a bunch of contrib modules that do anything with files because most of our media stuff is already in core. But I do think we should have a change record up in case anyone is using it in a custom module. And let's see, we added descriptions for roles...",
      "speaker": "SPEAKER_00",
      "recording_date": "2023-01-05"
    },
    {
      "video_id": "8399a812-aff7-404c-8fb2-17f2e0cfd722",
      "video_title": "Backdrop CMS Weekly Meeting",
      "timestamp": 475.5,
      "text": "Now you can customize how long you want that length to be... added a back to site button in the administration bar. So when you are on the front end page of your site and you go to edit something and you get thrown deep in the bowels of backdrop...",
      "speaker": "SPEAKER_00",
      "recording_date": "2023-01-05"
    }
  ]
}
```

### 3.4 LLM-Based Conversation Quality Verification

For verifying that AI responses are appropriate and well-cited:

```python
# backend/tests/utils/conversation_verification.py

CONVERSATION_VERIFICATION_PROMPT = """
You are evaluating the quality of an AI assistant's response in a video knowledge base system.

USER QUESTION:
{user_question}

PROVIDED CONTEXT:
{context}

AI RESPONSE:
{ai_response}

## Evaluation Criteria

### 1. Relevance (Weight: 30%)
- Does the response directly address the user's question?
- Is the information from the context used appropriately?
- Score 0-100

### 2. Citation Quality (Weight: 30%)
- Are citations provided in [Video Title @ MM:SS] format?
- Do citations correspond to actual context segments?
- Are claims properly attributed?
- Score 0-100

### 3. Accuracy (Weight: 25%)
- Is the information in the response accurate based on context?
- Are there any hallucinations or invented details?
- Score 0-100

### 4. Completeness (Weight: 15%)
- Does the response cover the key points from relevant context?
- Is important information omitted?
- Score 0-100

## Output Format (EXACT FORMAT REQUIRED)

RESPONSE_QUALITY|{overall_pass}|{weighted_score}
RELEVANCE|{PASS/FAIL}|{score}|{brief_explanation}
CITATION_QUALITY|{PASS/FAIL}|{score}|{brief_explanation}
ACCURACY|{PASS/FAIL}|{score}|{brief_explanation}
COMPLETENESS|{PASS/FAIL}|{score}|{brief_explanation}
SUMMARY|{one_sentence_summary}
"""
```

---

## 4. Story-by-Story Test Specifications

### S7: Conversational Search

#### Acceptance Criteria
- Chat-style conversation history
- AI remembers context within session
- Can reference previous results ("the second video")

#### Unit Tests (Backend) - Claude Wrapper Module

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S7-U01 | `test_claude_command_construction_new` | Build command for new conversation | `claude --session-id <uuid> -p "..."` |
| S7-U02 | `test_claude_command_construction_resume` | Build command for resumed conversation | `claude --resume <uuid> -p "..."` |
| S7-U03 | `test_claude_response_parsing` | Parse stdout to ClaudeResponse | result and conversation_id extracted |
| S7-U04 | `test_claude_error_handling` | Handle non-zero exit code | ClaudeError raised with message |
| S7-U05 | `test_claude_timeout_handling` | Handle subprocess timeout | TimeoutExpired raised |
| S7-U06 | `test_conversation_id_generation` | New UUID generated when none provided | Valid UUID v4 format |
| S7-U07 | `test_conversation_id_preserved` | Existing ID used when provided | Same ID in response |

#### Unit Tests (Backend) - Chat Service

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S7-U08 | `test_context_file_creation` | Write context to temp file | JSON file created at expected path |
| S7-U09 | `test_context_file_cleanup` | Temp file deleted after use | File does not exist after cleanup |
| S7-U10 | `test_prompt_construction` | Build prompt with context file ref | Prompt includes file path |
| S7-U11 | `test_citation_extraction` | Extract [Video @ MM:SS] citations | List of citation objects |
| S7-U12 | `test_citation_extraction_no_citations` | Handle response without citations | Empty citations list |

#### Integration Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S7-I01 | `test_chat_endpoint_new_conversation` | POST /api/chat without conversation_id | Returns message + new conversation_id |
| S7-I02 | `test_chat_endpoint_resume_conversation` | POST /api/chat with conversation_id | Returns message + same conversation_id |
| S7-I03 | `test_chat_searches_opensearch` | Chat triggers hybrid search | OpenSearch queried with message |
| S7-I04 | `test_chat_context_preparation` | Context written for Claude | Temp file contains segments |
| S7-I05 | `test_chat_response_includes_citations` | Response has citation objects | citations array populated |
| S7-I06 | `test_chat_empty_search_results` | Handle no matching segments | Graceful "no information" response |
| S7-I07 | `test_chat_claude_error` | Handle Claude CLI failure | 500 error with message |

#### Frontend Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S7-F01 | `test_chat_input_renders` | ChatInput component renders | Input field and send button visible |
| S7-F02 | `test_chat_message_submit` | Message submitted on enter/click | onSend callback called |
| S7-F03 | `test_chat_history_displays` | ChatHistory shows messages | User and AI messages rendered |
| S7-F04 | `test_chat_loading_state` | Loading indicator during request | Spinner/typing indicator shown |
| S7-F05 | `test_conversation_id_stored` | ID stored in hook state | useChat returns conversationId |
| S7-F06 | `test_citation_click_handler` | Citation component is clickable | onClick callback triggered |
| S7-F07 | `test_message_with_citations` | AI message renders with citations | Citation links visible in message |

#### E2E Tests (Conversation Quality - LLM Verified)

| Test ID | Test Name | Description | LLM Verification Criteria |
|---------|-----------|-------------|---------------------------|
| S7-E01 | `test_response_relevance` | AI answers the question asked | Relevance ≥85% |
| S7-E02 | `test_citation_quality` | Citations are properly formatted | Citation Quality ≥80% |
| S7-E03 | `test_conversation_context` | Follow-up uses previous context | "it" references resolve correctly |
| S7-E04 | `test_multi_turn_coherence` | 3-turn conversation stays coherent | All turns score ≥75% |

---

### S8: Results List

#### Acceptance Criteria
- Results list persists during session
- Each result is clickable
- Results can be video timestamps or generated documents

#### Unit Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S8-U01 | `test_citation_to_result_object` | Convert citation to result | Contains video_id, title, timestamp |
| S8-U02 | `test_result_deduplication` | Same segment not added twice | Unique results only |

#### Frontend Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S8-F01 | `test_results_panel_renders` | ResultsPanel component renders | Panel visible with heading |
| S8-F02 | `test_results_list_scrollable` | Results overflow scrolls | Scrollbar appears when needed |
| S8-F03 | `test_result_item_clickable` | ResultItem has click handler | onClick callback triggered |
| S8-F04 | `test_result_shows_video_info` | Video result shows title/timestamp | "Backdrop CMS Weekly Meeting @ 5:48" displayed |
| S8-F05 | `test_result_shows_document_info` | Document result shows title/date | "Summary.md" with icon displayed |
| S8-F06 | `test_results_accumulate` | New results added to list | Count increases after chat |
| S8-F07 | `test_results_persist_during_session` | Results survive navigation | Same results after tab switch |
| S8-F08 | `test_selected_result_highlighted` | Selected item has active style | CSS class 'selected' applied |

#### Integration Tests (Frontend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S8-I01 | `test_chat_adds_citations_to_results` | Chat response populates results | Results count increases |
| S8-I02 | `test_result_click_updates_content_pane` | Click result loads content | ContentPane shows video/doc |

---

### S9: Content Pane

#### Acceptance Criteria
- Content pane shows video player or document
- Video jumps to specified timestamp
- Documents have download option

#### Unit Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S9-U01 | `test_segment_context_fetch` | Fetch surrounding segments | Returns before/after segments |

#### Frontend Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S9-F01 | `test_content_pane_renders` | ContentPane component renders | Container visible |
| S9-F02 | `test_content_pane_empty_state` | Shows placeholder when empty | "Select a result" message |
| S9-F03 | `test_content_pane_video_mode` | Shows video player for video result | VideoPlayer component rendered |
| S9-F04 | `test_content_pane_document_mode` | Shows document viewer for doc result | DocumentViewer component rendered |
| S9-F05 | `test_video_seeks_to_timestamp` | Video jumps to specified time | player.currentTime matches |
| S9-F06 | `test_transcript_syncs_with_video` | Transcript panel shows and syncs | Current segment highlighted |
| S9-F07 | `test_document_download_button` | Download button visible for docs | Button triggers download |

#### Integration Tests (Frontend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S9-I01 | `test_result_click_loads_video` | Click video result shows player | Video source loaded |
| S9-I02 | `test_result_click_seeks_correctly` | Click seeks to exact timestamp | Within ±1 second of target |
| S9-I03 | `test_document_click_loads_content` | Click document shows viewer | Document text rendered |

---

### S2: AI-Generated Summaries

#### Acceptance Criteria
- Summary answers based on relevant content
- Cites sources with video + timestamp
- Synthesizes across multiple videos when relevant

#### Unit Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S2-U01 | `test_multi_video_context_building` | Context includes multiple videos | Segments from ≥2 videos |
| S2-U02 | `test_context_truncation` | Long context truncated | Under max token limit |
| S2-U03 | `test_source_formatting` | Sources formatted correctly | "Video: X, Timestamp: MM:SS" |

#### Integration Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S2-I01 | `test_summary_cites_multiple_sources` | Response cites different videos | ≥2 unique video_ids in citations |
| S2-I02 | `test_summary_synthesizes_content` | Answer combines information | Coherent synthesis verified |

#### E2E Tests (LLM Verified)

| Test ID | Test Name | Description | LLM Verification Criteria |
|---------|-----------|-------------|---------------------------|
| S2-E01 | `test_summary_accuracy` | Summary accurately reflects sources | Accuracy ≥85% |
| S2-E02 | `test_cross_video_synthesis` | Synthesizes from multiple meetings | References ≥2 videos correctly |

---

### S10: Summary Document Generation

#### Acceptance Criteria
- "Summarize the second video" generates document
- Document added to results list
- Viewable and downloadable

#### Unit Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S10-U01 | `test_document_schema_validation` | Validate GeneratedDocument schema | Valid data passes |
| S10-U02 | `test_document_id_generation` | UUID generated for document | Valid UUID format |
| S10-U03 | `test_document_content_markdown` | Content is valid markdown | Parses without error |
| S10-U04 | `test_document_source_tracking` | Source video/segment IDs stored | Arrays populated |

#### Integration Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S10-I01 | `test_create_document_endpoint` | POST /api/documents creates document | Returns document_id and preview |
| S10-I02 | `test_get_document_endpoint` | GET /api/documents/{id} returns content | Full markdown content |
| S10-I03 | `test_download_document_endpoint` | GET /api/documents/{id}/download | Returns file attachment |
| S10-I04 | `test_document_stored_in_database` | Document persisted | Row exists in generated_documents |
| S10-I05 | `test_document_generation_uses_claude` | Claude called for generation | Claude wrapper invoked |
| S10-I06 | `test_document_has_citations` | Generated doc has timestamp citations | [MM:SS] format found |

#### Frontend Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S10-F01 | `test_document_card_renders` | DocumentCard component renders | Card visible with title |
| S10-F02 | `test_document_card_shows_preview` | Preview text displayed | First ~100 chars shown |
| S10-F03 | `test_document_viewer_renders` | DocumentViewer shows markdown | Markdown rendered as HTML |
| S10-F04 | `test_download_button_triggers_fetch` | Download calls API | fetch called with correct URL |
| S10-F05 | `test_document_added_to_results` | New doc appears in results list | Results count increases |

#### E2E Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S10-E01 | `test_generate_summary_command` | "Summarize the meeting" creates doc | Document in results |
| S10-E02 | `test_document_viewable` | Document can be viewed in pane | Content renders correctly |
| S10-E03 | `test_document_downloadable` | Download produces file | File downloads successfully |

---

### V4: Recording Date Association

#### Acceptance Criteria
- Date field (required) on upload
- System uses date for temporal relevance

#### Unit Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| V4-U01 | `test_recording_date_required` | Video creation requires date | Validation error if missing |
| V4-U02 | `test_recording_date_format` | Date parsed correctly | ISO date format accepted |
| V4-U03 | `test_date_stored_in_model` | Video model has recording_date | Field accessible |

#### Integration Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| V4-I01 | `test_date_in_search_context` | Search results include recording_date | Date in segment response |
| V4-I02 | `test_date_in_chat_context` | Context file includes dates | recording_date field present |
| V4-I03 | `test_date_index_exists` | Database index on recording_date | Query plan uses index |

#### Frontend Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| V4-F01 | `test_date_field_required_in_upload` | Upload form requires date | Validation shown if empty |
| V4-F02 | `test_date_displayed_in_results` | Result shows recording date | Date visible in result item |

---

## 5. E2E Verification (MCP Interactive)

### Approach

E2E verification uses **Playwright MCP** (interactive browser control) as the **primary acceptance gate**. The verifier navigates the live system, interacts with UI elements, takes accessibility snapshots, and visually confirms behavior.

**Precondition for all E2E scenarios**: Data baseline established per [Section 2](#2-test-data-baseline).

**Test Video**: `test_meeting_full.mkv` (Backdrop CMS Weekly Meeting, 803s, 7 indexed segments)

### MCP Verification Method

For each scenario, the verifier uses these Playwright MCP tools:
- `browser_navigate` — Navigate to URLs
- `browser_snapshot` — Capture accessibility tree (preferred over screenshots for assertions)
- `browser_click` — Click elements by reference
- `browser_type` — Type into inputs
- `browser_evaluate` — Check DOM state (e.g., video currentTime)

Each verification step records: **PASS** (expected state confirmed) or **FAIL** (with details of what was observed).

---

### E2E-P2-01: Complete Conversational Search Flow

**Steps**:
1. Navigate to `/workspace`
2. Take snapshot — verify three-panel layout visible (`workspace-layout`, `conversation-panel`, `results-panel`, `content-pane`)
3. Type in chat input: "What new features were added to Backdrop 1.24?"
4. Click Send button
5. Wait for AI response — take snapshot, verify `ai-message` element appears
6. Verify response text mentions at least 2 of: permissions filter, role descriptions, back-to-site, search index rebuild
7. Verify citations appear in results panel (`result-item-video` elements)
8. Type follow-up: "Who contributed the back-to-site button?"
9. Click Send
10. Wait for second AI response — verify it references "Justin"
11. Verify results panel now has more citations than after step 7 (accumulated, not replaced)

**Pass Criteria**:
- [ ] Three-panel layout renders
- [ ] AI response is relevant to Backdrop 1.24 features
- [ ] Citations link to video timestamps
- [ ] Follow-up correctly uses conversation context
- [ ] Results accumulate across turns

---

### E2E-P2-02: Citation Click Navigation

**Preconditions**: Conversation with citations exists from E2E-P2-01

**Steps**:
1. Click first citation in results panel
2. Take snapshot — verify content pane shows video player
3. Evaluate `document.querySelector('video').currentTime` — verify it's within the expected timestamp range for the cited segment (not 0:00)
4. Take snapshot — verify transcript panel is visible and a segment is highlighted
5. Click a different citation (different timestamp)
6. Evaluate video currentTime again — verify it changed to match the new citation

**Pass Criteria**:
- [ ] Clicking citation loads video in content pane
- [ ] Video seeks to correct timestamp (not 0:00, within ±5s of cited segment)
- [ ] Transcript syncs with video position
- [ ] Different citations seek to different timestamps

---

### E2E-P2-03: Document Generation Flow

**Steps**:
1. Navigate to `/workspace`
2. Type: "What was discussed in the Backdrop CMS weekly meeting?"
3. Click Send, wait for response
4. Type: "Summarize the Backdrop 1.24 features discussion"
5. Click Send
6. Wait for document to appear in results panel (look for `result-item-document`)
7. Click on the document result
8. Take snapshot — verify document viewer renders in content pane with formatted markdown
9. Verify download button is visible

**Pass Criteria**:
- [ ] AI generates a document from the conversation
- [ ] Document appears in results list (distinct from video citations)
- [ ] Document viewable in content pane with proper formatting
- [ ] Download button present

---

### E2E-P2-04: Multi-Turn Conversation Coherence

**Purpose**: Verify AI maintains context across 3 turns with implicit references

**Steps**:
1. Navigate to `/workspace`
2. Turn 1: Type "What new features were added to Backdrop 1.24?", Send, wait for response
3. Verify response mentions Backdrop 1.24 features
4. Turn 2: Type "Who contributed the back-to-site button?", Send, wait for response
5. Verify response identifies Justin
6. Turn 3: Type "What other issues did they discuss after the feature review?", Send, wait for response
7. Verify response references htaccess changes, PHP 8, or UI updater notifications

**Pass Criteria**:
- [ ] Turn 1: Relevant feature list
- [ ] Turn 2: Correctly resolves context — identifies Justin
- [ ] Turn 3: Correctly resolves "they" and "after" — references post-feature discussion topics
- [ ] Conversation thread stays coherent

---

### E2E-P2-05: Results Persistence During Session

**Steps**:
1. From a conversation with 3+ accumulated results, note the count
2. Navigate to Library page (`/`)
3. Navigate back to Workspace (`/workspace`)
4. Take snapshot — verify conversation history is still displayed
5. Verify results list still has the same count
6. Ask a new question, wait for response
7. Verify new results are **added** to existing list (count increased)

**Pass Criteria**:
- [ ] Conversation survives navigation away and back
- [ ] Results persist during session
- [ ] New results accumulate (not replace)

---

### E2E-P2-06: Error Handling - Claude Timeout

**Steps**:
1. Navigate to `/workspace`
2. Submit a query (if Claude is unavailable or slow, observe timeout behavior)
3. Verify an error message is displayed to the user (not a blank screen or unhandled exception)
4. Verify the chat input remains usable
5. Submit another query
6. Verify the system recovers (either succeeds or shows another clean error)

**Pass Criteria**:
- [ ] Timeout/error handled gracefully with user-friendly message
- [ ] System remains usable after error (no reload needed)

---

### E2E-P2-07: Empty Search Results Handling

**Steps**:
1. Navigate to `/workspace`
2. Type: "What did we discuss about quantum computing?"
3. Click Send, wait for response
4. Verify AI responds with a "no relevant information" type message
5. Verify no citations were added to the results panel
6. Verify no false references to unrelated video content

**Pass Criteria**:
- [ ] AI acknowledges lack of relevant information
- [ ] No citations generated for irrelevant topic
- [ ] Results panel unchanged

---

### MCP Snapshot Verification Checklist

These snapshots confirm visual/structural correctness during E2E scenarios:

| ID | When | What to Verify |
|----|------|----------------|
| SCR-W01 | E2E-P2-01 step 2 | Three-panel workspace layout |
| SCR-W02 | E2E-P2-01 step 2 | Conversation panel with chat input |
| SCR-W03 | E2E-P2-01 step 7 | Results panel with citations |
| SCR-W04 | E2E-P2-01 step 2 | Content pane empty state |
| SCR-W05 | E2E-P2-02 step 2 | Content pane with video player |
| SCR-W06 | E2E-P2-03 step 8 | Content pane with document viewer |
| SCR-C01 | E2E-P2-01 step 2 | Chat input field and send button |
| SCR-C02 | E2E-P2-01 step 5 | AI response with citations in message |
| SCR-C03 | E2E-P2-04 step 6 | Multi-turn conversation history |
| SCR-R01 | E2E-P2-07 step 5 | Results panel unchanged (empty or prior state) |
| SCR-R02 | E2E-P2-01 step 7 | Results panel with video citations |
| SCR-R03 | E2E-P2-03 step 7 | Results panel with document entry |
| SCR-D01 | E2E-P2-03 step 8 | Document rendered in viewer |

---

## 6. Test Data Management

### Data Reset

See [Section 2: Test Data Baseline](#2-test-data-baseline) for the complete data reset procedure. This must be run before E2E verification.

### Claude Mock for Unit Tests

```python
# backend/tests/fixtures/mock_claude.py

from unittest.mock import MagicMock, patch
from dataclasses import dataclass


@dataclass
class MockClaudeResponse:
    result: str
    conversation_id: str


class MockClaudeService:
    """Mock Claude service for unit tests."""

    def __init__(self, responses: dict = None):
        self.responses = responses or {}
        self.calls = []

    def query(self, message: str, conversation_id: str = None, **kwargs) -> MockClaudeResponse:
        self.calls.append({
            "message": message,
            "conversation_id": conversation_id,
            **kwargs
        })

        # Find matching response
        for pattern, response_data in self.responses.items():
            if pattern.lower() in message.lower():
                return MockClaudeResponse(
                    result=response_data["response"],
                    conversation_id=conversation_id or "mock-conv-id"
                )

        # Default response
        return MockClaudeResponse(
            result="I don't have information about that topic.",
            conversation_id=conversation_id or "mock-conv-id"
        )


@pytest.fixture
def mock_claude():
    """Pytest fixture for mocked Claude service."""
    mock_service = MockClaudeService({
        "features": {
            "response": "Backdrop 1.24 introduced several features including a permissions page search filter, role descriptions, a back-to-site button, and a rebuild search index process [Backdrop CMS Weekly Meeting @ 5:48]."
        },
        "back-to-site": {
            "response": "The back-to-site button was Justin's first core contribution to Backdrop [Backdrop CMS Weekly Meeting @ 7:55]."
        }
    })

    with patch('app.services.claude.claude', mock_service):
        yield mock_service
```

### Temp File Cleanup

```python
# backend/tests/conftest.py

import pytest
from pathlib import Path
import shutil


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Clean up temp files before and after each test."""
    temp_dir = Path("/data/temp")
    test_temp_dir = temp_dir / "test"

    # Create test temp directory
    test_temp_dir.mkdir(parents=True, exist_ok=True)

    yield

    # Cleanup after test
    shutil.rmtree(test_temp_dir, ignore_errors=True)
```

### OpenSearch Test Isolation

**Known Issue**: Integration tests in `backend/tests/integration/test_search_api.py` use the production `segments_index` and wipe all documents with `delete_by_query(match_all)`. This destroys any manually uploaded test data.

**Requirement**: Integration tests MUST use a separate test index (e.g., `segments_index_test`) or run the data reset procedure after completion. See the Phase 1 investigation notes for full root cause analysis.

---

## 7. Success Criteria

### Phase 2 Completion Checklist

#### Backend Tests (Claude Wrapper & Services)

- [ ] All S7-U* tests passing (12 tests)
- [ ] All S7-I* tests passing (7 tests)
- [ ] All S8-U* tests passing (2 tests)
- [ ] All S9-U* tests passing (1 test)
- [ ] All S2-U* tests passing (3 tests)
- [ ] All S2-I* tests passing (2 tests)
- [ ] All S10-U* tests passing (4 tests)
- [ ] All S10-I* tests passing (6 tests)
- [ ] All V4-U* tests passing (3 tests)
- [ ] All V4-I* tests passing (3 tests)

**Total backend tests**: ~43 tests

#### Frontend Tests

- [ ] All S7-F* tests passing (7 tests)
- [ ] All S8-F* tests passing (8 tests)
- [ ] All S8-I* tests passing (2 tests)
- [ ] All S9-F* tests passing (7 tests)
- [ ] All S9-I* tests passing (3 tests)
- [ ] All S10-F* tests passing (5 tests)
- [ ] All V4-F* tests passing (2 tests)

**Total frontend tests**: ~34 tests

#### E2E Verification (MCP Interactive — PRIMARY GATE)

- [ ] Data baseline established (Section 2 reset procedure)
- [ ] E2E-P2-01: Complete conversational search flow — all pass criteria met
- [ ] E2E-P2-02: Citation click navigation — video seeks to correct timestamps
- [ ] E2E-P2-03: Document generation flow — document created and viewable
- [ ] E2E-P2-04: Multi-turn conversation coherence — context correctly maintained
- [ ] E2E-P2-05: Results persistence during session — survives navigation
- [ ] E2E-P2-06: Error handling — graceful timeout/error recovery
- [ ] E2E-P2-07: Empty search results — no false citations

**Total E2E scenarios**: 7 (verified interactively via Playwright MCP)

#### MCP Snapshot Verification

- [ ] All SCR-W* snapshots verified (6 checks — workspace layout)
- [ ] All SCR-C* snapshots verified (3 checks — chat interface)
- [ ] All SCR-R* snapshots verified (3 checks — results panel)
- [ ] All SCR-D* snapshots verified (1 check — document viewer)

**Total snapshot checks**: 13

### Acceptance Verification Matrix

| Story | Unit Tests | Integration Tests | MCP E2E Verification | MCP Snapshots |
|-------|------------|-------------------|---------------------|---------------|
| S7 | S7-U01-12, S7-F01-07 | S7-I01-07 | E2E-P2-01, E2E-P2-04 | SCR-W01-04, SCR-C01-03 |
| S8 | S8-U01-02, S8-F01-08 | S8-I01-02 | E2E-P2-01, E2E-P2-05 | SCR-R01-03 |
| S9 | S9-U01, S9-F01-07 | S9-I01-03 | E2E-P2-02 | SCR-W05 |
| S2 | S2-U01-03 | S2-I01-02 | E2E-P2-01 | SCR-C02 |
| S10 | S10-U01-04, S10-F01-05 | S10-I01-06 | E2E-P2-03 | SCR-W06, SCR-R03, SCR-D01 |
| V4 | V4-U01-03, V4-F01-02 | V4-I01-03 | - | - |

### Critical Path Testing

The following tests verify the most critical functionality:

| Priority | Test | Failure Impact |
|----------|------|----------------|
| **P0** | Claude wrapper subprocess invocation | No AI responses |
| **P0** | Conversation ID handling (new/resume) | Broken follow-ups |
| **P0** | Context file creation/cleanup | Memory leaks, security |
| **P1** | Citation extraction and linking | No source verification |
| **P1** | Three-panel layout rendering | Broken UI |
| **P1** | Results accumulation | Lost findings |
| **P2** | Document generation | Feature unavailable |
| **P2** | Download functionality | Export broken |

---

## Appendix A: Test File Structure

```
whedifaqaui/
├── backend/
│   └── tests/
│       ├── conftest.py                    # Shared fixtures
│       ├── fixtures/
│       │   ├── phase2_seed_data.py        # Phase 2 test data
│       │   └── mock_claude.py             # Claude mock service
│       ├── unit/
│       │   ├── test_claude_wrapper.py     # S7-U01-07
│       │   ├── test_chat_service.py       # S7-U08-12
│       │   ├── test_document_service.py   # S10-U01-04
│       │   └── test_context_preparation.py # S2-U01-03
│       ├── integration/
│       │   ├── test_chat_api.py           # S7-I01-07
│       │   ├── test_document_api.py       # S10-I01-06
│       │   └── test_context_flow.py       # S2-I01-02
│       ├── e2e/
│       │   └── test_conversation_quality.py # LLM verification tests
│       └── utils/
│           └── conversation_verification.py # LLM verification utility
│
├── frontend/
│   └── src/
│       └── __tests__/
│           ├── components/
│           │   ├── workspace/
│           │   │   ├── ConversationPanel.test.tsx  # S7-F*
│           │   │   ├── ResultsPanel.test.tsx       # S8-F*
│           │   │   └── ContentPane.test.tsx        # S9-F*
│           │   ├── chat/
│           │   │   ├── ChatInput.test.tsx
│           │   │   ├── ChatMessage.test.tsx
│           │   │   └── Citation.test.tsx
│           │   └── documents/
│           │       ├── DocumentCard.test.tsx       # S10-F*
│           │       └── DocumentViewer.test.tsx
│           └── hooks/
│               ├── useChat.test.ts
│               └── useWorkspace.test.ts
│
└── data/
    └── test/
        ├── videos/
        │   ├── test_meeting_full.mkv       # PRIMARY: Backdrop CMS meeting (803s, 7 speakers)
        │   ├── test_meeting_primary.mkv    # Family discussion (81s, Phase 1)
        │   ├── test_meeting_long.mkv       # Trimmed meeting intro (185s, Phase 1)
        │   ├── test_silent.mkv             # Silent video (error testing)
        │   └── test_corrupted.mkv          # Truncated file (error testing)
        ├── conversations/                  # Test conversation scenarios
        │   ├── backdrop_meeting.json       # Backdrop CMS weekly meeting scenario
        │   └── document_generation.json
        ├── mock_responses/                 # Mock Claude responses
        │   └── chat_responses.json
        ├── context/                        # Sample context files
        │   └── sample_context.json
        └── expected/
            ├── test_meeting_full_ground_truth.json  # Ground truth for full meeting
            ├── test_meeting_long_ground_truth.json  # Ground truth for trimmed meeting
            └── test_meeting_primary_ground_truth.json  # Ground truth for family discussion
```

---

## Appendix B: Commands Reference

```bash
# ============================================
# DATA BASELINE (run before E2E verification)
# ============================================

# See Section 2 for full procedure. Summary:
# 1. Clear DB, OpenSearch, files
# 2. Upload test_meeting_full.mkv via API
# 3. Wait for processing to complete
# 4. Verify segment count in OpenSearch

# ============================================
# BACKEND TESTS
# ============================================

# Run Claude wrapper unit tests
cd backend && pytest tests/unit/test_claude_wrapper.py -v

# Run chat service tests
cd backend && pytest tests/unit/test_chat_service.py -v

# Run Phase 2 integration tests
cd backend && pytest tests/integration/test_chat_api.py -v
cd backend && pytest tests/integration/test_document_api.py -v

# Run all Phase 2 backend tests
cd backend && pytest tests/ -k "phase2 or chat or document or claude" -v

# ============================================
# FRONTEND TESTS
# ============================================

# Run workspace component tests
cd frontend && npm test -- --grep "workspace"

# Run chat component tests
cd frontend && npm test -- --grep "Chat"

# Run document component tests
cd frontend && npm test -- --grep "Document"

# Run all Phase 2 frontend tests
cd frontend && npm test -- --grep "S7|S8|S9|S2|S10|V4"

# ============================================
# E2E VERIFICATION (Playwright MCP)
# ============================================

# E2E verification is performed interactively via Playwright MCP.
# See Section 5 for the verification scenarios and pass criteria.
# No scripted test runner — the verifier uses MCP tools directly.
```

---

## Appendix C: LLM Verification Implementation

```python
# backend/tests/utils/conversation_verification.py

import subprocess
from pathlib import Path

VERIFICATION_PROMPT = """
You are evaluating the quality of an AI assistant's response.

USER QUESTION:
{user_question}

PROVIDED CONTEXT (segments from video archive):
{context}

AI RESPONSE:
{ai_response}

## Evaluation Criteria

### 1. Relevance (30%)
- Does response address the question?
- Is context used appropriately?

### 2. Citation Quality (30%)
- Are citations in [Video Title @ MM:SS] format?
- Do citations match context segments?

### 3. Accuracy (25%)
- Is information accurate per context?
- Any hallucinations?

### 4. Completeness (15%)
- Are key points covered?

## Output Format

RESPONSE_QUALITY|{{overall_pass: true/false}}|{{weighted_score: 0-100}}
RELEVANCE|{{PASS/FAIL}}|{{score}}|{{explanation}}
CITATION_QUALITY|{{PASS/FAIL}}|{{score}}|{{explanation}}
ACCURACY|{{PASS/FAIL}}|{{score}}|{{explanation}}
COMPLETENESS|{{PASS/FAIL}}|{{score}}|{{explanation}}
SUMMARY|{{one_line_summary}}
"""


def verify_response_quality(
    user_question: str,
    context: str,
    ai_response: str
) -> dict:
    """
    Use LLM to verify response quality.

    Returns dict with verification results.
    """
    prompt = VERIFICATION_PROMPT.format(
        user_question=user_question,
        context=context,
        ai_response=ai_response
    )

    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        cwd="/home/ubuntu/code/whedifaqaui",
        timeout=120
    )

    if result.returncode != 0:
        raise RuntimeError(f"LLM verification failed: {result.stderr}")

    return parse_verification_output(result.stdout)


def parse_verification_output(output: str) -> dict:
    """Parse pipe-delimited verification output."""
    result = {
        'overall_pass': False,
        'weighted_score': 0,
        'relevance': {'pass': False, 'score': 0, 'details': ''},
        'citation_quality': {'pass': False, 'score': 0, 'details': ''},
        'accuracy': {'pass': False, 'score': 0, 'details': ''},
        'completeness': {'pass': False, 'score': 0, 'details': ''},
        'summary': ''
    }

    for line in output.strip().split('\n'):
        if not line or line.startswith('#'):
            continue

        parts = line.split('|')
        if len(parts) < 2:
            continue

        record_type = parts[0].strip().upper()

        if record_type == 'RESPONSE_QUALITY':
            result['overall_pass'] = parts[1].strip().lower() == 'true'
            result['weighted_score'] = int(parts[2].strip())

        elif record_type == 'RELEVANCE':
            result['relevance'] = {
                'pass': parts[1].strip() == 'PASS',
                'score': int(parts[2].strip()),
                'details': parts[3].strip() if len(parts) > 3 else ''
            }

        elif record_type == 'CITATION_QUALITY':
            result['citation_quality'] = {
                'pass': parts[1].strip() == 'PASS',
                'score': int(parts[2].strip()),
                'details': parts[3].strip() if len(parts) > 3 else ''
            }

        elif record_type == 'ACCURACY':
            result['accuracy'] = {
                'pass': parts[1].strip() == 'PASS',
                'score': int(parts[2].strip()),
                'details': parts[3].strip() if len(parts) > 3 else ''
            }

        elif record_type == 'COMPLETENESS':
            result['completeness'] = {
                'pass': parts[1].strip() == 'PASS',
                'score': int(parts[2].strip()),
                'details': parts[3].strip() if len(parts) > 3 else ''
            }

        elif record_type == 'SUMMARY':
            result['summary'] = parts[1].strip() if len(parts) > 1 else ''

    return result
```
