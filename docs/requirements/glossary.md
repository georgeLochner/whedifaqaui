# Glossary

This document defines key terms used throughout the Whedifaqaui project documentation.

## Project Terms

### Whedifaqaui
The project name, derived from a little-known bird that lives in the African grass plains. This tiny flightless bird has a signature call that sounds like "whedifaqaui" which it utters as it jumps above the grass when it needs to locate its nest. The metaphor reflects the system's purpose: helping users "jump up" to locate the information they need within a vast landscape of video content.

---

## User Personas

### Content Admin
A user responsible for uploading videos and managing the video library. Ensures content is properly titled, dated, and organized.

### Knowledge Seeker
Any team member (from developer to manager) who uses the system to find information. The primary user type, focused on asking questions and getting answers.

### Curator
A user who improves content quality by correcting transcriptions, adding annotations, and maintaining the accuracy of extracted entities.

---

## Content & Data Terms

### Transcript
The text conversion of spoken audio in a video. Generated automatically by the system and associated with timestamps for navigation.

### Timestamp
A specific point in time within a video, typically expressed as HH:MM:SS. Used for navigation and citation.

### Entity
A named thing extracted from content, such as:
- **Person**: Individual names (e.g., "John Smith")
- **Project**: Project or product names (e.g., "Project Phoenix")
- **System**: Technical systems or services (e.g., "AWS Cognito", "PostgreSQL")
- **Date**: Temporal references (e.g., "Q3 2024", "last sprint")

### Entity Normalization
The process of mapping variations of an entity name to a single canonical form. For example, "AWS Cognito", "Amazon Cognito", and "Cognito" all map to the same entity.

### Knowledge Graph
A network structure representing domain concepts and their relationships. Nodes are entities/concepts, edges are relationships. Evolves as new content is added.

### Visual Content
Non-audio information in videos, including:
- Whiteboards and diagrams
- Screen shares and code
- Slides and presentations
- UI demonstrations

### OCR (Optical Character Recognition)
Technology used to extract text from images, such as reading text from whiteboard photos or slide screenshots.

---

## Search & Discovery Terms

### Natural Language Query
A search expressed in conversational English rather than keywords or structured syntax. Example: "How does the authentication system work?" vs. "authentication system architecture"

### Fuzzy Matching
Search capability that finds results even when the query contains typos or variations. "Cognitio" still finds "Cognito".

### Temporal Query
A search that involves time or dates. Examples:
- "When was feature X added?"
- "What changed after January 2024?"
- "Show discussions from last month"

### Citation
A reference from an AI-generated answer back to the source material, including video title and timestamp.

---

## UI Terms

### Conversation Panel
The left panel of the main interface where users ask questions and receive AI responses in a chat-style format.

### Results List
The middle panel that accumulates findings during a search session. Contains clickable items (video timestamps, generated documents) that display in the content pane.

### Content Pane
The right panel that displays the selected item from the results list. Shows either a video player with transcript or a document viewer.

### Video Library
The administrative view showing all uploaded videos with their status, metadata, and management options.

---

## Processing Terms

### Transcription
The process of converting spoken audio to text. Includes speaker changes and timestamp markers.

### Speaker Diarization
The process of identifying and labeling different speakers in an audio recording. Determines "who said what."

### Content Analysis
AI-driven examination of transcribed content to extract entities, identify topics, and understand relationships between concepts.

### Processing Status
The current state of a video in the ingestion pipeline:
- **Uploading**: File transfer in progress
- **Transcribing**: Audio-to-text conversion
- **Analyzing**: Entity extraction and content understanding
- **Ready**: Fully processed and searchable
- **Error**: Processing failed

---

## Document Terms

### Generated Document
A document created by the AI in response to a user request, such as a summary of specific content. Added to the results list and downloadable.

### Summary
An AI-generated condensation of content from one or more videos, highlighting key points and decisions.

---

## Curation Terms

### Annotation
User-added notes or comments attached to specific timestamps in a video.

### Deprecation
Marking content as outdated or superseded by newer information. Deprecated content remains searchable but is visually flagged.

### Supersession
When newer content replaces or updates older content. The system can detect potential supersession relationships.

---

## Technical Terms

### MKV (Matroska Video)
The video container format used for input files. Supports multiple audio/video tracks and metadata.

### Deep Linking
URL parameters that navigate directly to a specific timestamp in a video. Enables sharing of precise moments.

### Session
A single user interaction period with the system. Results and conversation context persist within a session.

---

## Relationship Types (Knowledge Graph)

### Contains
A hierarchical relationship. "Authentication" contains "AWS Cognito".

### Related To
A general association between concepts. "User Pools" related to "Lambda Triggers".

### Supersedes
Temporal relationship indicating newer information. "New Auth Flow" supersedes "Old Auth Flow".

### Migrated From/To
Transition relationship. "AWS Cognito" migrated from "Auth0".

---

## Abbreviations

| Abbreviation | Meaning |
|--------------|---------|
| AI | Artificial Intelligence |
| API | Application Programming Interface |
| CRUD | Create, Read, Update, Delete |
| MVP | Minimum Viable Product |
| OCR | Optical Character Recognition |
| POC | Proof of Concept |
| UI | User Interface |
| UX | User Experience |
