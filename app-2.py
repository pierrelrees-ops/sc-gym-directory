import streamlit as st
import json
import pandas as pd
from datetime import datetime

# ── Page setup ──────────────────────────────────────────────
st.set_page_config(
    page_title="Every Gym on the Sunshine Coast",
    page_icon="🏋️",
    layout="wide"
)

# ── Load gym data ───────────────────────────────────────────
@st.cache_data
def load_data():
    with open("gyms_data.json", "r") as f:
        return json.load(f)

gyms = load_data()

# Build a fast lookup dict by gym ID
gyms_by_id = {g["id"]: g for g in gyms}

# ── Flatten gym types for filtering ─────────────────────────
all_types = sorted(set(t for g in gyms for t in g.get("gymType", [])))
all_suburbs = sorted(set(g["suburb"] for g in gyms if g.get("suburb")))
all_franchises = sorted(set(g["franchiseBrand"] for g in gyms if g.get("franchiseBrand")))

# ── Session state init ───────────────────────────────────────
if "pipeline" not in st.session_state:
    st.session_state.pipeline = {}  # keyed by gym_id (int)

PIPELINE_STAGES = ["Prospect", "Contacted", "Meeting Booked", "Proposal Sent", "Won", "Lost"]

STAGE_COLORS = {
    "Prospect": "#4A90D9",
    "Contacted": "#E8A838",
    "Meeting Booked": "#9B59B6",
    "Proposal Sent": "#1ABC9C",
    "Won": "#2ECC71",
    "Lost": "#E74C3C",
}

# ── Header ──────────────────────────────────────────────────
st.markdown("# 🏋️ Every Gym on the Sunshine Coast")
st.markdown("**132 gyms · Searchable by type, location & owner · Built for fitness industry suppliers**")

# Stats row
total = len(gyms)
independent = sum(1 for g in gyms if g.get("independent"))
franchise = total - independent
suburbs = len(all_suburbs)
pipeline_count = len(st.session_state.pipeline)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Gyms", total)
c2.metric("Independent", independent)
c3.metric("Franchise", franchise)
c4.metric("Suburbs", suburbs)
c5.metric("In Pipeline", pipeline_count)

st.divider()

# ── Main tabs ────────────────────────────────────────────────
tab_dir, tab_pipeline = st.tabs(["📋 Directory", "🎯 Sales Pipeline"])

# ════════════════════════════════════════════════════════════
# TAB 1: DIRECTORY
# ════════════════════════════════════════════════════════════
with tab_dir:
    # ── Filters ─────────────────────────────────────────────
    col_search, col_type, col_ownership = st.columns([2, 2, 1])

    with col_search:
        search = st.text_input("🔍 Search by gym name, suburb, or owner", "")

    with col_type:
        selected_types = st.multiselect("Filter by gym type", all_types)

    with col_ownership:
        ownership = st.radio("Ownership", ["All", "Independent", "Franchise"], horizontal=True)

    # ── Apply filters ────────────────────────────────────────
    filtered = gyms.copy()

    if search:
        s = search.lower()
        filtered = [g for g in filtered if (
            s in g["name"].lower() or
            s in g.get("suburb", "").lower() or
            s in g.get("owner", {}).get("name", "").lower() or
            s in g.get("manager", {}).get("name", "").lower() or
            s in g.get("postcode", "").lower() or
            s in (g.get("franchiseBrand") or "").lower()
        )]

    if selected_types:
        filtered = [g for g in filtered if any(t in g.get("gymType", []) for t in selected_types)]

    if ownership == "Independent":
        filtered = [g for g in filtered if g.get("independent")]
    elif ownership == "Franchise":
        filtered = [g for g in filtered if not g.get("independent")]

    st.markdown(f"**Showing {len(filtered)} of {total} gyms**")

    # ── Map ──────────────────────────────────────────────────
    map_data = pd.DataFrame([
        {
            "lat": g["lat"],
            "lon": g["lng"],
        }
        for g in filtered if g.get("lat") and g.get("lng")
    ])

    if not map_data.empty:
        st.map(map_data, zoom=10)

    # ── Gym Cards ────────────────────────────────────────────
    for g in filtered:
        gym_id = g["id"]
        in_pipeline = gym_id in st.session_state.pipeline

        with st.container():
            # Header row with name and pipeline button
            name = g["name"]
            types = ", ".join(g.get("gymType", []))
            suburb = g.get("suburb", "")
            postcode = g.get("postcode", "")

            # Build badges
            badges = ""
            if g.get("independent"):
                badges += " `INDEPENDENT`"
            else:
                brand = g.get("franchiseBrand", "Franchise")
                badges += f" `{brand}`"
            for t in g.get("gymType", [])[:2]:
                badges += f" `{t}`"

            hdr_col, btn_col = st.columns([5, 1])
            with hdr_col:
                st.markdown(f"### {name}")
                st.markdown(f"{badges}")
                st.markdown(f"📍 {suburb} {postcode}")

            with btn_col:
                if in_pipeline:
                    stage = st.session_state.pipeline[gym_id]["stage"]
                    st.markdown(f"**Pipeline:** `{stage}`")
                    if st.button("Remove from Pipeline", key=f"remove_{gym_id}", type="secondary"):
                        del st.session_state.pipeline[gym_id]
                        st.rerun()
                else:
                    if st.button("➕ Add to Pipeline", key=f"add_{gym_id}", type="primary"):
                        st.session_state.pipeline[gym_id] = {
                            "gym_id": gym_id,
                            "stage": "Prospect",
                            "notes": [],
                            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        }
                        st.rerun()

            # Info columns
            c1, c2, c3 = st.columns(3)

            with c1:
                # Contact
                phone = g.get("phone", "")
                email = g.get("email", "")
                website = g.get("website", "")
                if phone:
                    st.markdown(f"📞 {phone}")
                if email:
                    st.markdown(f"✉️ {email}")
                if website:
                    st.markdown(f"🌐 [{website[:40]}...]({website})" if len(website) > 40 else f"🌐 [{website}]({website})")

            with c2:
                # Social
                insta = g.get("instagram", "")
                fb = g.get("facebook", "")
                gmaps = g.get("googleMapsLink", "")
                rating = g.get("googleRating")
                if insta:
                    st.markdown(f"📸 [Instagram]({insta})" if insta.startswith("http") else f"📸 @{insta}")
                if fb:
                    st.markdown(f"📘 [Facebook]({fb})")
                if gmaps:
                    st.markdown(f"📍 [Google Maps]({gmaps})")
                if rating:
                    st.markdown(f"⭐ {rating}/5 ({g.get('googleReviewCount', '?')} reviews)")

            with c3:
                # People
                owner = g.get("owner", {})
                manager = g.get("manager", {})
                size = g.get("estimatedSize", "")
                date_opened = g.get("dateOpened", "")

                if owner and owner.get("name"):
                    st.markdown(f"👤 **Owner:** {owner['name']}")
                    if owner.get("role"):
                        st.markdown(f"   *{owner['role']}*")
                    if owner.get("linkedin"):
                        st.markdown(f"   [LinkedIn]({owner['linkedin']})")
                if manager and manager.get("name"):
                    st.markdown(f"👤 **Manager:** {manager['name']}")
                    if manager.get("role"):
                        st.markdown(f"   *{manager['role']}*")
                if date_opened:
                    st.markdown(f"📅 Est. {date_opened}")
                if size:
                    st.markdown(f"📏 {size}")

            # About
            about = g.get("aboutGym", "")
            owner_about = (g.get("owner") or {}).get("about", "")
            amenities = g.get("amenities", [])
            equip = g.get("equipmentBrands", [])

            if about or owner_about or amenities or equip:
                with st.expander("About this gym"):
                    if about:
                        st.write(about)
                    if amenities:
                        st.markdown("**Services & Amenities:** " + " · ".join(amenities))
                    if equip:
                        st.markdown("**Equipment brands:** " + " · ".join(equip))
                    if owner_about:
                        st.markdown("---")
                        owner_name = (g.get("owner") or {}).get("name", "Owner")
                        st.markdown(f"**About {owner_name}:** {owner_about}")
                    staff_url = g.get("staffPageUrl", "")
                    if staff_url:
                        st.markdown(f"[View Staff Page →]({staff_url})")

            st.divider()

    # ── Footer ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**Want this for your entire state?** [Contact us](mailto:hello@example.com) for a custom build.")
    st.markdown("*Created with [Perplexity Computer](https://www.perplexity.ai/computer)*")


# ════════════════════════════════════════════════════════════
# TAB 2: SALES PIPELINE
# ════════════════════════════════════════════════════════════
with tab_pipeline:
    pipeline = st.session_state.pipeline

    if not pipeline:
        st.info("No gyms in your pipeline yet. Go to the **Directory** tab and click **➕ Add to Pipeline** on any gym card.")
        st.markdown("### How to use the Sales Pipeline")
        st.markdown("""
1. Browse gyms in the **Directory** tab
2. Click **➕ Add to Pipeline** on any gym
3. Track your outreach progress through stages: **Prospect → Contacted → Meeting Booked → Proposal Sent → Won → Lost**
4. Add notes to track conversations and follow-ups
5. Move gyms between stages as your relationship develops
        """)
    else:
        # ── Pipeline Summary Stats ──────────────────────────
        st.markdown("### Pipeline Overview")

        stage_counts = {stage: 0 for stage in PIPELINE_STAGES}
        for entry in pipeline.values():
            stage_counts[entry["stage"]] = stage_counts.get(entry["stage"], 0) + 1

        stat_cols = st.columns(len(PIPELINE_STAGES) + 1)
        stat_cols[0].metric("Total in Pipeline", len(pipeline))
        for i, stage in enumerate(PIPELINE_STAGES):
            stat_cols[i + 1].metric(stage, stage_counts[stage])

        st.divider()

        # ── Add new gym to pipeline (search widget) ─────────
        with st.expander("➕ Add another gym to pipeline"):
            # Show gyms not already in pipeline
            available = [g for g in gyms if g["id"] not in pipeline]
            if available:
                gym_options = {f"{g['name']} ({g.get('suburb', '')})": g["id"] for g in available}
                selected_label = st.selectbox("Select gym to add", list(gym_options.keys()))
                if st.button("Add to Pipeline", key="add_search"):
                    selected_id = gym_options[selected_label]
                    st.session_state.pipeline[selected_id] = {
                        "gym_id": selected_id,
                        "stage": "Prospect",
                        "notes": [],
                        "date_added": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                    st.rerun()
            else:
                st.write("All gyms are already in your pipeline.")

        # ── Kanban Board ────────────────────────────────────
        st.markdown("### Kanban Board")

        # Render one column per stage
        stage_cols = st.columns(len(PIPELINE_STAGES))

        for col_idx, stage in enumerate(PIPELINE_STAGES):
            with stage_cols[col_idx]:
                color = STAGE_COLORS[stage]
                stage_gyms = [
                    (gid, entry)
                    for gid, entry in pipeline.items()
                    if entry["stage"] == stage
                ]

                st.markdown(
                    f"""<div style="background:{color}22; border-left: 4px solid {color}; 
                    padding: 8px 12px; border-radius: 4px; margin-bottom: 12px;">
                    <strong style="color:{color};">{stage}</strong>
                    <span style="float:right; background:{color}; color:white; 
                    border-radius:50%; width:22px; height:22px; display:inline-flex;
                    align-items:center; justify-content:center; font-size:12px;">
                    {len(stage_gyms)}</span></div>""",
                    unsafe_allow_html=True,
                )

                for gym_id, entry in stage_gyms:
                    gym = gyms_by_id.get(gym_id, {})
                    gym_name = gym.get("name", f"Gym #{gym_id}")
                    suburb = gym.get("suburb", "")
                    owner_name = (gym.get("owner") or {}).get("name", "")
                    phone = gym.get("phone", "")
                    email = gym.get("email", "")
                    date_added = entry.get("date_added", "")
                    notes = entry.get("notes", [])

                    with st.container():
                        st.markdown(
                            f"""<div style="background:#1e1e2e; border:1px solid #333; 
                            border-radius:8px; padding:12px; margin-bottom:10px;">
                            <strong>{gym_name}</strong><br>
                            <small style="color:#888;">📍 {suburb}</small>
                            </div>""",
                            unsafe_allow_html=True,
                        )

                        if owner_name:
                            st.markdown(f"👤 {owner_name}")
                        if phone:
                            st.markdown(f"📞 {phone}")
                        if email:
                            st.markdown(f"✉️ {email}")

                        st.markdown(f"<small style='color:#666;'>Added: {date_added}</small>", unsafe_allow_html=True)

                        # Latest note preview
                        if notes:
                            last_note = notes[-1]
                            st.markdown(
                                f"""<div style="background:#2a2a3e; border-radius:4px; 
                                padding:6px 8px; margin:6px 0; font-size:12px; color:#aaa;">
                                💬 {last_note['text'][:80]}{'...' if len(last_note['text']) > 80 else ''}
                                <br><small>{last_note['timestamp']}</small></div>""",
                                unsafe_allow_html=True,
                            )

                        # Stage move dropdown
                        new_stage = st.selectbox(
                            "Move to stage",
                            PIPELINE_STAGES,
                            index=PIPELINE_STAGES.index(stage),
                            key=f"stage_{gym_id}",
                            label_visibility="collapsed",
                        )
                        if new_stage != stage:
                            st.session_state.pipeline[gym_id]["stage"] = new_stage
                            st.rerun()

                        # Expand for notes & remove
                        with st.expander("Notes & Actions", expanded=False):
                            # Show all notes
                            if notes:
                                st.markdown("**Notes:**")
                                for note in reversed(notes):
                                    st.markdown(
                                        f"""<div style="background:#1a1a2e; border-radius:4px; 
                                        padding:6px 8px; margin:4px 0; font-size:12px;">
                                        {note['text']}<br>
                                        <small style="color:#666;">{note['timestamp']}</small>
                                        </div>""",
                                        unsafe_allow_html=True,
                                    )
                            else:
                                st.markdown("*No notes yet.*")

                            # Add note
                            new_note = st.text_area(
                                "Add a note",
                                placeholder="e.g. Called Monday, spoke to owner, following up Thursday",
                                key=f"note_input_{gym_id}",
                                height=70,
                            )
                            if st.button("Save Note", key=f"save_note_{gym_id}"):
                                if new_note.strip():
                                    st.session_state.pipeline[gym_id]["notes"].append({
                                        "text": new_note.strip(),
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    })
                                    st.rerun()

                            # Remove from pipeline
                            st.markdown("---")
                            if st.button("🗑️ Remove from Pipeline", key=f"remove_kanban_{gym_id}", type="secondary"):
                                del st.session_state.pipeline[gym_id]
                                st.rerun()

        st.divider()

        # ── Pipeline Table View ──────────────────────────────
        st.markdown("### Pipeline Table")
        table_rows = []
        for gym_id, entry in pipeline.items():
            gym = gyms_by_id.get(gym_id, {})
            notes = entry.get("notes", [])
            last_note = notes[-1]["text"] if notes else ""
            table_rows.append({
                "Gym": gym.get("name", f"Gym #{gym_id}"),
                "Suburb": gym.get("suburb", ""),
                "Stage": entry["stage"],
                "Owner": (gym.get("owner") or {}).get("name", ""),
                "Phone": gym.get("phone", ""),
                "Email": gym.get("email", ""),
                "Date Added": entry.get("date_added", ""),
                "Notes": f"{len(notes)} note(s)",
                "Latest Note": last_note[:60] + ("..." if len(last_note) > 60 else ""),
            })

        if table_rows:
            df = pd.DataFrame(table_rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

        # ── Export pipeline ──────────────────────────────────
        st.markdown("### Export Pipeline")
        if table_rows:
            csv_data = pd.DataFrame(table_rows).to_csv(index=False)
            st.download_button(
                label="⬇️ Download Pipeline as CSV",
                data=csv_data,
                file_name=f"pipeline_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
