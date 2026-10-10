# Benchmark summary (60 prompts, local `llama3.2:1b`, cloud `gemma-4-26b-a4b-it`, judge `gemma-4-26b-a4b-it`)

## Routing

| Metric | Value |
|---|---|
| Agreement with hand labels | 57/60 (95.0%) |
| Routed on-device | 58.3% |
| Labelled local, routed cloud | 3 |
| Labelled cloud, routed local | 0 |

## Quality of the local model's answers (judged against the cloud answer)

| Group | Prompts | Local answer acceptable | Mean score (1-5) |
|---|---|---|---|
| Router sent on-device | 35 | 85.7% | 4.43 |
| Router sent to cloud (local answer generated anyway) | 23 | 17.4% | 2.04 |

## Latency on this laptop

| Metric | Seconds |
|---|---|
| Local, median (prompts routed on-device) | 4.4 |
| Local, 90th percentile | 12.8 |
| Cloud, median (same prompts) | 5.82 |
| Local generation speed, median | 12.2 tokens/s |

## Estimated footprint (25 W device, 458 gCO2e/kWh grid)

| Scenario | Energy (Wh) | Water (mL) | CO2e (g) |
|---|---|---|---|
| All cloud | 14.4 | 15.6 | 1.8 |
| GreenRoute | 7.538 | 6.5 | 1.455 |
| GreenRoute + re-asking weak local answers in the cloud | 8.738 | 7.8 | 1.605 |

Saving vs all-cloud: energy 47.6%, water 58.3%, CO2e 19.2% (with retries: 39.3% / 50.0% / 10.9%).

Break-even device power: routing locally saves energy below ~136 W of extra draw while generating, on this prompt mix.

| Device power while generating | Energy saving vs all-cloud |
|---|---|
| 10 W | 54.1% |
| 25 W | 47.6% |
| 60 W | 32.7% |
| 150 W | -5.8% |

## Routing misses

- expected local, routed cloud (code, 0.48): What does the Python len() function do?
- expected local, routed cloud (code, 0.48): Write a SQL query to select all rows from a table called users where age is over 30.
- expected local, routed cloud (unknown, 0.3): Write a short, professional email to my landlord asking them to fix the heating.

## Weak local answers the router let through

- score 2: TL;DR: "Our team shipped the new login page, fixed two payment bugs, and pushed the analyt - The candidate answer misrepresents the reason for the delay, changing the specific technical blocker (data pipeline) into a vague, inaccurate statement about ensuring readiness.
- score 2: Fix the grammar: "Me and him goes to the store yesterday and buyed three apple." - The candidate failed to correct the subject pronouns, leaving 'Me and him' which is grammatically incorrect.
- score 2: Translate "Where is the train station?" into Spanish. - The candidate only translates part of the requested sentence, omitting the 'Where is' component.
- score 2: How do you say "good night" in German? - While the candidate provides the correct phrase, it includes several incorrect translations and a grammatically wrong variation, which is misleading to a learner.
- score 2: Extract the date and time from: "Let's meet next Tuesday, June 3rd, at 2:30pm in the lobby - The candidate failed to extract the specific date, providing only the day of the week and omitting 'June 3rd'.
