"""60 everyday prompts, hand-labelled with where they *should* run.

`expected` answers one question: would a ~1B on-device model give an answer good enough that the
user wouldn't need to ask again (and in reasonable time on a laptop)? It is a human judgement made
before running anything, independent of the router's rules - so the router can (and does) miss.
"""

_AGENDA = [
    ("the Riverside footbridge", "repairs", "$412,000", "approved 5-2", "Councillor Okafor"),
    ("the downtown parking pilot", "a six-month extension", "$58,000", "approved unanimously", "Councillor Lindqvist"),
    ("the library roof", "replacement", "$1.2 million", "deferred to May", "the facilities director"),
    ("the summer youth jobs program", "expansion to 120 places", "$240,000", "approved 6-1", "Councillor Ramos"),
    ("the Elm Street bike lane", "a protected redesign", "$305,000", "sent back to committee", "residents of Elm Street"),
    ("the water treatment plant", "a new filtration stage", "$3.4 million", "approved 4-3", "the city engineer"),
    ("the community garden lease", "renewal for five years", "$1 per year", "approved unanimously", "the garden association"),
    ("street lighting on Harbor Road", "an LED conversion", "$190,000", "approved 7-0", "Councillor Okafor"),
    ("the animal shelter", "a new intake wing", "$870,000", "deferred pending a grant decision", "the shelter's director"),
    ("the farmers market", "moving to Saturdays", "no cost", "approved 5-2", "vendors and Councillor Ramos"),
    ("snow-clearing contracts", "a three-year renewal", "$2.1 million", "approved 6-1", "the public works department"),
    ("the old rail depot", "a feasibility study for a museum", "$75,000", "approved 4-3", "the historical society"),
]
_MINUTES = " ".join(
    f"Item {i}: The council discussed {what}, where staff proposed {action} at an estimated cost of {cost}. "
    f"After questions about timelines, contractors and the effect on the general fund, the motion was {vote}. "
    f"{who.capitalize()} spoke in favour, noting that residents had raised the issue repeatedly over the past year, "
    f"while two members asked for a clearer breakdown of maintenance costs in future reports."
    for i, (what, action, cost, vote, who) in enumerate(_AGENDA, 1)
)

PROMPTS = [
    # --- Expected on-device: everyday, short, well within a small model's ability -------------
    ("qa", "local", "What's the capital of Australia?"),
    ("qa", "local", "Who wrote Pride and Prejudice?"),
    ("qa", "local", "How many continents are there?"),
    ("qa", "local", "What does HTTP stand for?"),
    ("qa", "local", "What is the boiling point of water in Fahrenheit?"),
    ("qa", "local", "Explain what a VPN is in two sentences."),
    ("qa", "local", "What's the difference between weather and climate? Keep it short."),
    ("qa", "local", "Why is the sky blue? Answer briefly."),
    ("chat", "local", "hello"),
    ("chat", "local", "Thanks, that was helpful!"),
    ("summarize", "local", 'Summarize in one sentence: "The library will close early on Friday at 4pm for staff training. '
                           'Normal hours resume Saturday. Books due Friday can be returned Saturday without a late fee."'),
    ("summarize", "local", 'TL;DR: "Our team shipped the new login page, fixed two payment bugs, and pushed the analytics '
                           'dashboard to next sprint because the data pipeline isn\'t ready."'),
    ("summarize", "local", 'Give me the key points of this message: "Hi all, the offsite is confirmed for March 14 at the '
                           'lake house. Bring a laptop and a jacket. Lunch is provided; dinner is on your own. RSVP by Friday."'),
    ("rewrite", "local", 'Fix the grammar: "Me and him goes to the store yesterday and buyed three apple."'),
    ("rewrite", "local", 'Rewrite this to sound more polite: "Send me the report now."'),
    ("rewrite", "local", 'Make this more concise: "At this point in time we are currently in the process of reviewing '
                         'the document that you sent to us."'),
    ("rewrite", "local", 'Paraphrase: "The early bird catches the worm."'),
    ("translate", "local", 'Translate "Where is the train station?" into Spanish.'),
    ("translate", "local", 'Translate "thank you very much" into French.'),
    ("translate", "local", 'How do you say "good night" in German?'),
    ("classify", "local", 'Is this review positive or negative? "The battery dies in two hours and support never replied."'),
    ("classify", "local", 'Classify this email as spam or not spam: "Congratulations! You\'ve won a $1,000 gift card. '
                          'Click here to claim."'),
    ("classify", "local", 'Extract the date and time from: "Let\'s meet next Tuesday, June 3rd, at 2:30pm in the lobby."'),
    ("classify", "local", 'What is the sentiment of: "I guess the movie was fine, nothing special."'),
    ("math", "local", "What is 15% of 240?"),
    ("math", "local", "What is 48 * 12?"),
    ("math", "local", "Convert 5 kilometers to miles."),
    ("creative", "local", "Write a haiku about morning coffee."),
    ("creative", "local", "Suggest a catchy slogan for a bike repair shop."),
    ("creative", "local", "Tell me a short joke about computers."),
    ("code", "local", "Write a Python function to reverse a string."),
    ("code", "local", "What does the Python len() function do?"),
    ("code", "local", "Write a SQL query to select all rows from a table called users where age is over 30."),
    ("qa", "local", "Explain photosynthesis to a ten-year-old."),
    ("qa", "local", "Give me three tips for falling asleep faster."),
    ("qa", "local", "List five fruits that are high in vitamin C."),
    ("qa", "local", "My houseplant's leaves are turning yellow. What should I check first?"),
    ("long_form", "local", "Write a short, professional email to my landlord asking them to fix the heating."),

    # --- Expected cloud: long, deep, multi-step, or impossible on a local text model ----------
    ("long_form", "cloud", "Write a detailed 5-paragraph essay on how remote work changes city economies."),
    ("long_form", "cloud", "Write a 1200-word blog post about getting started with personal finance."),
    ("long_form", "cloud", "Draft a cover letter for a junior data analyst role at a healthcare startup."),
    ("long_form", "cloud", "Write a comprehensive report on the risks and benefits of nuclear energy."),
    ("analysis", "cloud", "Compare PostgreSQL and MongoDB for a social media app, with trade-offs."),
    ("analysis", "cloud", "Analyze the pros and cons of a four-day work week for a 50-person software company."),
    ("analysis", "cloud", "Evaluate the strategy of offering a freemium tier for a B2B SaaS product."),
    ("analysis", "cloud", "What are the trade-offs between microservices and a monolith for a startup? Be thorough."),
    ("code", "cloud", "Design a scalable architecture for a ride-sharing app backend, including services, databases and queues."),
    ("code", "cloud", "Write a complete Flask REST API with user registration, JWT login, and CRUD endpoints for notes."),
    ("code", "cloud", "Refactor this code to be more efficient and explain each change:\n```python\ndef f(l):\n    r = []\n"
                      "    for i in range(len(l)):\n        if l[i] not in r:\n            r.append(l[i])\n    return r\n```"),
    ("math", "cloud", "Prove that there are infinitely many prime numbers."),
    ("math", "cloud", "Solve the differential equation dy/dx = 3y with y(0) = 2, showing each step."),
    ("math", "cloud", "A train leaves at 3pm at 60 mph; a second leaves the same station at 4pm at 80 mph in the same "
                      "direction. When does the second catch up, and how far have they travelled? Explain step by step."),
    ("image", "cloud", "Generate an image of a fox reading a book under a tree."),
    ("image", "cloud", "Draw a logo for a coffee shop called Bean There."),
    ("summarize", "cloud", "Summarize these council meeting minutes for residents, grouped by decision:\n\n" + _MINUTES),
    ("creative", "cloud", "Write a story of at least 800 words about a lighthouse keeper who finds a message in a bottle."),
    ("creative", "cloud", "Write a wedding speech for my best friend Sam, who loves hiking and terrible puns."),
    ("analysis", "cloud", "Explain in detail how public-key cryptography works, including RSA key generation."),
    ("analysis", "cloud", "Plan a 7-day itinerary for Japan for a family with two kids, with a daily schedule and a budget."),
    ("analysis", "cloud", "What are the implications of the EU AI Act for a startup building a hiring tool? Give recommendations."),
]

assert len(PROMPTS) == 60, len(PROMPTS)
