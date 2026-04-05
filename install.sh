#!/bin/bash
# Install skills_loader into ~/bin so it's available from any project.

set -e

SKILLLOADER_HOME="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/bin"
TARGET="$BIN_DIR/skills_loader"

# Create ~/bin if needed
mkdir -p "$BIN_DIR"

# Write the wrapper script
cat > "$TARGET" <<EOF
#!/bin/bash
export SKILLLOADER_HOME="$SKILLLOADER_HOME"
exec python3 "\$SKILLLOADER_HOME/skills_sdk.py" "\$@"
EOF

chmod +x "$TARGET"

echo "✓ Installed: $TARGET"
echo "  SKILLLOADER_HOME=$SKILLLOADER_HOME"
echo ""

# Check if ~/bin is on PATH
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    SHELL_RC="$HOME/.zshrc"
    [ -n "$BASH_VERSION" ] && SHELL_RC="$HOME/.bashrc"

    echo "  ~/bin is not on your PATH. Adding it to $SHELL_RC..."
    echo '' >> "$SHELL_RC"
    echo '# SkillLoader' >> "$SHELL_RC"
    echo 'export PATH="$HOME/bin:$PATH"' >> "$SHELL_RC"
    echo "  Run: source $SHELL_RC"
    echo "  Or open a new terminal."
else
    echo "  ~/bin is already on PATH — ready to use."
fi

echo ""
echo "  Usage:"
echo "    cd /your/project"
echo "    skills_loader              # deploy skills to this project"
echo "    skills_loader categories   # browse the library"
echo "    skills_loader search seo   # search skills"
