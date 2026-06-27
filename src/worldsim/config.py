"""Configuration constants for worldsim."""

# LLM configuration
MODEL = "claude-sonnet-4-6"  # Fast and capable - good balance for many calls per run
MAX_RETRIES = 2
TEMPERATURE = 1.0  # Variable for varied behavior; can be 0.0 for reproducibility

# Simulation configuration
N_TICKS = 10
RUN_SEED = 42

# Resource types
RESOURCES = ["food", "ore", "wealth"]

# Action types
ACTION_TYPES = ["trade", "migrate", "attack", "innovate", "build", "diplomacy", "hold"]

# Relations bounds
MIN_RELATION = -100
MAX_RELATION = 100

# Memory configuration
MEMORY_WINDOW = 8  # Number of recent events to keep in memory
MAX_BELIEFS_CHARS = 600
MAX_NOTE_CHARS = 120

# --- v2 economy ---
FOOD_PER_POP = 100           # 1 food eaten per tick per this many people
GROWTH_DIVISOR = 20          # population grows by population // GROWTH_DIVISOR when well-fed
STARVE_DEATHS_PER_FOOD = 15  # deaths per unit of food deficit
RANDOM_EVENT_CHANCE = 0.30   # chance of one world event per tick
