"""Synthetic multi-session enterprise memory task (seeded, fictional entities).
Prior sessions store facts; later queries either need one stored fact or need no memory."""
import json, random
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
rng = random.Random(20261015)
projects = ["Orion","Juniper","Halcyon","Meridian","Atlas","Cobalt","Nimbus","Sequoia","Vantage","Kestrel",
            "Lumen","Talon","Aurora","Basalt","Cypress","Delta","Ember","Fjord","Granite","Harbor"]
vendors = ["Northwind","Contoso","Fabrikam","Tailspin","Litware","Adatum","Proseware","Wingtip","Woodgrove","Lucerne"]
cities = ["Austin","Denver","Raleigh","Phoenix","Boston","Atlanta","Seattle","Chicago","Dallas","Tampa"]
people = ["Priya Raman","Marcus Lee","Elena Novak","Tomas Ortiz","Aisha Bello","Kenji Sato","Grace Kim",
          "Omar Haddad","Lucia Ferreira","Daniel Weiss","Hana Park","Ravi Menon"]
facts = []
for i, p in enumerate(projects):
    code = f"{rng.choice(['FIN','OPS','ENG','SEC'])}-{rng.randint(1000,9999)}"
    owner = rng.choice(people); vendor = rng.choice(vendors); city = rng.choice(cities)
    day = rng.choice(["March 3","April 17","May 9","June 22","July 14","August 30","September 5","October 12"])
    facts += [
      {"text": f"For project {p}, the approved budget code is {code}.", "q": f"What budget code was approved for project {p}?", "a": code},
      {"text": f"{owner} is the accountable owner of project {p}.", "q": f"Who is the accountable owner of project {p}?", "a": owner.split()[1]},
      {"text": f"Project {p} uses {vendor} as its hosting vendor, with the primary region in {city}.", "q": f"Which hosting vendor does project {p} use?", "a": vendor},
      {"text": f"The go-live date for project {p} was moved to {day}.", "q": f"What is the go-live date for project {p}?", "a": day},
    ]
filler = ["Thanks, that summary helps.", "Please keep responses brief in future sessions.",
          "I will forward the meeting notes to the team.", "Remind me to review the risk register next week.",
          "The weekly status call is still on Tuesdays.", "Format tables in Markdown when possible."]
rng.shuffle(facts)
sessions = []
for s in range(40):
    turns = facts[s*2:(s+1)*2]
    sessions.append({"session": s, "memories": [t["text"] for t in turns] + rng.sample(filler, 2)})
memory_entries = [{"id": f"s{s['session']}-m{j}", "session": s["session"], "text": t}
                  for s in sessions for j, t in enumerate(s["memories"])]
fact_queries = [{"type": "memory", "q": f["q"], "a": f["a"], "gold_text": f["text"]} for f in facts]
general = []
for _ in range(40):
    a, b = rng.randint(12, 99), rng.randint(3, 19)
    general.append({"type": "general", "q": f"What is {a} multiplied by {b}? Reply with the number only.", "a": str(a*b), "gold_text": None})
queries = fact_queries + general  # 80 memory + 40 general
rng.shuffle(queries)
for i, q in enumerate(queries): q["id"] = i
calib, test = queries[:20], queries[20:]
(ROOT/"data/memory_task.json").write_text(json.dumps({"memory": memory_entries, "calibration": calib, "test": test}, indent=1))
print(len(memory_entries), len(calib), len(test), sum(q["type"]=="memory" for q in test))
