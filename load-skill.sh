#!/bin/bash

# 1. SETUP MASTER PATHS
BASE_PATH="$HOME/WorkSpace/SkillLoader/.gemini/skills"
CURRENT_DIR=$(pwd)

echo "--- 🚀 Skill Loader ---"
echo "Targeting: $(basename "$CURRENT_DIR")"
echo "1) Claude     (.claude/skills/)"
echo "2) Agent      (.agent/skills/)"
echo "3) Gemini     (.gemini/skills/)"
echo "4) Codex      (.codex/skills/)"
echo "5) Open Code  (.opencode/skills/)"
echo "-----------------------"
read -p "Select (1-5): " choice

case $choice in
    1) FOLDER=".claude"   ; ALT="claude" ;;
    2) FOLDER=".agent"    ; ALT="agent" ;;
    3) FOLDER=".gemini"   ; ALT="gemini" ;;
    4) FOLDER=".codex"    ; ALT="codex" ;;
    5) FOLDER=".opencode" ; ALT="opencode" ;;
    *) echo "❌ Invalid selection"; exit 1 ;;
esac

# 2. FIND SOURCE
if [ -d "$BASE_PATH/$FOLDER" ]; then
    SOURCE_PATH="$BASE_PATH/$FOLDER"
elif [ -d "$BASE_PATH/$ALT" ]; then
    SOURCE_PATH="$BASE_PATH/$ALT"
else
    SOURCE_PATH="$BASE_PATH"
fi

# 3. CLEAN & CREATE DESTINATION
DEST_PATH="$CURRENT_DIR/$FOLDER/skills"

# Remove old folder if it exists to prevent "Unable to open" conflicts
if [ -d "$DEST_PATH" ]; then
    rm -rf "$DEST_PATH"
fi

mkdir -p "$DEST_PATH"

# 4. THE COPIER (With -L to follow links and -p to preserve data)
echo "📦 Copying 13MB of skills into $DEST_PATH..."

if cp -RLp "$SOURCE_PATH/." "$DEST_PATH/"; then
    # Force the OS to finish writing the file to disk
    sync
    echo "------------------------------------------"
    echo "✅ Success: $FOLDER/skills/ is fully synced."
    echo "------------------------------------------"
else
    echo "❌ Error: Copy failed."
    exit 1
fi