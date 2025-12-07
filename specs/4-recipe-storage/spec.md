# Feature Specification: Recipe Storage

**Feature ID**: 4-recipe-storage  
**Created**: December 2, 2025  
**Status**: Draft  

## Overview

### Problem Statement

Currently, recipes are generated on-demand without any persistence. Users who discover a recipe they love have no way to save it for future reference. If they want to revisit a recipe, they must regenerate it through conversation, which may not produce identical results and wastes time.

### Solution Summary

Implement persistent storage for generated recipes with an intelligent save workflow. The agent detects when users express satisfaction with a recipe and offers to save it. Upon confirmation, a specialized process stores the recipe, generates an accompanying image, and presents a visual confirmation card. This creates a personal recipe collection users can access anytime.

### Target Users

- **Primary User**: Home cook/mixologist who regularly discovers and saves favorite recipes
- **Use Context**: Building a personal digital recipe collection for repeated use

## Functional Requirements

### FR-1: User Satisfaction Detection

The agent shall recognize when a user expresses satisfaction or approval of a generated recipe via system prompt instructions.

**Acceptance Criteria**:
- System prompt instructs agent to identify positive sentiment signals (e.g., "this looks great", "perfect!", "I love this", "exactly what I wanted")
- Agent recognizes explicit save intent (e.g., "save this", "keep this recipe", "add to my favorites")
- Detection is implemented through prompt engineering (not separate ML/NLP pipeline)

### FR-2: Save Offer Prompt

When satisfaction is detected, the agent shall offer to save the recipe for the user.

**Acceptance Criteria**:
- Agent asks user if they would like to save the recipe
- Offer is natural and non-intrusive within conversation context
- User can accept, decline, or modify the recipe before saving
- If declined, conversation continues normally without repeated prompts

### FR-3: Recipe Persistence

When the user confirms, the system shall persistently store the complete recipe.

**Acceptance Criteria**:
- Recipe is stored with all fields: name, type, ingredients, instructions, prep time, cook time, servings, source references, and notes
- Each saved recipe has a unique identifier
- Stored recipes persist across sessions
- Storage includes timestamp of when recipe was saved
- User can save multiple recipes in a session

### FR-4: Recipe Image Generation

Upon saving, the system shall generate an accompanying image for the recipe.

**Acceptance Criteria**:
- Image is generated based on the recipe name and description
- Image visually represents the finished dish or cocktail
- Image is stored alongside the recipe record
- Generation completes within a reasonable time (user feedback during wait)

### FR-5: Visual Confirmation Display

After successful save, a visual confirmation card shall appear showing the saved recipe with options for user action.

**Acceptance Criteria**:
- Card displays the generated recipe image
- Card shows recipe name and key details (type, prep time, servings)
- Card appears as a distinct UI element within the chat interface
- Card provides visual confirmation that save was successful
- If user denies/rejects the saved recipe, the recipe is deleted from storage
- If user requests changes to the displayed recipe, modifications are applied and saved
- Card can be dismissed or minimized by user

### FR-6: Recipe Retrieval

Users shall be able to access their saved recipes.

**Acceptance Criteria**:
- User can ask to see their saved recipes
- Agent can list saved recipes by name
- User can request a specific saved recipe by name or description
- Retrieved recipes display with their stored images

### FR-7: Recipe Categorization

Saved recipes shall be automatically categorized for organization.

**Acceptance Criteria**:
- Recipes are tagged by type (cocktail, food, dessert)
- Recipes can have user-defined tags/labels
- Categories are used internally by agent to organize and retrieve recipes
- Users access categorized recipes only through agent conversation (no direct browsing interface)

### FR-8: Recipe Memory Search Priority

When a user requests a recipe, the agent shall search saved recipes first before external sources.

**Acceptance Criteria**:
- System prompt instructs agent to check recipe memory before web search or YouTube
- Agent searches saved recipes by name, ingredients, and tags
- If matching saved recipes exist, agent presents them before offering to search externally
- Agent can suggest both saved recipes and offer to find new ones if no exact match

## User Scenarios & Testing

### Scenario 1: Spontaneous Save Offer

**Given** a user has received a generated recipe  
**When** they say "Wow, this Old Fashioned recipe is perfect!"  
**Then** the agent recognizes satisfaction and asks "Would you like me to save this recipe to your collection?"

### Scenario 2: Explicit Save Request

**Given** a user is viewing a generated recipe  
**When** they say "Save this recipe"  
**Then** the agent confirms, stores the recipe, generates an image, and displays the visual confirmation card.

### Scenario 3: Decline to Save

**Given** the agent offers to save a recipe  
**When** the user says "No thanks" or "Not this one"  
**Then** the conversation continues without saving and the agent doesn't re-prompt for the same recipe.

### Scenario 4: View Saved Recipes

**Given** a user has previously saved recipes  
**When** they ask "Show me my saved recipes"  
**Then** the agent lists only the recipe headers (names and types), not full recipe details.

### Scenario 5: Retrieve Specific Recipe by Name

**Given** a user has saved an "Old Fashioned" recipe  
**When** they ask "Get my Old Fashioned recipe"  
**Then** the agent displays the full saved recipe with its generated image.

### Scenario 5a: Search Saved Recipes by Ingredient

**Given** a user has saved "Old Fashioned" and "Whiskey Sour" recipes (both contain bourbon)  
**When** they ask "Do I have any recipes with bourbon?"  
**Then** the agent finds and presents both matching saved recipes from the recipe book.

### Scenario 6: Image Generation Feedback

**Given** a recipe is being saved  
**When** image generation is in progress  
**Then** the user sees feedback that the recipe is being saved and the image is being created.

### Scenario 7: Reject Saved Recipe

**Given** a visual confirmation card is displayed after saving  
**When** the user says "Actually, delete this" or rejects the recipe  
**Then** the recipe is removed from storage and the agent confirms deletion.

### Scenario 8: Modify Saved Recipe

**Given** a visual confirmation card is displayed after saving  
**When** the user says "Can you change the servings to 4?" or requests modifications  
**Then** the agent applies the changes to the saved recipe and updates the confirmation card.

## Success Criteria

| Criterion | Target | Measurement Method |
|-----------|--------|-------------------|
| Save Detection Accuracy | Agent correctly identifies save-worthy moments 90%+ of the time | Review of conversation samples |
| Save Workflow Completion | Users can complete save flow in under 10 seconds after confirmation | Timed user testing |
| Recipe Retrieval | Saved recipes are retrievable in future sessions | Verified persistence testing |
| Image Generation | Images are generated for 100% of saved recipes | Automated verification |
| Visual Confirmation | Confirmation card appears after every save | UI verification |
| User Satisfaction | Users successfully build recipe collections | User feedback surveys |

## Key Entities

### Saved Recipe
- Recipe ID (unique identifier)
- Recipe data (all fields from Recipe model)
- Generated image URL/reference
- User-defined tags
- Created timestamp
- Last accessed timestamp

### Recipe Collection
- List of saved recipe references
- Category groupings
- Search/filter capabilities

### Save Event
- Recipe being saved
- User confirmation timestamp
- Image generation status
- Completion status

## Assumptions

1. Users want to build a personal recipe collection over time
2. Image generation service is available and responsive
3. Storage solution can handle reasonable recipe volumes (hundreds per user)
4. Single user context (no multi-user collections initially)
5. Images are supplementary—recipes remain useful without them if generation fails
6. Existing Recipe model is sufficient for storage (no schema changes needed)

## Out of Scope

- Multi-user support and shared collections
- Non-blocking sentiment detection (separate ML/NLP pipeline for detecting satisfaction)
- Direct recipe browsing interface (users access recipes only through agent conversation)
- Export functionality (PDF, print, share)
- Nutritional information storage
- Shopping list integration
- Meal planning features
- Recipe versioning/modification history
- Offline access to saved recipes

## Dependencies

- Recipe Agent backend (spec 1-recipe-agent-backend)
- Agent Chat UI frontend (spec 3-agent-chat-frontend)
- Image generation service availability
- Persistent storage solution
- Generative UI capability in chat interface

## Clarifications

### Session 2024-12-02

- Q: How should satisfaction detection be implemented? → A: Via system prompt instructions, not a separate ML/NLP pipeline. Non-blocking detection is out of scope.
- Q: Should the system prompt be updated for recipe memory priority? → A: Yes, agent should search saved recipes first before web search and YouTube.
- Q: What happens if user rejects the saved recipe after confirmation card appears? → A: Recipe is deleted from storage.
- Q: What happens if user requests changes after confirmation card appears? → A: Changes are applied to the saved recipe.
- Q: Can users browse recipes directly? → A: No, users can only access recipes through agent conversation.
- Q: What does "show my recipes" display? → A: Only recipe headers (names and types), not full details.

---

*This specification defines WHAT the recipe storage feature should do. Implementation details will be addressed in the technical planning phase.*

