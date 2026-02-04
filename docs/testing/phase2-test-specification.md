# Phase 2 Test Specification

**Phase**: Conversational AI (Quick Mode)
**Goal**: Pre-fetched context, quick answers, results workspace
**Stories Covered**: S7, S8, S9, S2, S10, V4

---

## Table of Contents

1. [Test Strategy Overview](#1-test-strategy-overview)
2. [Test Resources](#2-test-resources)
3. [Story-by-Story Test Specifications](#3-story-by-story-test-specifications)
4. [End-to-End Test Scenarios](#4-end-to-end-test-scenarios)
5. [Playwright Screenshot Verification](#5-playwright-screenshot-verification)
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
                    │   E2E Tests     │  ← Playwright (5-7 critical flows)
                    │   (Slow, Few)   │
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
| E2E | pytest (API only) | Playwright |
| Screenshots | - | Playwright MCP |
| LLM Verification | Claude CLI subprocess | - |

### Claude Wrapper Testing Strategy

The Claude Wrapper Module (`services/claude.py`) is the most critical component. Testing approach:

1. **Unit Tests**: Test command construction, response parsing, error handling (with mocked subprocess)
2. **Integration Tests**: Test actual CLI invocation with controlled prompts
3. **E2E Tests**: Test full conversation flow through the web UI

---

## 2. Test Resources

### 2.1 Test Conversation Scenarios

Pre-defined conversation scenarios for testing multi-turn interactions:

**Location**: `/data/test/conversations/`

#### Scenario: Authentication Discussion

```json
// /data/test/conversations/auth_discussion.json
{
  "scenario_id": "auth_discussion",
  "description": "Multi-turn conversation about authentication system",
  "turns": [
    {
      "turn": 1,
      "user_message": "What authentication system do we use?",
      "expected_topics": ["authentication", "Cognito", "Auth0"],
      "expected_citations_min": 1
    },
    {
      "turn": 2,
      "user_message": "When did we migrate to it?",
      "requires_context": true,
      "expected_topics": ["migration", "date", "timeline"],
      "expected_citations_min": 1
    },
    {
      "turn": 3,
      "user_message": "What were the main challenges?",
      "requires_context": true,
      "expected_topics": ["challenges", "problems", "issues"],
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
      "user_message": "What was discussed in the Auth Migration Meeting?",
      "expected_citations_min": 2
    },
    {
      "turn": 2,
      "action": "generate_document",
      "request": "Summarize the authentication discussion",
      "expected_document": {
        "format": "markdown",
        "min_length": 200,
        "has_citations": true
      }
    }
  ]
}
```

### 2.2 Mock Claude Responses

For unit and integration testing without actual Claude CLI calls:

**Location**: `/data/test/mock_responses/`

```json
// /data/test/mock_responses/chat_responses.json
{
  "simple_answer": {
    "input_pattern": "What authentication.*",
    "response": "Based on the recordings, you use AWS Cognito for authentication. In the Auth Migration Meeting from March 2024, John explained that the team migrated from Auth0 to Cognito due to cost considerations [Auth Migration Meeting @ 2:05].",
    "expected_citations": [
      {
        "video_title": "Auth Migration Meeting",
        "timestamp": "2:05"
      }
    ]
  },
  "follow_up_answer": {
    "input_pattern": "When did we migrate.*",
    "requires_context": true,
    "response": "Based on our previous discussion and the recordings, the migration to Cognito was completed in Q2 2024. John mentioned the exact date as April 15th, 2024 [Auth Migration Meeting @ 5:30].",
    "expected_citations": [
      {
        "video_title": "Auth Migration Meeting",
        "timestamp": "5:30"
      }
    ]
  },
  "no_results": {
    "input_pattern": ".*nonexistent.*",
    "response": "I couldn't find any relevant information about this topic in the video archive."
  }
}
```

### 2.3 Test Context Files

Sample context files for testing prompt construction:

```json
// /data/test/context/sample_context.json
{
  "query": "What authentication system do we use?",
  "segments": [
    {
      "video_id": "vid-auth-001",
      "video_title": "Auth Migration Meeting",
      "timestamp": 125.5,
      "text": "We decided to migrate from Auth0 to Cognito because of the cost savings and better AWS integration.",
      "speaker": "SPEAKER_00",
      "recording_date": "2024-03-15"
    },
    {
      "video_id": "vid-auth-001",
      "video_title": "Auth Migration Meeting",
      "timestamp": 330.0,
      "text": "The migration process took about two weeks, and we had to handle the token refresh logic differently.",
      "speaker": "SPEAKER_01",
      "recording_date": "2024-03-15"
    }
  ]
}
```

### 2.4 LLM-Based Conversation Quality Verification

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

## 3. Story-by-Story Test Specifications

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
| S8-F04 | `test_result_shows_video_info` | Video result shows title/timestamp | "Auth Meeting @ 2:05" displayed |
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

## 4. End-to-End Test Scenarios

### E2E-P2-01: Complete Conversational Search Flow

**Preconditions**: Phase 1 complete, test video processed and indexed

**Test Video**: `test_meeting_primary.mkv` (from Phase 1)

**Steps**:
1. Navigate to Workspace page (/workspace)
2. Verify three-panel layout visible
3. Type question in chat input: "What authentication system do we use?"
4. Press Enter / click Send
5. Wait for AI response (loading indicator shown)
6. Verify response appears in conversation panel
7. Verify response contains citations
8. Verify citations added to results panel
9. Ask follow-up: "When did we migrate to it?"
10. Verify follow-up uses conversation context
11. Verify response references "it" correctly
12. Verify new citations accumulated (not replaced)

**Expected Results**:
- Three-panel layout renders correctly
- AI responds with relevant information
- Citations link to video timestamps
- Follow-up question uses conversation context
- Results accumulate across turns

**LLM Verification**:
```python
# After step 6: Verify response quality
verification = verify_response_quality(
    user_question="What authentication system do we use?",
    context=retrieved_context,
    ai_response=response.message
)
assert verification['overall_pass'] == True
assert verification['weighted_score'] >= 75
```

**Playwright Screenshots**:
- `e2e-p2-01-01-workspace-empty.png` - Empty workspace
- `e2e-p2-01-02-question-entered.png` - Question in input
- `e2e-p2-01-03-loading-state.png` - AI thinking indicator
- `e2e-p2-01-04-response-received.png` - AI response with citations
- `e2e-p2-01-05-results-panel.png` - Citations in results list
- `e2e-p2-01-06-followup-response.png` - Follow-up conversation

---

### E2E-P2-02: Citation Click Navigation

**Preconditions**: Conversation with citations exists

**Steps**:
1. From E2E-P2-01, have conversation with citations
2. Click on first citation in results panel
3. Verify content pane shows video player
4. Verify video loaded and seeked to timestamp
5. Verify transcript panel synchronized
6. Verify current segment highlighted
7. Click on second citation
8. Verify video/timestamp changes correctly

**Expected Results**:
- Clicking citation loads video in content pane
- Video seeks to correct timestamp (±1 second)
- Transcript syncs with video position
- Different citations load different content

**Playwright Screenshots**:
- `e2e-p2-02-01-citation-hover.png` - Citation highlighted
- `e2e-p2-02-02-video-loaded.png` - Video player in content pane
- `e2e-p2-02-03-transcript-synced.png` - Transcript with highlight
- `e2e-p2-02-04-second-citation.png` - Different video/timestamp

---

### E2E-P2-03: Document Generation Flow

**Preconditions**: Test video processed, conversation established

**Steps**:
1. Navigate to Workspace
2. Ask: "What was discussed in the Auth Migration Meeting?"
3. Wait for response with citations
4. Ask: "Summarize the authentication discussion"
5. Wait for document generation
6. Verify document appears in results panel (with doc icon)
7. Click on document in results
8. Verify document viewer shows in content pane
9. Verify document has proper formatting
10. Click Download button
11. Verify file downloads with correct content

**Expected Results**:
- Document generated and stored
- Document appears in results list
- Document viewable in content pane
- Document downloadable as markdown file

**Playwright Screenshots**:
- `e2e-p2-03-01-summarize-request.png` - User asks for summary
- `e2e-p2-03-02-generating-state.png` - Document being generated
- `e2e-p2-03-03-document-in-results.png` - Document in results list
- `e2e-p2-03-04-document-viewer.png` - Document in content pane
- `e2e-p2-03-05-download-triggered.png` - Download initiated

---

### E2E-P2-04: Multi-Turn Conversation Coherence

**Preconditions**: Test video processed

**Purpose**: Verify AI maintains context across multiple turns

**Steps**:
1. Navigate to Workspace
2. Turn 1: "What authentication system do we use?"
3. Wait for response
4. Turn 2: "Who discussed this?" (implicit reference to auth)
5. Wait for response
6. Turn 3: "What problems did they mention?" (implicit reference to person + topic)
7. Wait for response
8. **LLM Verify**: Each turn correctly resolves references

**LLM Verification Criteria**:
| Turn | Verification |
|------|--------------|
| 1 | Response mentions auth system |
| 2 | Response identifies speakers who discussed auth |
| 3 | Response lists problems related to auth mentioned by identified speakers |

**Expected Results**:
- Turn 2 correctly interprets "this" as authentication
- Turn 3 correctly interprets "they" as speakers from Turn 2
- Conversation maintains coherent thread

**Playwright Screenshots**:
- `e2e-p2-04-01-turn1.png` - First question/response
- `e2e-p2-04-02-turn2.png` - Second turn with context
- `e2e-p2-04-03-turn3.png` - Third turn with full context

---

### E2E-P2-05: Results Persistence During Session

**Preconditions**: Active conversation with results

**Steps**:
1. Start conversation, accumulate 3+ results
2. Navigate away from workspace (e.g., to Library)
3. Return to Workspace
4. Verify conversation history preserved
5. Verify results list preserved
6. Ask new question
7. Verify new results added to existing list

**Expected Results**:
- Conversation survives navigation
- Results persist during session
- New results accumulate (not replace)

**Playwright Screenshots**:
- `e2e-p2-05-01-results-before.png` - Results before navigation
- `e2e-p2-05-02-after-return.png` - Results after returning
- `e2e-p2-05-03-new-results-added.png` - New results accumulated

---

### E2E-P2-06: Error Handling - Claude Timeout

**Preconditions**: System running (Claude may be slow/unavailable)

**Steps**:
1. Navigate to Workspace
2. Submit query
3. Simulate Claude timeout (or wait for actual timeout)
4. Verify error message displayed
5. Verify system remains usable
6. Submit another query
7. Verify normal operation resumes

**Expected Results**:
- Timeout handled gracefully
- User-friendly error message
- System recovers without reload

**Playwright Screenshots**:
- `e2e-p2-06-01-error-displayed.png` - Timeout error message
- `e2e-p2-06-02-retry-success.png` - Successful retry

---

### E2E-P2-07: Empty Search Results Handling

**Preconditions**: Test video processed

**Steps**:
1. Navigate to Workspace
2. Ask question about non-existent topic: "What did we discuss about quantum computing?"
3. Verify AI responds appropriately
4. Verify no false citations generated
5. Verify results panel not populated with irrelevant items

**Expected Results**:
- AI acknowledges lack of relevant information
- No citations for irrelevant content
- Results list unchanged

**Playwright Screenshots**:
- `e2e-p2-07-01-no-results-response.png` - "No information found" response

---

## 5. Playwright Screenshot Verification

### Screenshot Specification Format

Each screenshot verification includes:
- **ID**: Unique identifier
- **URL**: Page URL when captured
- **Wait condition**: Element to wait for before capture
- **Viewport**: Browser size (default: 1920x1080)
- **Assertions**: Visual elements that must be present

### Three-Panel Layout Screenshots

| ID | Filename | Wait Condition | Assertions |
|----|----------|----------------|------------|
| SCR-W01 | `workspace-layout.png` | `[data-testid="workspace-layout"]` | Three panels visible |
| SCR-W02 | `conversation-panel.png` | `[data-testid="conversation-panel"]` | Chat input, message area |
| SCR-W03 | `results-panel.png` | `[data-testid="results-panel"]` | Results list container |
| SCR-W04 | `content-pane-empty.png` | `[data-testid="content-pane"]` | Empty state message |
| SCR-W05 | `content-pane-video.png` | `video[data-testid="video-player"]` | Video player visible |
| SCR-W06 | `content-pane-document.png` | `[data-testid="document-viewer"]` | Markdown content |

### Chat Interface Screenshots

| ID | Filename | Wait Condition | Assertions |
|----|----------|----------------|------------|
| SCR-C01 | `chat-input-empty.png` | `[data-testid="chat-input"]` | Input field, send button |
| SCR-C02 | `chat-input-typing.png` | `[data-testid="chat-input"]` has value | Text visible in input |
| SCR-C03 | `chat-loading.png` | `[data-testid="chat-loading"]` | Typing indicator |
| SCR-C04 | `chat-response.png` | `[data-testid="ai-message"]` | AI response with citations |
| SCR-C05 | `chat-history.png` | Multiple `.chat-message` | User and AI messages |
| SCR-C06 | `citation-in-message.png` | `[data-testid="citation-link"]` | Clickable citation |

### Results Panel Screenshots

| ID | Filename | Wait Condition | Assertions |
|----|----------|----------------|------------|
| SCR-R01 | `results-empty.png` | `[data-testid="results-empty"]` | Empty state message |
| SCR-R02 | `results-with-videos.png` | `[data-testid="result-item-video"]` | Video results visible |
| SCR-R03 | `results-with-documents.png` | `[data-testid="result-item-document"]` | Document with icon |
| SCR-R04 | `result-selected.png` | `.result-item.selected` | Highlighted selection |

### Document Screenshots

| ID | Filename | Wait Condition | Assertions |
|----|----------|----------------|------------|
| SCR-D01 | `document-generating.png` | `[data-testid="doc-generating"]` | Generation indicator |
| SCR-D02 | `document-preview.png` | `[data-testid="document-card"]` | Card with preview text |
| SCR-D03 | `document-full-view.png` | `[data-testid="document-viewer"]` | Full markdown rendered |
| SCR-D04 | `document-download.png` | `[data-testid="download-button"]` | Download button visible |

### Playwright Test Structure

```typescript
// e2e/phase2.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Phase 2 E2E Tests', () => {

  test('E2E-P2-01: Complete conversational search flow', async ({ page }) => {
    // Step 1: Navigate to workspace
    await page.goto('/workspace');
    await expect(page.getByTestId('workspace-layout')).toBeVisible();
    await page.screenshot({ path: 'screenshots/e2e-p2-01-01-workspace-empty.png' });

    // Step 2: Verify three-panel layout
    await expect(page.getByTestId('conversation-panel')).toBeVisible();
    await expect(page.getByTestId('results-panel')).toBeVisible();
    await expect(page.getByTestId('content-pane')).toBeVisible();

    // Step 3: Enter question
    const chatInput = page.getByTestId('chat-input');
    await chatInput.fill('What authentication system do we use?');
    await page.screenshot({ path: 'screenshots/e2e-p2-01-02-question-entered.png' });

    // Step 4: Submit
    await page.getByTestId('send-button').click();
    await page.screenshot({ path: 'screenshots/e2e-p2-01-03-loading-state.png' });

    // Step 5: Wait for response (with reasonable timeout for Claude)
    await expect(page.getByTestId('ai-message')).toBeVisible({ timeout: 60000 });
    await page.screenshot({ path: 'screenshots/e2e-p2-01-04-response-received.png' });

    // Step 6: Verify citations in results
    await expect(page.getByTestId('result-item-video')).toBeVisible();
    await page.screenshot({ path: 'screenshots/e2e-p2-01-05-results-panel.png' });

    // Step 7: Follow-up question
    await chatInput.fill('When did we migrate to it?');
    await page.getByTestId('send-button').click();

    // Wait for follow-up response
    const messages = page.locator('[data-testid="ai-message"]');
    await expect(messages).toHaveCount(2, { timeout: 60000 });
    await page.screenshot({ path: 'screenshots/e2e-p2-01-06-followup-response.png' });

    // Verify conversation context maintained
    const followUpResponse = await messages.nth(1).textContent();
    expect(followUpResponse?.toLowerCase()).toContain('migrat');
  });

  test('E2E-P2-02: Citation click navigation', async ({ page }) => {
    // Setup: Create conversation with citations
    await page.goto('/workspace');
    await page.getByTestId('chat-input').fill('What authentication system do we use?');
    await page.getByTestId('send-button').click();
    await expect(page.getByTestId('result-item-video')).toBeVisible({ timeout: 60000 });

    // Click citation
    const firstResult = page.getByTestId('result-item-video').first();
    await firstResult.click();
    await page.screenshot({ path: 'screenshots/e2e-p2-02-02-video-loaded.png' });

    // Verify video player loaded
    const videoPlayer = page.locator('video[data-testid="video-player"]');
    await expect(videoPlayer).toBeVisible();

    // Verify timestamp
    const expectedTimestamp = await firstResult.getAttribute('data-timestamp');
    // Note: Video currentTime verification requires waiting for seek
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/e2e-p2-02-03-transcript-synced.png' });
  });

  test('E2E-P2-03: Document generation flow', async ({ page }) => {
    await page.goto('/workspace');

    // Ask about a topic
    await page.getByTestId('chat-input').fill('What was discussed in the Auth Migration Meeting?');
    await page.getByTestId('send-button').click();
    await expect(page.getByTestId('ai-message')).toBeVisible({ timeout: 60000 });

    // Request summary
    await page.getByTestId('chat-input').fill('Summarize the authentication discussion');
    await page.getByTestId('send-button').click();
    await page.screenshot({ path: 'screenshots/e2e-p2-03-01-summarize-request.png' });

    // Wait for document generation (may take longer)
    await expect(page.getByTestId('result-item-document')).toBeVisible({ timeout: 90000 });
    await page.screenshot({ path: 'screenshots/e2e-p2-03-03-document-in-results.png' });

    // Click document to view
    await page.getByTestId('result-item-document').click();
    await expect(page.getByTestId('document-viewer')).toBeVisible();
    await page.screenshot({ path: 'screenshots/e2e-p2-03-04-document-viewer.png' });

    // Verify download button
    await expect(page.getByTestId('download-button')).toBeVisible();
  });
});
```

---

## 6. Test Data Management

### Database Seeding for Phase 2

```python
# backend/tests/fixtures/phase2_seed_data.py

# Requires Phase 1 video to be processed
PHASE2_TEST_CONVERSATIONS = [
    {
        "id": "conv-11111111-1111-1111-1111-111111111111",
        "created_at": "2024-03-15T10:00:00Z",
        "turns": 3
    }
]

PHASE2_TEST_DOCUMENTS = [
    {
        "id": "doc-22222222-2222-2222-2222-222222222222",
        "session_id": "session-test-001",
        "title": "Authentication System Summary",
        "content": "# Authentication System Summary\n\nBased on the team discussions...",
        "source_video_ids": ["vid-auth-001"],
        "created_at": "2024-03-15T10:30:00Z"
    }
]
```

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
        "authentication": {
            "response": "Based on the recordings, you use AWS Cognito for authentication [Auth Meeting @ 2:05]."
        },
        "migrate": {
            "response": "The migration happened in Q2 2024 [Auth Meeting @ 5:30]."
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

#### End-to-End Tests

- [ ] E2E-P2-01: Complete conversational search flow passing
- [ ] E2E-P2-02: Citation click navigation passing
- [ ] E2E-P2-03: Document generation flow passing
- [ ] E2E-P2-04: Multi-turn conversation coherence passing (LLM verified)
- [ ] E2E-P2-05: Results persistence during session passing
- [ ] E2E-P2-06: Error handling - Claude timeout passing
- [ ] E2E-P2-07: Empty search results handling passing

**Total E2E tests**: 7 scenarios

#### LLM Verification Tests

- [ ] S7-E01: Response relevance ≥85%
- [ ] S7-E02: Citation quality ≥80%
- [ ] S7-E03: Conversation context resolution
- [ ] S7-E04: Multi-turn coherence (all turns ≥75%)
- [ ] S2-E01: Summary accuracy ≥85%
- [ ] S2-E02: Cross-video synthesis

**Total LLM verification criteria**: 6 checks

#### Screenshot Verification

- [ ] All SCR-W* screenshots captured and verified (6 screenshots)
- [ ] All SCR-C* screenshots captured and verified (6 screenshots)
- [ ] All SCR-R* screenshots captured and verified (4 screenshots)
- [ ] All SCR-D* screenshots captured and verified (4 screenshots)

**Total screenshots**: ~20 screenshots

### Acceptance Verification Matrix

| Story | Unit Tests | Integration Tests | E2E Coverage | LLM Verification | Screenshots |
|-------|------------|-------------------|--------------|------------------|-------------|
| S7 | S7-U01-12, S7-F01-07 | S7-I01-07 | E2E-P2-01, E2E-P2-04 | S7-E01-04 | SCR-C01-06 |
| S8 | S8-U01-02, S8-F01-08 | S8-I01-02 | E2E-P2-01, E2E-P2-05 | - | SCR-R01-04 |
| S9 | S9-U01, S9-F01-07 | S9-I01-03 | E2E-P2-02 | - | SCR-W04-06 |
| S2 | S2-U01-03 | S2-I01-02 | E2E-P2-01 | S2-E01-02 | SCR-C04 |
| S10 | S10-U01-04, S10-F01-05 | S10-I01-06 | E2E-P2-03 | - | SCR-D01-04 |
| V4 | V4-U01-03, V4-F01-02 | V4-I01-03 | - | - | - |

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
├── e2e/
│   ├── playwright.config.ts
│   ├── phase2.spec.ts                      # Playwright E2E scenarios
│   └── screenshots/                        # Captured screenshots
│
└── data/
    └── test/
        ├── conversations/                  # Test conversation scenarios
        │   ├── auth_discussion.json
        │   └── document_generation.json
        ├── mock_responses/                 # Mock Claude responses
        │   └── chat_responses.json
        └── context/                        # Sample context files
            └── sample_context.json
```

---

## Appendix B: Commands Reference

```bash
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

# Run LLM verification tests (requires Claude CLI)
cd backend && pytest tests/e2e/test_conversation_quality.py -v

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
# END-TO-END TESTS (Playwright)
# ============================================

# Run Phase 2 E2E tests
cd e2e && npx playwright test phase2.spec.ts

# Run with UI for debugging
cd e2e && npx playwright test phase2.spec.ts --ui

# Run specific E2E scenario
cd e2e && npx playwright test phase2.spec.ts -g "E2E-P2-01"

# Update screenshots
cd e2e && npx playwright test phase2.spec.ts --update-snapshots

# ============================================
# FULL PHASE 2 TEST SUITE
# ============================================

# Run all tests (requires Phase 1 complete + test data)
./scripts/run-phase2-tests.sh
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
