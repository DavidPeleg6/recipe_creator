# Quickstart Guide: Recipe Storage

**Feature**: 4-recipe-storage  
**Date**: December 2, 2025  

---

## Prerequisites

- Python 3.11+
- Existing Recipe Agent setup (from spec 1-recipe-agent-backend)
- Google AI API key (for Nano Banana Pro image generation)

---

## Quick Setup

### 1. Install New Dependencies

```bash
cd recipe_creator
uv pip install sqlalchemy google-generativeai google-cloud-storage Pillow
```

Or update requirements.txt and sync:

```bash
uv pip sync requirements.txt
```

**Note**: Uses the local `.venv` virtual environment. If not activated:

```bash
source .venv/bin/activate  # or on Windows: .venv\Scripts\activate
```

### 2. Configure Environment

Add to your `.env` file:

```bash
# Google AI for image generation (Nano Banana Pro)
GOOGLE_AI_API_KEY=your-google-ai-api-key
```

**Getting a Google AI API Key**:
1. Go to [Google AI Studio](https://aistudio.google.com)
2. Sign in with your Google account
3. Click "Get API Key" → "Create API key"
4. Copy the key to your `.env` file

### 3. Create Images Directory

```bash
mkdir -p recipe_creator/images
```

### 4. Initialize Database

The database initializes automatically on first use. Location: `recipe_creator/recipes.db`

---

## Verify Installation

### Start the CLI

```bash
cd recipe_creator
source .venv/bin/activate  # Ensure venv is active
python main.py
```

### Test Save Flow

```
You: How do I make an Old Fashioned?
[Agent provides recipe]

You: This is perfect! Save it!
[Agent saves recipe and shows confirmation]

You: Show me my saved recipes
[Agent lists saved recipe headers]
```

### Test Memory Priority

```
You: Do I have any bourbon recipes?
[Agent searches saved recipes FIRST, finds Old Fashioned]
```

---

## Troubleshooting

### "GOOGLE_AI_API_KEY not set"

Ensure your `.env` file contains the key and is in the `recipe_creator` directory.

### Image Generation Fails

- Check API key validity
- Free tier limited to 2 images/day
- Recipe saves successfully even without image

### Database Issues

Delete `recipes.db` to reset:

```bash
rm recipe_creator/recipes.db
```

---

## File Locations

| File | Purpose |
|------|---------|
| `recipes.db` | SQLite database (auto-created) |
| `images/` | Generated recipe images |
| `.env` | API keys and configuration |

---

## Next Steps

- Try saving different recipe types (cocktails, food, desserts)
- Test searching by ingredient ("recipes with chicken")
- Explore tag-based organization

---

*Setup complete. Happy cooking! 🍳🍹*

