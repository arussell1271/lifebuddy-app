# Functionality Guide



This document defines the high-level system behaviors, data relationships, and the necessary separation of duties between the 'Body' and the 'Brain'.



1\. Architectural Mandates \& Service Allocation

Asynchronous Rule: Re-state the constraint that the App must never wait for the Engine for cognitive tasks (e.g., chat response, vector generation).



App Responsibilities: User authentication, API serving, UI data provision (history, settings), initial data persistence (writes to documents, conversations, messages, user\_settings), and message queue submission.



Engine Responsibilities: Natural Language Generation (chat response), Intent Routing (future V2), Vector Embedding generation (for RAG), data retrieval (to build RAG context), and writing vector results (to document\_vectors).



2\. Data Flow: Conversation Management (Chat)

Conversation Start: App creates a new record in the conversations table (App-only write).



Message Ingestion: App writes the user's message to the messages table, referencing the conversation\_id. RLS must be active.



Asynchronous Chat Request: App sends a job to the Message Queue (MQ) containing: user\_id, conversation\_id, message\_id, advisor\_id, and system\_mode (from user\_settings).



Engine Processing: Engine retrieves job from MQ. It executes a DB query (with RLS set via SET app.current\_user\_id) to fetch the necessary system\_prompt\_template and any relevant RAG context (via vector search). Engine generates the response.



Response Persistence: Engine writes the advisor's response directly to the messages table, using the same conversation\_id and the Engine's authenticated session (RLS in effect).



3\. Data Flow: Settings \& Preferences

RLS-Secured Settings: Document that the user\_settings table is the single source for all preferences and is secured by RLS on user\_id.



Health Data Integration: The App service is responsible for managing the external API connection (e.g., Apple Health). Any fetched raw data must be immediately stored in the RLS-secured health\_metrics table or queued to the Engine for processing/summarization, adhering to the asynchronous rule.

