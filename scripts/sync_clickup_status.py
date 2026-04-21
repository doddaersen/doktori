import json
import os
import re
import sys
from pathlib import Path

import requests

API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
LIST_ID = os.getenv("CLICKUP_LIST_ID", "901510802421")
STATUS_FILE = Path("status.json")

if not API_TOKEN:
    print("Missing CLICKUP_API_TOKEN", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://api.clickup.com/api/v2"
HEADERS = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json",
}

KEY_MAP = {
    "tartalomjegyzek": ["tartalomjegyzék"],
    "bevezetes": ["bevezetés"],
    "konyv_fogalmanak_ujrairasa": ["2. a könyv fogalmának újraírása"],
    "melyik_polcra": ["3. melyik polcra kerüljenek a művészkönyvek"],
    "regi_technikak": ["4. régi technikák, új narratívák"],
    "vizsgalati_szempontok": ["vizsgálati szempontok"],
    "esettanulmany_13": ["13 esettanulmány", "13 esettanulmány"],
    "elemzes_kihivasok": ["elemzés, kihívások azonosítása"],
    "kategorizalasi_szempontok": ["kategorizálási szempontok"],
    "adatmodell_struktura": ["adatmodell struktúra xls", "adatmodell – struktúra", "adatmodell - struktúra"],
    "mezolista_attributumok": ["mezőlista attribútumok xls", "mezőlista / attribútumok"],
    "ontologiai_mapping": ["ontológiai mapping xls", "ontológiai mapping"],
    "terminologiai_szotar": ["terminológiai szótár xls", "terminológiai szótár"],
    "ontologia_fejezet": ["ontológia fejezet"],
    "szotarak_xls": ["szótárak xls", "szótárak"],
    "osszegzes_tavlatok": ["összegzés, távlatok"],
    "zaro_gondolatok": ["záró gondolatok"],
    "koszonetnyilvanitas": ["köszönetnyilvánítás"],
    "bibl_2": ["2. fejezet bibliográfia"],
    "bibl_3": ["3. fejezet bibliográfia"],
    "bibl_4": ["4. fejezet bibliográfia"],
    "bibl_5": ["5. fejezet bibliográfia"],
    "bibl_6": ["6. fejezet bibliográfia"],
    "bibl_7": ["7. fejezet bibliográfia"],
    "keplista": ["képjegyzék", "képlista"],
}

STATUS_ALIASES = {
    "írás": "írás",
    "iras": "írás",
    "fejezet írása": "írás",
    "szerkesztés": "szerkesztés",
    "szerkesztes": "szerkesztés",
    "szerkesztés alatt": "szerkesztés",
    "vizualizálás / ábra": "vizualizálás / ábra",
    "vizualizalas / abra": "vizualizálás / ábra",
    "vizu/ábra": "vizualizálás / ábra",
    "vizu/abra": "vizualizálás / ábra",
    "források ellenőrzése": "források ellenőrzése",
    "forrasok ellenorzese": "források ellenőrzése",
    "témavezetői ellenőrzés": "témavezetői ellenőrzés",
    "temavezeto i ellenorzes": "témavezetői ellenőrzés",
    "temavezeto i ellenőrzés": "témavezetői ellenőrzés",
    "témavezetői ellenorzes": "témavezetői ellenőrzés",
    "kész": "kész",
    "kesz": "kész",
}


def normalize_text(value: str) -> str:
    value = value.lower().strip()
    value = value.replace("–", "-")
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_status(value: str) -> str:
    key = normalize_text(value)
    return STATUS_ALIASES.get(key, value.lower())


def fetch_tasks() -> list[dict]:
    tasks = []
    page = 0
    while True:
      response = requests.get(
          f"{BASE_URL}/list/{LIST_ID}/task",
          headers=HEADERS,
          params={
              "archived": "false",
              "include_subtasks": "true",
              "page": page,
          },
          timeout=30,
      )
      response.raise_for_status()
      data = response.json()
      page_tasks = data.get("tasks", [])
      tasks.extend(page_tasks)
      last_page = data.get("last_page", True)
      if last_page or not page_tasks:
          break
      page += 1
    return tasks


def build_name_status_map(tasks: list[dict]) -> dict[str, str]:
    out = {}
    for task in tasks:
        name = normalize_text(task.get("name", ""))
        status = normalize_status(task.get("status", {}).get("status", ""))
        if name and status:
            out[name] = status
    return out


def main() -> None:
    tasks = fetch_tasks()
    name_status_map = build_name_status_map(tasks)

    data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))

    for key, candidates in KEY_MAP.items():
        for candidate in candidates:
            normalized_candidate = normalize_text(candidate)
            if normalized_candidate in name_status_map:
                if key not in data:
                    data[key] = {}
                data[key]["status"] = name_status_map[normalized_candidate]
                break

    STATUS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Updated status.json from ClickUp")


if __name__ == "__main__":
    main()
