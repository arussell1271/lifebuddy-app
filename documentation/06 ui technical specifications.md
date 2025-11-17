# UI Technical Specifications



This document details the concrete interfaces the App exposes, including API endpoints, directory structure, and specific data formats (Pydantic schemas).



1. Directory and Module Structure

   Define the location for all new Python components:

   app/data/models/: New SQLAlchemy ORM models (conversation\_model.py, message\_model.py, user\_setting\_model.py, advisor\_model.py).
   app/api/schemas/: New Pydantic schemas (conversation\_schema.py, message\_schema.py, user\_setting\_schema.py).
   app/api/routes/: New FastAPI endpoints (conversations.py, settings.py).
   engine/tasks/: The Engine-side worker definitions for processing chat requests.
   
2. API Endpoint Specification (App/Body)

   Specify the RESTful interface for the new features. All endpoints must rely on the RLS session hook dependency.

   Feature         Method                 Endpoint        Pydantic Schema (Input/Output)                  Function                                Responsibility                  Start      
   Chat            POST      /v1/conversations/           Input: {advisor\_id} / Output: ConversationOut   Initializes a new conversation record.  App                    Get
   History         GET       /v1/conversations/           Output: List\[ConversationSummaryOut]            Retrieves all conversation metadata (title, date) for the user (RLS).     App      Get
   TranscriptGET/v1/conversations/{id}/messagesOutput: List\[MessageOut]Retrieves all messages in a specific conversation (RLS).AppSend MessagePOST/v1/conversations/{id}/messagesInput: MessageCreate / Output: MessageOut (User's message)Writes message to DB, Queues task to Engine. Returns 202 Accepted.AppGet SettingsGET/v1/settings/Output: UserSettingsOutRetrieves the current user preferences (RLS).AppUpdate SettingsPATCH/v1/settings/Input: UserSettingsUpdate / Output: UserSettingsOutUpdates user preferences (RLS).App



3\. Critical Pydantic Schema Definitions

Focus on data integrity and security, ensuring user\_id is never accepted as input and not unnecessarily returned as output.



MessageCreate (Input Schema for chat):



class MessageCreate(BaseModel):

&nbsp;   content: str = Field(..., max\_length=4096)

&nbsp;   # The message should not include 'user\_id' or 'conversation\_id' in the payload;

&nbsp;   # they are derived from the authenticated session and URL path, respectively.

UserSettingsUpdate (Input Schema for preferences):

class UserSettingsUpdate(BaseModel):

&nbsp;   # Nullable fields allow for partial updates (PATCH)

&nbsp;   system\_mode: str | None = Field(None, description="e.g., 'spiritual', 'neutral'")

&nbsp;   health\_access\_enabled: bool | None = None

&nbsp;   # Use JSON for flexible storage of advisor name overrides

&nbsp;   advisor\_names: dict\[str, str] | None = Field(None, description="Key: Advisor ID, Value: Custom Name")

