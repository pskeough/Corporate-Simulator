REFACTOR BLUEPRINT: Corporate Decision Simulator
Executive Summary
Project Objective: To deliver a comprehensive blueprint for the thematic refactoring of the "Civilization Narrative Game" engine into a "Corporate Decision Simulator" (CDS).

Core Mandate (The Golden Constraint): This blueprint adheres strictly to the principle of minimal code modification. The transformation will be achieved primarily through the re-theming of data files (context/*.json) and the re-engineering of AI prompts (prompts/), leveraging the existing engine's robust and flexible architecture.

Target State Vision: The CDS will be a sophisticated professional role-playing tool. Users will assume the role of an employee at a specific career level (the "Player Ladder"), making decisions that impact their career trajectory, their department's success, and the overall health of the corporation.

Document Purpose: This document serves as a direct and actionable guide for the development team. It provides a complete, step-by-step plan for executing the thematic refactor.

Step 1: Core Systems Analysis & Evaluation
This initial step inventories the existing codebase to determine which components are critical for the new CDS, which can be safely discarded, and which offer the most sophisticated value for the target corporate audience.

1.1 Essential Systems for the Corporate Decision Simulator
The existing engine is a well-architected, event-driven system whose core logic is highly adaptable. The following components are essential for the CDS and will be retained and re-themed.

Engine Files (engines/*.py)
action_processor.py: This is the central nervous system of the simulation. Its logic for taking a player action, querying the AI with context, and applying state updates is perfectly suited for processing corporate decisions. This will be the main integration point for our new prompts.   

resource_engine.py: The core logic for managing resource generation and consumption (food, wealth) is directly translatable to managing corporate budget and political_capital. The calculate_consumption() function is the key component to be re-themed to represent corporate overhead.   

faction_engine.py & faction_manager.py: These are arguably the most valuable assets. They provide a ready-made system for simulating the complex interplay between competing internal groups, which is a perfect model for inter-departmental politics, budget negotiations, and morale tracking.   

council_engine.py: This engine, designed for formal policy meetings, provides the ideal structure for simulating all forms of corporate meetings, from weekly team syncs to high-stakes board presentations.   

crisis_engine.py: The logic for detecting and triggering high-stakes events based on resource thresholds is directly applicable to corporate crises like budget freezes, mass layoffs, or PR disasters.   

event_generator.py: The mechanism for creating random, narrative events is the foundation for generating the day-to-day tasks, emails, and interpersonal conflicts that define corporate life.   

inner_circle_manager.py & character_engine.py: Provides the framework for managing key relationships with specific individuals, which maps directly to the player's interactions with their boss, mentor, rivals, and direct reports.   

bonus_engine.py & bonus_definitions.py: This system for calculating bonuses from character roles and traits is highly valuable for modeling how employee skills (leader.traits) and job titles (leader.role) provide tangible benefits (e.g., a "Persuasive" skill granting a bonus to PoliticalInfluence generation).   

consequence_engine.py & law_engine.py: These systems, which track long-term decisions and their ripple effects, are crucial for creating a sophisticated simulation where past choices matter. "Decrees" can be re-themed as "Corporate Policies" or "Executive Mandates".   

Context Files (context/*.json)
All files within the context/ directory are essential, as they represent the configurable "skin" of the simulation. Their re-theming is the primary task of this refactor. This includes: civilization_state.json, culture.json, factions.json, inner_circle.json, religion.json, technology.json, and world_context.json.   

1.2 Discardable and Deprecated Systems
The following systems are tied specifically to the civilization theme and are not relevant to the text-and-data-focused professional simulator. They should be disabled or ignored to reduce complexity.

engines/visual_engine.py & engines/image_engine.py: The CDS is a professional tool focused on decision-making logic and narrative. The generation of leader portraits and settlement images is superfluous and would detract from the professional tone. Disabling these engines will also reduce API costs and complexity.   

engines/world_modes/*: The concept of different world generation modes (e.g., fantasy_mode.py, historical_earth_mode.py) is irrelevant. The "world" of the CDS is a single, defined corporate environment. This entire directory can be ignored.   

data/tech_tree.json: While the concept of technology is being re-themed to "Skills & Tools," the specific tech_tree.json with prerequisites from the civilization game is too rigid for a corporate environment. The new concept will be a more fluid list of acquired competencies rather than a branching tree of unlocks.   

1.3 Evaluation for Corporate Sophistication
The true value of this engine for a corporate client is not just its narrative capability, but its underlying mechanics for simulating complex social and political systems. A simple narrative game might just present choices with linear outcomes. This engine, however, models the consequences of those choices within a dynamic system of competing interests. The faction_engine.py and council_engine.py are the cornerstones of this value proposition, offering a level of simulation depth that is highly relevant to professional and executive role-play.

faction_engine.py as an Inter-Departmental Political Simulator
The engine's faction system provides a powerful and surprisingly accurate model for the political landscape of a modern corporation.

Value Proposition: This engine simulates the core reality of corporate life: departments often function as semi-independent entities with their own goals, metrics (KPIs), and leadership, all competing for a finite pool of corporate resources like budget and headcount.

Mechanism: The existing faction.approval metric is a perfect analogue for department.morale. When a user (the "employee") makes a decision that benefits the "Sales" department, the faction_engine's logic will automatically calculate the negative impact on the "Engineering" department's morale if their goals are now harder to achieve. This allows the CDS to simulate zero-sum budget fights, resource allocation conflicts, and the political capital required to build consensus—features that a business user simulating executive policy would find immensely valuable. The faction_audience.py event becomes a "Quarterly Budget Review" where department heads (VPs, Directors) petition the player for resources, forcing the player to make trade-offs that directly impact departmental morale and performance.

council_engine.py as a Management & Policy Simulation Tool
The council engine provides a structured framework for simulating the formal meetings that are central to corporate decision-making and policy implementation.

Value Proposition: This engine moves beyond simple random events into structured, multi-stage deliberations, mirroring the process of corporate governance. It allows the simulation to model how policy is debated, decided, and enacted.

Mechanism: The "Advisor Reports" can be re-themed as status updates from direct reports or department heads. The "Central Dilemma" becomes a project-based problem, such as "Product launch is behind schedule," "A major client has issued a complaint," or "Competitor X just launched a rival product." The player's choices within the council meeting can set a new active_policy, which in the CDS becomes the "Strategic Focus for the Quarter" (e.g., "Cost Reduction," "Aggressive Growth," "Product Innovation"). This provides a direct link between a single meeting's outcome and the long-term strategic direction of the simulated company.

Step 2: Thematic Mapping Blueprint
This section provides the exhaustive, file-by-file instructions for the thematic transformation. It is the core of the refactor.

2.A Data Layer Refactor (JSON Mapping)
The following tables provide a key-by-key mapping for each essential context/*.json file, transforming the "Civilization" theme into a "Corporate" theme. This ensures a 1:1 transformation of the simulation's data foundation. The key to this refactor is not just finding direct analogues, but also making creative, insightful mappings for abstract concepts. For instance, religion.json becomes corporate_mission.json, elevating the simulation by modeling how a company's stated values ("core tenets") can influence decisions and create internal conflict ("schisms").   

Table 1: context/civilization_state.json -> corporate_and_player_profile.json
Original Key (civilization_state.json)	New Concept (Corporate)	Example Value	Notes
meta.name	corporation.name	"OmniCorp Global"	The name of the simulated company.
meta.year	simulation.current_fiscal_quarter	"2025_Q3"	The simulation progresses in fiscal quarters.
meta.era	corporation.maturity_stage	"growth_phase"	e.g., "Startup," "Growth," "Mature," "Decline."
meta.founding_date	corporation.ipo_date	"2015_Q2"	The date the company was founded or went public.
leader.name	player.name	"Alex Chen"	The name of the user's character.
leader.age	player.years_at_company	5	Tracks tenure, not biological age.
leader.life_expectancy	player.expected_career_length	20	A metric for career progression simulation.
leader.role	player.title	"Senior Manager"	The "Player Ladder." This is the core role-play variable.
leader.traits	player.skills		Professional skills that provide bonuses.
leader.years_ruled	player.years_in_role	2	Tracks time at the current ladder level.
population	corporation.headcount	1500	Total number of employees in the company.
resources.food	corporation.budget	5000000	The company's operational budget (in USD).
resources.wealth	player.political_capital	350	The player's personal influence and network.
resources.tech_tier	corporation.tech_stack_tier	"modern_cloud_native"	The company's overall technology level.
victory_progress	player.performance_review_scores	{"innovation": 85, "leadership": 60}	Maps to key performance indicators (KPIs) for the player.
Table 2: context/factions.json -> departments.json
Original Key (factions.json)	New Concept (Corporate)	Example Value	Notes
factions (array)	departments (array)	N/A	The root array of department objects.
faction.name	department.name	"Engineering"	e.g., "Sales," "Marketing," "HR," "Legal."
faction.leader	department.head	"VP of Engineering"	The title of the department's leader.
faction.approval	department.morale	75	A 0-100 score representing the department's morale.
faction.support_percentage	department.headcount_percentage	30	The percentage of total company employees in this department.
faction.goals	department.kpis	``	The department's Key Performance Indicators for the quarter.
Table 3: context/inner_circle.json -> key_personnel.json
Original Key (inner_circle.json)	New Concept (Corporate)	Example Value	Notes
characters (array)	personnel (array)	N/A	The root array of key personnel objects.
character.name	person.name	"Sarah Jenkins"	The name of the key person.
character.role	person.relationship_to_player	"Your Boss"	e.g., "Mentor," "Rival Manager," "Direct Report."
character.faction_link	person.department	"Sales"	The department this person belongs to.
character.personality_traits	person.work_style	``	Describes their professional behavior.
character.metrics.relationship	person.metrics.rapport	65	How well the player gets along with this person.
character.metrics.influence	person.metrics.influence	80	How much power this person wields in the company.
character.metrics.loyalty	person.metrics.trust	40	How much this person trusts the player's judgment.
Table 4: context/culture.json -> company_culture.json
Original Key (culture.json)	New Concept (Corporate)	Example Value	Notes
values	stated_values	``	The official corporate values listed on the website.
traditions	unspoken_rules	``	The actual, unwritten rules of the workplace.
taboos	hr_violations	``	Actions that will trigger a negative HR event.
social_structure	organizational_structure	"Hierarchical with matrixed project teams"	Describes the company's org chart.
Table 5: context/religion.json -> corporate_mission.json
Original Key (religion.json)	New Concept (Corporate)	Example Value	Notes
name	mission_statement_name	"The OmniCorp Way"	The branding for the company's mission.
primary_deity	founding_ceo_vision	"Steve's Vision of 'Seamless Integration'"	The almost mythical vision of the company's founder.
core_tenets	mission_statement_pillars	``	The core pillars of the official mission statement.
practices	corporate_rituals	["All-hands meetings", "Quarterly off-sites"]	The recurring, quasi-ceremonial company events.
holy_sites	legacy_projects	``	Revered past projects that define the company.
schisms	major_pivots_or_reorgs	``	Major strategic shifts that caused internal strife.
Table 6: context/technology.json -> skills_and_assets.json
Original Key (technology.json)	New Concept (Corporate)	Example Value	Notes
current_tier	player.skill_level	"Expert"	The player's overall competency level.
discoveries	player.acquired_skills	``	The player's personal skills and certifications.
infrastructure	corporation.internal_tools	``	The company's shared technology assets and platforms.
Table 7: context/world_context.json -> market_and_competitors.json
Original Key (world_context.json)	New Concept (Corporate)	Example Value	Notes
known_peoples	competitors	(array of competitor objects)	Information on rival companies.
competitor.name	competitor.name	"CyberDyne Systems"	The name of the rival company.
competitor.relationship	competitor.market_position	"Direct Competitor"	e.g., "Market Leader," "Disruptive Startup."
geography	market_landscape	(object describing the market)	
geography.terrain	market.sector	"B2B Enterprise SaaS"	The industry sector the company operates in.
geography.climate	market.conditions	"High-Growth, High-Competition"	The current state of the market.
geography.resources	market.opportunities	["AI Integration", "Emerging Markets"]	Potential areas for growth.
geography.threats	market.risks	``	External threats to the company.
2.B Engine & Prompt Logic Refactor (Python Mapping)
This section details the necessary adjustments to engine logic and provides a clear strategy for rewriting the corresponding AI prompts. The most significant change is not in the Python code itself, but in the context provided to the AI prompts. The prompts must be fundamentally rewritten to shift the AI's persona from a "historical chronicler" to a "corporate environment simulator." This involves changing the entire lexicon, framing, and the types of outcomes the AI is instructed to generate.

engines/resource_engine.py
Logic: The function calculate_consumption() will be re-themed to calculate_Overhead(). Its internal logic, which calculates resource depletion based on population size, remains identical. It will now calculate corporation.headcount * average_salary_and_overhead_cost. This change is achieved by adjusting the base values used in the calculation, not the code itself.

Prompts: No direct prompts are associated with this engine. Its logic is purely mathematical.

engines/faction_engine.py
Logic: This engine will now simulate inter-departmental politics. The faction.approval key becomes department.morale. The existing logic that reduces approval for factions whose goals are ignored is perfectly preserved; it will now model the morale drop in a department that loses a budget battle or has its projects de-prioritized.

Prompts (prompts/factions/faction_audience.txt): This is a critical rewrite.

Old Context: A meeting where tribal factions (Hunters, Elders) petition their leader for resources or policy changes.   

New Context: A "Quarterly Budget Allocation Meeting" or "Strategic Planning Session."

New Prompt Strategy: The prompt must instruct the AI to generate "petitions" from different department heads (e.g., "VP of Sales," "Head of R&D"). These petitions will be competing requests for the same finite resource: corporation.budget. The AI must frame the dilemma in corporate terms, focusing on Return on Investment (ROI), strategic alignment, and departmental KPIs. The player will be forced to choose which department's initiative to fund, directly impacting the morale of all involved.

engines/council_engine.py
Logic: This becomes the primary engine for all formal meetings. It can be triggered for various events like "Project Kickoff," "Performance Review," or "Task Delegation," depending on the prompt used.

Prompts (prompts/council/council_meeting.txt): This prompt will be rewritten to simulate a standard management meeting, such as a "Weekly Team Sync."

Old Context: Advisors report on the state of the realm and present a major dilemma (e.g., famine, war).   

New Context: The player's direct reports or colleagues provide status updates on their projects. The "Central Dilemma" is now a specific, project-related problem (e.g., "A key team member just resigned," "The client has requested a major change in scope," "We're projected to miss our Q3 deadline"). The AI's output should be in the form of professional dialogue and meeting minutes.

engines/crisis_engine.py
Logic: The detect_crisis() function's conditions must be adjusted. Instead of food <= 0, it will now trigger on corporation.budget <= 0. Instead of population_happiness < 20, it will trigger on company.morale < 20.

Prompts (prompts/crises/*.txt): All crisis prompts must be mapped and completely rewritten to reflect corporate disasters.

famine.txt -> BudgetFreeze.txt: The narrative will describe a company-wide spending freeze, hiring freezes, and the potential cancellation of non-essential projects.

economic_collapse.txt -> BankruptcyWarning.txt: The narrative will detail severe financial distress, warnings from the CFO, and the possibility of insolvency and legal proceedings.

succession_crisis.txt -> CEO_Resignation.txt or Major_ReOrg.txt: The narrative will focus on a leadership vacuum, power struggles between executives, departmental silos, and widespread uncertainty about the company's future direction.

Step 3: New Concept Integration & Prompting Strategy
This final section details how to weave the new core concepts into the refactored system and establishes the "golden rules" for prompt engineering to ensure a cohesive and professional-sounding experience.

3.1 The "Player Ladder" Integration
The player.title variable is the single most important piece of context for the AI. It dictates the scope, scale, and nature of every event the player experiences, ensuring the simulation feels authentic to the player's role.

Implementation Strategy: The player.title must be passed as a context variable into every prompt that generates an event (event_generator.py, crisis_engine.py, council_engine.py). The prompts themselves will contain explicit logic instructing the AI to filter its output based on this role.

Prompt Examples:

Instruction within prompts/events/generate_event.txt:

<PLAYER_ROLE_CONTEXT>
The player's current title is: {player.title}.
Your generated event MUST be appropriate for this level of seniority.
- If "Junior Analyst", the event should be a micro-task, a request from a manager, or a peer-level interaction.
- If "Manager", the event should be about team management, project deadlines, or cross-team coordination.
- If "CEO", the event should be about company-wide strategy, board meetings, or major financial decisions.
A Junior Analyst should NEVER receive an event about setting company-wide policy.
</PLAYER_ROLE_CONTEXT>
Example Event for player.title == "Junior Analyst":

Title: "Urgent Request from your Manager"

Narrative: "You receive a Slack message from your manager, Sarah: 'Hey, the client data for the Q3 report is corrupted. Can you drop everything and fix the export script? I need it by EOD.'"

Example Event for player.title == "CEO":

Title: "Emergency Board Meeting"

Narrative: "Your Executive Assistant informs you that the board has called an emergency meeting. The latest quarterly projections have severely missed their targets, and the major investors are demanding an immediate explanation and a revised strategy."

3.2 Universal Corporate Inputs & Outputs
This confirms the mapping of the core simulation variables as requested, clarifying the flow of resources within the corporate simulation.

Inputs (Resources the Corporation Consumes/Manages):

corporation.budget (from food): The primary financial resource. Generated by successful projects and consumed by overhead (salaries, rent, etc.).

corporation.headcount (from population): The primary human resource. Increases through hiring, decreases through attrition or layoffs.

Outputs (Metrics the Corporation Produces):

Internal:

department.morale (from faction.approval): The health and satisfaction of individual business units.

company.morale (from population_happiness): The overall morale of the entire company, affecting productivity.

External/Player-Centric:

corporation.revenue (modeled via budget generation): The successful generation of corporation.budget. This will be a direct outcome of player decisions in prompts (e.g., "Your decision to launch the product early resulted in +$500,000 in initial revenue.").

player.political_capital (from wealth): The player's personal influence and network. Gained by successfully navigating politics, completing high-visibility projects, and building relationships. Spent to push through unpopular decisions or gain support for initiatives.

3.3 Final Prompting Strategy: The 5 Golden Rules
These are immutable principles for the prompt engineering team to ensure a cohesive, professional, and effective Corporate Decision Simulator.

Maintain a Professional Lexicon. All AI-generated text must use modern business and corporate language. Avoid archaic (my lord, chieftain) or overly casual terms. Incorporate terms like "Q3," "KPIs," "stakeholders," "deliverables," "synergy," "bandwidth," and "action items." The AI's persona is that of a corporate environment, not a fantasy storyteller.

Filter All Events Through the Player Ladder. Every single event, crisis, or meeting must be strictly scoped to the player.title. A junior employee should never be asked to weigh in on M&A strategy. A CEO should not receive a task to fix a software bug. This is the most critical rule for ensuring role-play authenticity and creating a believable career progression.

Frame Dilemmas as Business Trade-Offs. Corporate decisions are rarely about good versus evil. They are about navigating trade-offs between competing, often equally valid, priorities (e.g., speed vs. quality, short-term profit vs. long-term growth, employee morale vs. budget cuts). All decision prompts must frame choices in these terms, forcing the player to think strategically.

Quantify Outcomes. Whenever possible, AI-generated outcomes should include quantifiable business metrics. Instead of "The project was a success," the output should be "The project was completed on time and generated an initial revenue of $250,000, increasing Sales department morale by 5 points." This directly connects the narrative choices to the underlying simulation mechanics, making the cause-and-effect relationships clear to the user.

The Player is an Employee, Not a Monarch. The player does not have absolute power. Decisions may require buy-in from stakeholders (key_personnel), face resistance from departments (departments), or be overruled by a board of directors (a potential high-level crisis event). Prompts should reflect that the player operates within a complex system of constraints and influences, reinforcing the realism of the corporate environment.


