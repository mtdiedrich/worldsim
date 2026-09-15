"""Configuration constants for worldsim."""

# LLM configuration
MODEL = "claude-haiku-4-5-20251001"  # fast + cheap; the world is largely LLM-authored now
MAX_RETRIES = 2
TEMPERATURE = 1.0  # Variable for varied behavior; can be 0.0 for reproducibility
AGENT_MAX_TOKENS = 1400        # per-agent response budget
CHRONICLER_MAX_TOKENS = 4000   # the Chronicler writes long; give it room so JSON never truncates

# Simulation configuration
N_TICKS = 12
RUN_SEED = 42
YEARS_PER_TICK = 25  # each tick is about a generation; world history spans an age

# Resource types
RESOURCES = ["food", "ore", "wealth"]

# Action types
ACTION_TYPES = ["trade", "migrate", "attack", "innovate", "build", "diplomacy",
                "found", "marry", "subjugate", "hold"]

# --- emergent layer (Chronicler + living cast) ---
CHRONICLER_MODEL = MODEL       # the Chronicler narrates emergent history each tick
MAX_CULTURES = 14              # cap on how many peoples can exist at once
MAX_SPAWN_PER_TICK = 2         # at most this many new peoples born per generation
SCHISM_POP_FRACTION = 0.30     # share of a parent's population a schism takes with it
REBELLION_POP_FRACTION = 0.25  # share that rises with a successful rebellion

# Relations bounds
MIN_RELATION = -100
MAX_RELATION = 100

# Memory configuration
MEMORY_WINDOW = 8  # Number of recent events to keep in memory
MAX_BELIEFS_CHARS = 600
MAX_NOTE_CHARS = 120

# --- economy (civilizational scale; populations in the tens of thousands) ---
FOOD_PER_POP = 800        # 1 food consumed per tick per this many people
GROWTH_DIVISOR = 25       # well-fed population grows by population // GROWTH_DIVISOR (~4%/tick)
STARVE_FRACTION = 0.10    # fraction of population lost per tick while starving
GROWTH_EVENT_MIN = 500    # only emit a growth event when growth is at least this large
RANDOM_EVENT_CHANCE = 0.45  # chance of one world event per tick
SETTLE_FOOD_COST = 40     # food cost to settle an empty region

# --- cliodynamics engine (geography -> feedback loops -> emergent history) ---
# Carrying capacity
K_PER_FOOD = 1200          # carrying capacity per unit of (food + traded-food) yield
TRADE_K_FACTOR = 0.5       # how much a region's wealth-yield converts to importable food
TECH_K_BONUS = 0.50        # each point of tech_level raises carrying capacity by this fraction
# Malthusian population
POP_GROWTH = 0.22          # logistic growth per generation when well below capacity
STARVE_RATE = 0.30         # fraction of the over-capacity excess that dies per generation
EXTINCT_POP = 800          # below this a landless people is finished
# Secular cycle (elites, instability)
ELITE_SHARE_0 = 0.02       # baseline elite fraction of population
ELITE_GROWTH = 0.12        # elite reproduction premium in good times
ELITE_OVERPRODUCE = 0.03   # elites grow even in bad times (overproduction)
INSTAB_GAIN = 0.40         # instability gained per generation under pressure
INSTAB_DECAY = 0.18        # instability shed per generation when healthy
COLLAPSE_THRESHOLD = 1.0   # instability at which a polity fractures
# Asabiyya (cohesion)
ASAB_GAIN = 0.18           # cohesion gained per generation on a hard frontier
ASAB_DECAY = 0.05          # cohesion lost per generation to imperial size
ASAB_STRIFE_DECAY = 0.12   # extra cohesion lost to internal instability
# Expansion and war
EXPANSION_HUNGER = 0.70    # N/K above which a polity hungers for more land
COHESION_EXPAND = 0.62     # cohesion above which a polity expands even when fed
CONQUEST_EDGE = 1.15       # attacker power must exceed defender's by this to seize a region
# Diffusion
DIFFUSE_RATE = 0.25        # fraction of the tech gap to a neighbour closed per generation
INNOVATE_CHANCE = 0.30     # chance per generation of an endogenous tech advance
# Shocks
PLAGUE_CHANCE = 0.22       # chance per generation of a plague
CLIMATE_CHANCE = 0.18      # chance per generation of a climate swing

# --- dynasties and rulers ---
RULER_START_AGE = 30      # age a new ruler takes the throne
RULER_DEATH_AGE = 55      # death risk climbs steeply past this age
RULER_VIOLENCE_CHANCE = 0.06  # flat per-generation chance of death by accident/violence at any age

# --- layered sovereignty ---
TRIBUTE_FRACTION = 0.15   # share of a tributary's wealth sent to its overlord each tick
SUBJUGATE_STRENGTH_RATIO = 1.4  # how much stronger you must be to force vassalage
FOUND_WEALTH_COST = 30    # founding an institution costs wealth (keeps it occasional)
