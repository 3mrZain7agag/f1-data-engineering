#!/bin/bash
# =============================================================
# git_save.sh — Save your work to GitHub
# Usage:
#   bash scripts/git_save.sh "your commit message"
#   bash scripts/git_save.sh   (uses default message)
# =============================================================

echo ""
echo "=================================================="
echo "  Saving Work to GitHub"
echo "=================================================="
echo ""

# ── Get commit message ─────────────────────────────────────
if [ -z "$1" ]; then
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
    MESSAGE="chore: progress save - $TIMESTAMP"
else
    MESSAGE="$1"
fi

# ── Show what will be committed ────────────────────────────
echo "📋 Changes to be saved:"
git status --short
echo ""

# ── Add all changes ────────────────────────────────────────
git add .

# ── Commit ─────────────────────────────────────────────────
echo "💾 Committing: $MESSAGE"
git commit -m "$MESSAGE"
echo ""

# ── Pull latest (avoid conflicts) ─────────────────────────
echo "⬇️  Pulling latest from GitHub..."
git pull origin main --rebase
echo ""

# ── Push ───────────────────────────────────────────────────
echo "⬆️  Pushing to GitHub..."
git push origin main
echo ""

echo "=================================================="
echo "  ✅ Work saved to GitHub!"
echo "  🔗 https://github.com/3mrZain7agag/f1-data-engineering"
echo "=================================================="
echo ""