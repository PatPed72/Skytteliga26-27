# ============================================================
# IFK TUMBA - SKYTTELIGA 26/27
# Streamlit-version för GitHub / Streamlit Community Cloud
# ============================================================

import json
from collections import defaultdict

import requests
import streamlit as st


# ------------------------------------------------------------
# 1. KONFIGURATION
# ------------------------------------------------------------

st.set_page_config(
    page_title="IFK Tumba - Skytteliga 26/27",
    page_icon="🏆",
    layout="centered",
)

# Registreringarna sparas i JSONBin.io.
# Lägg dessa värden i Streamlit Community Cloud -> App settings -> Secrets:
# ADMIN_PASSWORD = "välj-ett-starkt-lösenord"
# JSONBIN_API_KEY = "din_jsonbin_master_key"
# JSONBIN_BIN_ID = "id_for_din_jsonbin"

try:
    ADMIN_LOSENORD = st.secrets["ADMIN_PASSWORD"]
    JSONBIN_API_KEY = st.secrets["JSONBIN_API_KEY"]
    JSONBIN_BIN_ID = st.secrets["JSONBIN_BIN_ID"]
except Exception:
    ADMIN_LOSENORD = ""
    JSONBIN_API_KEY = ""
    JSONBIN_BIN_ID = ""

JSONBIN_API = "https://api.jsonbin.io/v3/b"


def jsonbin_headers():
    if not JSONBIN_API_KEY or not JSONBIN_BIN_ID:
        raise RuntimeError(
            "JSONBin är inte konfigurerat. Lägg till JSONBIN_API_KEY och "
            "JSONBIN_BIN_ID i Streamlit Cloud -> App settings -> Secrets."
        )
    return {
        "X-Master-Key": JSONBIN_API_KEY,
        "Content-Type": "application/json",
    }


def jsonbin_data_url():
    return f"{JSONBIN_API}/{JSONBIN_BIN_ID}"


# ------------------------------------------------------------
# 2. SPELARE
# ------------------------------------------------------------

SPELARE = [
    "Arvid", "Charlie", "Ebrahim", "George", "Ivar",
    "Jimmy", "Leo", "Linus", "Luca", "Mattias",
    "Michael", "Noel", "Olle", "Sebastian",
    "Jayden", "Timur", "Victor", "Widar",
]


# ------------------------------------------------------------
# 3. MATCHER
# ------------------------------------------------------------

MATCHER_SERIE = [
    "IFK Tumba HK 1 - Spånga HK",
    "Hammarby IF HF 1 - IFK Tumba HK 1",
    "IFK Tumba HK 1 - Gustavsbergs IF HK",
    "Skuru IK 1 - IFK Tumba HK 1",
    "IFK Tumba HK 1 - Täby HBK 1",
    "Huddinge HK - IFK Tumba HK 1",
    "IFK Tumba HK 1 - Sannadals SK",
    "Tyresö Handboll 1 - IFK Tumba HK 1",
    "Spånga HK - IFK Tumba HK 1",
    "IFK Tumba HK 1 - Hammarby IF HF 1",
    "Gustavsbergs IF HK - IFK Tumba HK 1",
    "IFK Tumba HK 1 - Skuru IK 1",
    "Täby HBK 1 - IFK Tumba HK 1",
    "IFK Tumba HK 1 - Huddinge HK",
    "Sannadals SK - IFK Tumba HK 1",
    "IFK Tumba HK 1 - Tyresö Handboll 1",

    "IFK Tumba HK 2 - Tyresö Handboll 2",
    "Skogås HK - IFK Tumba HK 2",
    "IFK Tumba HK 2 - Lidingö SK 2",
    "Skuru IK 2 - IFK Tumba HK 2",
    "IFK Tumba HK 2 - IK Bolton",
    "Huddinge HK 2 - IFK Tumba HK 2",
    "Årsta AIK HF 1 - IFK Tumba HK 2",
    "Tyresö Handboll 2 - IFK Tumba HK 2",
    "IFK Tumba HK 2 - Skogås HK",
    "Lidingö SK 2 - IFK Tumba HK 2",
    "IFK Tumba HK 2 - Skuru IK 2",
    "IK Bolton - IFK Tumba HK 2",
    "IFK Tumba HK 2 - Huddinge HK 2",
    "IFK Tumba HK 2 - Årsta AIK HF 1",
]

MATCHER_OB = [
    "IFK Tumba HK - Tyresö Handboll",
    "Skogås HK - IFK Tumba HK",
    "Huddinge HK - IFK Tumba HK",
]

MATCHER = MATCHER_SERIE + MATCHER_OB

MATCHTYPER = [
    "Seriespel",
    "ÖB",
    "Hellton",
    "Lunda",
]


# ------------------------------------------------------------
# 4. DATA
# ------------------------------------------------------------

def ladda_data():
    """Läser registreringar och egna matcher från JSONBin."""
    response = requests.get(
        f"{jsonbin_data_url()}/latest",
        headers=jsonbin_headers(),
        timeout=20,
    )

    if not response.ok:
        raise RuntimeError(
            f"Kunde inte läsa JSONBin (HTTP {response.status_code})."
        )

    try:
        record = response.json()["record"]
    except (KeyError, ValueError, TypeError) as exc:
        raise RuntimeError("JSONBin-svaret kunde inte läsas.") from exc

    if isinstance(record, dict):
        st.session_state["egna_matcher"] = record.get("matches", [])
        data = record.get("data", [])
    else:
        st.session_state["egna_matcher"] = []
        data = record

    if not isinstance(data, list):
        raise RuntimeError("Registreringarna har fel format.")

    if not isinstance(st.session_state["egna_matcher"], list):
        st.session_state["egna_matcher"] = []

    return data


def spara_data(data):
    """Sparar registreringar och egna matcher i JSONBin."""
    response = requests.put(
        jsonbin_data_url(),
        headers=jsonbin_headers(),
        json={
            "data": data,
            "matches": st.session_state.get("egna_matcher", []),
        },
        timeout=20,
    )

    if not response.ok:
        raise RuntimeError(
            f"Kunde inte spara JSONBin (HTTP {response.status_code})."
        )


def hamta_registreringar():
    if "registreringar" not in st.session_state:
        st.session_state.registreringar = ladda_data()

    return st.session_state.registreringar


try:
    registreringar = hamta_registreringar()
except Exception as exc:
    st.error(f"Kunde inte läsa sparade registreringar: {exc}")
    st.stop()


# ------------------------------------------------------------
# 5. HJÄLPFUNKTIONER
# ------------------------------------------------------------

def berakna_skytteliga():
    total = defaultdict(int)
    per_matchtyp = defaultdict(lambda: defaultdict(int))

    antal_matcher = defaultdict(set)
    antal_matcher_per_matchtyp = defaultdict(lambda: defaultdict(set))

    for r in registreringar:
        try:
            spelare = r["spelare"]
            mal = int(r["mal"])
            match = r["match"]
            matchtyp = r["matchtyp"]
        except (KeyError, TypeError, ValueError):
            continue

        total[spelare] += mal
        per_matchtyp[matchtyp][spelare] += mal

        antal_matcher[spelare].add(match)
        antal_matcher_per_matchtyp[matchtyp][spelare].add(match)

    return (
        total,
        per_matchtyp,
        antal_matcher,
        antal_matcher_per_matchtyp,
    )


def visa_tabell(rows, kolumner):
    """Visar en enkel, responsiv tabell med Streamlit."""
    if not rows:
        st.info("Inga registreringar ännu.")
        return

    st.dataframe(
        rows,
        column_config=kolumner,
        hide_index=True,
        use_container_width=True,
    )


# ------------------------------------------------------------
# 6. STATISTIK
# ------------------------------------------------------------

def visa_skytteliga():
    (
        total,
        _,
        antal_matcher,
        _,
    ) = berakna_skytteliga()

    skyttar = [
        (spelare, mal)
        for spelare, mal in total.items()
        if mal > 0
    ]

    skyttar.sort(key=lambda x: (-x[1], x[0]))

    rows = []

    for placering, (spelare, mal) in enumerate(skyttar, start=1):
        matcher = len(antal_matcher[spelare])
        snitt = mal / matcher if matcher else 0

        rows.append(
            {
                "Plats": placering,
                "Spelare": spelare,
                "Mål": mal,
                "Snitt mål/match": round(snitt, 1),
            }
        )

    visa_tabell(
        rows,
        {
            "Plats": st.column_config.NumberColumn(width="small", alignment="left"),
            "Spelare": st.column_config.TextColumn(width="medium", alignment="left"),
            "Mål": st.column_config.NumberColumn(width="small", alignment="left"),
            "Snitt mål/match": st.column_config.NumberColumn(
                format="%.1f",
                width="medium",
                alignment="left",
            ),
        },
    )


def visa_statistik_per_matchtyp():
    (
        _,
        per_matchtyp,
        _,
        antal_matcher_per_matchtyp,
    ) = berakna_skytteliga()

    for matchtyp in MATCHTYPER:
        st.subheader(matchtyp)

        spelare_data = [
            (spelare, mal)
            for spelare, mal in per_matchtyp[matchtyp].items()
            if mal > 0
        ]

        spelare_data.sort(key=lambda x: (-x[1], x[0]))

        rows = []

        for spelare, mal in spelare_data:
            matcher = len(
                antal_matcher_per_matchtyp[matchtyp][spelare]
            )
            snitt = mal / matcher if matcher else 0

            rows.append(
                {
                    "Spelare": spelare,
                    "Mål": mal,
                    "Snitt mål/match": round(snitt, 1),
                }
            )

        visa_tabell(
            rows,
            {
                "Spelare": st.column_config.TextColumn(width="medium", alignment="left"),
                "Mål": st.column_config.NumberColumn(width="small", alignment="left"),
                "Snitt mål/match": st.column_config.NumberColumn(
                    format="%.1f",
                    width="medium",
                    alignment="left",
                ),
            },
        )


# ------------------------------------------------------------
# 7. LÖSENORD
# ------------------------------------------------------------

def kontrollera_losenord():
    if st.session_state.get("admin_inloggad", False):
        return True

    st.subheader("🔐 Registrering")
    st.write(
        "Den här fliken är endast till för att registrera mål "
        "och administrera registreringarna."
    )

    losenord = st.text_input(
        "Lösenord",
        type="password",
        key="admin_losenord",
    )

    if st.button("Logga in", type="primary"):
        if losenord == ADMIN_LOSENORD:
            st.session_state.admin_inloggad = True
            st.rerun()
        else:
            st.error("Fel lösenord.")

    return False


# ------------------------------------------------------------
# 8. REGISTRERING
# ------------------------------------------------------------

def registreringsflik():
    if not kontrollera_losenord():
        return

    st.success("Inloggad som administratör.")

    if st.button("Logga ut"):
        st.session_state.admin_inloggad = False
        st.rerun()

    st.divider()

    # --- Formulär 1: Lägg till match ---
    st.subheader("➕ Lägg till match")

    with st.form("lagg_till_match_form"):
        ny_match = st.text_input(
            "Matchnamn",
            placeholder="Exempel: IFK Tumba HK - Ny motståndare",
        )
        lagg_till_match = st.form_submit_button("Spara match")

    if lagg_till_match:
        matchnamn = ny_match.strip()
        alla_matcher = MATCHER + st.session_state.get("egna_matcher", [])

        if not matchnamn:
            st.error("Skriv ett matchnamn först.")
        elif matchnamn in alla_matcher:
            st.warning("Den matchen finns redan.")
        else:
            egna = st.session_state.setdefault("egna_matcher", [])
            egna.append(matchnamn)

            try:
                spara_data(registreringar)
            except Exception as exc:
                egna.pop()
                st.error(f"Kunde inte spara matchen: {exc}")
            else:
                st.success(f"Matchen {matchnamn} har sparats!")
                st.rerun()

    st.divider()

    # --- Formulär 2: Registrera mål ---
    st.subheader("➕ Registrera mål")

    with st.form("registrering_form"):
        spelare = st.selectbox(
            "Spelare",
            SPELARE,
        )

        mal = st.selectbox(
            "Antal mål",
            list(range(0, 31)),
            index=0,
        )

        alla_matcher = MATCHER + st.session_state.get("egna_matcher", [])

        match = st.selectbox(
            "Match",
            alla_matcher,
        )

        matchtyp = st.selectbox(
            "Matchtyp",
            MATCHTYPER,
        )

        skickad = st.form_submit_button(
            "💾 Spara registrering",
            type="primary",
        )

    if skickad:
        ny = {
            "spelare": spelare,
            "mal": int(mal),
            "match": match,
            "matchtyp": matchtyp,
        }

        registreringar.append(ny)
        try:
            spara_data(registreringar)
        except Exception as exc:
            registreringar.pop()
            st.error(f"Registreringen kunde inte sparas till JSONBin: {exc}")
        else:
            st.success(
                f"{spelare} gjorde {mal} mål i matchen "
                f"'{match}'. Matchtyp: {matchtyp}. Registreringen är sparad i JSONBin."
            )

    st.divider()

    # --- Visning & Hantering av registreringar ---
    st.subheader("📋 Registrerade matcher")

    if not registreringar:
        st.info("Inga registreringar ännu.")
    else:
        rows = []

        for r in reversed(registreringar):
            rows.append(
                {
                    "Spelare": r["spelare"],
                    "Mål": r["mal"],
                    "Match": r["match"],
                    "Matchtyp": r["matchtyp"],
                }
            )

        visa_tabell(
            rows,
            {
                "Spelare": st.column_config.TextColumn(width="medium", alignment="left"),
                "Mål": st.column_config.NumberColumn(width="small", alignment="left"),
                "Match": st.column_config.TextColumn(width="large", alignment="left"),
                "Matchtyp": st.column_config.TextColumn(width="medium", alignment="left"),
            },
        )

    st.divider()

    st.subheader("🗑️ Ta bort senaste registreringen")

    if not registreringar:
        st.caption("Det finns inga registreringar att ta bort.")
    else:
        senaste = registreringar[-1]

        st.write(
            f"Senaste: **{senaste['spelare']}** – "
            f"{senaste['mal']} mål – "
            f"{senaste['match']} – "
            f"{senaste['matchtyp']}"
        )

        if st.button("Ta bort senaste", type="secondary"):
            borttagen = registreringar.pop()
            try:
                spara_data(registreringar)
            except Exception as exc:
                registreringar.append(borttagen)
                st.error(f"Registreringen kunde inte tas bort från JSONBin: {exc}")
            else:
                st.warning(
                    f"Registreringen för {borttagen['spelare']} "
                    f"togs bort och ändringen sparades i JSONBin."
                )
                st.rerun()


# ------------------------------------------------------------
# 9. HUVUDAPP
# ------------------------------------------------------------

st.title("🏆 IFK Tumba P13 - Skytteliga 26/27")

st.caption(
    "Statistiken är öppen för alla. Registrering och "
    "administration kräver lösenord."
)

flik_statistik, flik_registrering = st.tabs(
    [
        "📊 Skytteliga",
        "🔐 Registrera mål",
    ]
)

with flik_statistik:
    st.header("Skytteliga")

    (
        total,
        _,
        _,
        _,
    ) = berakna_skytteliga()

    totalt_mal = sum(total.values())

    st.metric(
        "Totalt registrerade mål",
        totalt_mal,
    )

    st.subheader("🥇 Skytteliga totalt")
    visa_skytteliga()

    st.subheader("📊 Statistik per matchtyp")
    visa_statistik_per_matchtyp()

with flik_registrering:
    registreringsflik()
