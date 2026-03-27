import streamlit as st
import json
import pandas as pd

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

# ── Flatten gym types for filtering ─────────────────────────
all_types = sorted(set(t for g in gyms for t in g.get("gymType", [])))
all_suburbs = sorted(set(g["suburb"] for g in gyms if g.get("suburb")))
all_franchises = sorted(set(g["franchiseBrand"] for g in gyms if g.get("franchiseBrand")))

# ── Header ──────────────────────────────────────────────────
st.markdown("# 🏋️ Every Gym on the Sunshine Coast")
st.markdown("**132 gyms · Searchable by type, location & owner · Built for fitness industry suppliers**")

# Stats row
total = len(gyms)
independent = sum(1 for g in gyms if g.get("independent"))
franchise = total - independent
suburbs = len(all_suburbs)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Gyms", total)
c2.metric("Independent", independent)
c3.metric("Franchise", franchise)
c4.metric("Suburbs", suburbs)

st.divider()

# ── Filters ─────────────────────────────────────────────────
col_search, col_type, col_ownership = st.columns([2, 2, 1])

with col_search:
    search = st.text_input("🔍 Search by gym name, suburb, or owner", "")

with col_type:
    selected_types = st.multiselect("Filter by gym type", all_types)

with col_ownership:
    ownership = st.radio("Ownership", ["All", "Independent", "Franchise"], horizontal=True)

# ── Apply filters ───────────────────────────────────────────
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

# ── Map ─────────────────────────────────────────────────────
map_data = pd.DataFrame([
    {
        "lat": g["lat"],
        "lon": g["lng"],
    }
    for g in filtered if g.get("lat") and g.get("lng")
])

if not map_data.empty:
    st.map(map_data, zoom=10)

# ── Gym Cards ───────────────────────────────────────────────
for g in filtered:
    with st.container():
        # Header row
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

        st.markdown(f"### {name}")
        st.markdown(f"{badges}")
        st.markdown(f"📍 {suburb} {postcode}")

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
            if insta:
                st.markdown(f"📸 [{insta}]({insta})" if insta.startswith("http") else f"📸 @{insta}")
            if fb:
                st.markdown(f"📘 [Facebook]({fb})")
            if gmaps:
                st.markdown(f"📍 [Google Maps]({gmaps})")

        with c3:
            # People
            owner = g.get("owner", {})
            manager = g.get("manager", {})
            rating = g.get("googleRating")
            size = g.get("estimatedSize", "")

            if owner.get("name"):
                st.markdown(f"👤 **Owner:** {owner['name']}")
                if owner.get("linkedin"):
                    st.markdown(f"[LinkedIn]({owner['linkedin']})")
            if manager.get("name"):
                st.markdown(f"👤 **Manager:** {manager['name']}")
            if rating:
                st.markdown(f"⭐ {rating}/5 ({g.get('googleReviewCount', '?')} reviews)")
            if size:
                st.markdown(f"📏 {size}")

        # About
        about = g.get("aboutGym", "")
        if about:
            with st.expander("About this gym"):
                st.write(about)
                amenities = g.get("amenities", [])
                if amenities:
                    st.markdown("**Services:** " + " · ".join(amenities))
                equip = g.get("equipmentBrands", [])
                if equip:
                    st.markdown("**Equipment brands:** " + " · ".join(equip))
                staff_url = g.get("staffPageUrl", "")
                if staff_url:
                    st.markdown(f"[View Staff Page →]({staff_url})")

        st.divider()

# ── Footer ──────────────────────────────────────────────────
st.markdown("---")
st.markdown("**Want this for your entire state?** [Contact us](mailto:hello@example.com) for a custom build.")
st.markdown("*Created with [Perplexity Computer](https://www.perplexity.ai/computer)*")
