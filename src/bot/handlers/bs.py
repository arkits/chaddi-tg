import random

from telegram import Update
from telegram.ext import ContextTypes

from src.domain import dc


def generate_bullshit():
    """Generate a single bullshit sentence."""
    adjectives = [
        "strategic",
        "seamless",
        "value-added",
        "leveraged",
        "synergistic",
        "proactive",
        "holistic",
        "integrated",
        "scalable",
        "robust",
        "best-of-breed",
        "cross-functional",
        "mission-critical",
        "game-changing",
        "revolutionary",
        "disruptive",
        "innovative",
        "agile",
        "dynamic",
    ]

    nouns = [
        "synergy",
        "paradigm shift",
        "value proposition",
        "core competency",
        "best practice",
        "ecosystem",
        "mindshare",
        "bandwidth",
        "pivot point",
        "deliverable",
        "stakeholder",
        "initiative",
        "roadmap",
        "milestone",
        "key performance indicator",
        "win-win scenario",
        "thought leadership",
        "value chain",
    ]

    verbs = [
        "leverage",
        "empower",
        "optimize",
        "streamline",
        "synergize",
        "drive",
        "enhance",
        "facilitate",
        "accelerate",
        "champion",
        "revolutionize",
        "disrupt",
        "innovate",
        "maximize",
        "deliver",
    ]

    # Generate random sentence structure
    structures = [
        f"We need to {random.choice(verbs)} our {random.choice(nouns)} to {random.choice(verbs)} {random.choice(nouns)}.",
        f"Our {random.choice(adjectives)} {random.choice(nouns)} will {random.choice(verbs)} {random.choice(nouns)}.",
        f"The {random.choice(adjectives)} {random.choice(nouns)} is key to {random.choice(verbs)} {random.choice(nouns)}.",
        f"Let's {random.choice(verbs)} {random.choice(adjectives)} {random.choice(nouns)} to {random.choice(verbs)} {random.choice(nouns)}.",
        f"Going forward, we will {random.choice(verbs)} our {random.choice(adjectives)} {random.choice(nouns)}.",
    ]

    return random.choice(structures)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dc.log_command_usage("bs", update)
        bullshit = generate_bullshit()
        await update.message.reply_text(bullshit)
    except Exception:
        await update.message.reply_text("Error generating corporate bullshit!")
