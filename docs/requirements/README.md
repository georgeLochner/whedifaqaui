# Whedifaqaui - Requirements Documentation

## Project Overview

**Whedifaqaui** is a Video Knowledge Management System that ingests video recordings, transcribes them, builds an evolving knowledge graph, and enables natural language search with AI-generated summaries.

> *Named after a little-known bird that lives in the African grass plains. This tiny flightless bird has a signature call that sounds like "whedifaqaui" which it utters as it jumps above the grass when it needs to locate its nest.*

## Problem Statement

Technical project handovers often rely on undocumented knowledge exchanged during recorded meetings. After the original team departs, finding specific information within hours of video recordings becomes nearly impossible.

Teams need a way to:
- Search video content using natural language
- Find specific timestamps where topics were discussed
- Get AI-synthesized summaries rather than just links
- Build cumulative domain understanding as new videos are added

## Target Users

| Persona | Description | Primary Goals |
|---------|-------------|---------------|
| **Content Admin** | Uploads videos, manages metadata | Maintain organized video library |
| **Knowledge Seeker** | Any team member (dev to manager) | Find answers quickly, verify in source |
| **Curator** | Reviews and improves content quality | Correct transcriptions, add annotations |

## Documentation Index

| Document | Description |
|----------|-------------|
| [User Stories](user-stories.md) | Complete catalog of user stories organized by epic |
| [Implementation Phases](implementation-phases.md) | Phased delivery plan from MVP to full feature set |
| [UI Mockups](ui-mockups.md) | Frontend layout specifications and wireframes |
| [Glossary](glossary.md) | Terms and definitions |

## Key Characteristics

- **Video Format**: MKV files, 10 minutes to 2 hours duration
- **Initial Scale**: ~20 hours of video, growing over time
- **Audio**: Multiple speakers, accented English (European, African, Indian)
- **Content Types**: Whiteboards, screen shares, slides, talking heads
- **Deployment**: Self-hosted web application (POC)

## High-Level Features

1. **Video Ingestion** - Upload, transcribe, and process video content
2. **Conversational Search** - AI-powered natural language Q&A interface
3. **Intelligent Analysis** - Entity extraction, speaker identification, visual content capture
4. **Knowledge Graph** - Evolving domain model connecting concepts across videos
5. **Content Curation** - Transcript editing, annotations, deprecation marking

## Next Steps

After requirements approval:
1. Technical & architectural analysis
2. Technology selection
3. Detailed design
4. Implementation planning
