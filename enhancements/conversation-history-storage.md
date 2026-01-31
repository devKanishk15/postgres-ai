# Enhancement: Conversation History Storage

Implemented a persistence layer for the chatbot to maintain context across multiple turns using session IDs.

## Changes

### 1. Persistence Layer
- Created `history_manager.py` to handle conversation state.
- Supports in-memory caching and JSON file storage.
- Implemented history trimming to stay within token context limits.

### 2. Agent Logic
- Updated `agent.py` to accept and track `conversation_id`.
- The agent now loads prior messages from storage before processing new queries.
- Results are automatically appended and persisted back to storage.

### 3. API Integration
- Enhanced `main.py` models (`ChatRequest`, `ChatResponse`) to include `conversation_id`.
- Users can now resume conversations by passing the same ID.

## File References
- [history_manager.py](file:///Users/kanishqk77/Desktop/postgres-ai/chatbot/history_manager.py)
- [agent.py](file:///Users/kanishqk77/Desktop/postgres-ai/chatbot/agent.py)
- [main.py](file:///Users/kanishqk77/Desktop/postgres-ai/chatbot/main.py)
