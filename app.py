import re
import sqlite3

import pandas as pd
import streamlit as st

# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================
st.set_page_config(
    page_title="SQL in Plain English",
    page_icon="✨",
    layout="wide"
)

# ==================================================
# 2. COLORFUL UI
# ==================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef2ff 0%, #fdf2f8 100%);
}
.main-title {
    text-align: center;
    color: #4f46e5;
    font-size: 42px;
    font-weight: 800;
}
.subtitle {
    text-align: center;
    color: #475569;
    font-size: 17px;
}
div.stButton > button {
    background: linear-gradient(90deg, #4f46e5, #9333ea);
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: 600;
    padding: 9px 16px;
}
div.stButton > button:hover {
    color: white;
    border: 1px solid #4f46e5;
}
[data-testid="stDataFrame"] {
    border: 1px solid #c7d2fe;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# 3. SAMPLE STUDENT DATA
# Replace this data with your actual dataset later.
# ==================================================
students = pd.DataFrame({
    "name": [
        "Sahana", "Ananya", "Priya", "Rahul",
        "Sneha", "Arjun", "Kavya", "Rohan"
    ],
    "marks": [95, 82, 76, 68, 91, 55, 88, 79],
    "department": [
        "AIML", "CSE", "AIML", "ECE",
        "AIML", "CSE", "AIML", "ECE"
    ]
})

# ==================================================
# 4. CREATE SQLITE DATABASE
# ==================================================
@st.cache_resource
def create_database():
    conn = sqlite3.connect(
        ":memory:",
        check_same_thread=False
    )
    students.to_sql(
        "students",
        conn,
        index=False,
        if_exists="replace"
    )
    return conn

connection = create_database()

# ==================================================
# 5. CONVERT ENGLISH TO SQL
# ==================================================
def convert_to_sql(question):
    q = question.lower().strip()
    q = re.sub(r"[?!.,]+", " ", q)
    q = re.sub(r"\s+", " ", q).strip()

    if not q:
        return None, None, "Please enter a question."

    # Count students
    if (
        re.search(r"\b(how many|count|number of)\b", q)
        and re.search(r"\bstudents?\b", q)
    ):
        return (
            "SELECT COUNT(*) AS total_students FROM students",
            (),
            None
        )

    # Highest marks
    if (
        re.search(r"\b(highest|maximum|max)\b", q)
        and re.search(r"\b(marks?|scores?)\b", q)
    ):
        return (
            """SELECT * FROM students
               WHERE marks = (
                   SELECT MAX(marks) FROM students
               )""",
            (),
            None
        )

    # Above a specified mark
    match = re.search(
        r"\b(?:above|greater than|more than|over|higher than)"
        r"\s+(\d+(?:\.\d+)?)\b",
        q
    )
    if match and re.search(r"\b(marks?|scores?)\b", q):
        value = float(match.group(1))
        return (
            "SELECT * FROM students WHERE marks > ?",
            (value,),
            None
        )

    # Below a specified mark
    match = re.search(
        r"\b(?:below|less than|under|lower than)"
        r"\s+(\d+(?:\.\d+)?)\b",
        q
    )
    if match and re.search(r"\b(marks?|scores?)\b", q):
        value = float(match.group(1))
        return (
            "SELECT * FROM students WHERE marks < ?",
            (value,),
            None
        )

    # Sort marks descending
    if (
        re.search(r"\b(sort|order|arrange|rank)\b", q)
        and re.search(r"\b(marks?|scores?)\b", q)
        and re.search(
            r"\b(descending|highest first|high to low)\b", q
        )
    ) or re.search(r"\bsort by marks descending\b", q):
        return (
            "SELECT * FROM students ORDER BY marks DESC",
            (),
            None
        )

    # Sort marks ascending
    if (
        re.search(r"\b(sort|order|arrange)\b", q)
        and re.search(r"\b(marks?|scores?)\b", q)
        and re.search(
            r"\b(ascending|lowest first|low to high)\b", q
        )
    ):
        return (
            "SELECT * FROM students ORDER BY marks ASC",
            (),
            None
        )

    # Show student names only
    if (
        re.search(r"\b(names?|name)\b", q)
        and re.search(
            r"\b(show|display|list|get|find)\b", q
        )
        and re.search(r"\bstudents?\b", q)
    ):
        return (
            "SELECT name FROM students",
            (),
            None
        )

    # Filter by department
    dept_match = re.search(
        r"\b(?:from|in|belonging to)\s+"
        r"(?:the\s+)?([a-z][a-z0-9 &-]*?)\s+department\b",
        q
    )
    if dept_match:
        department = dept_match.group(1).strip().upper()

        return (
            """SELECT * FROM students
               WHERE UPPER(department) = ?""",
            (department,),
            None
        )

    # Show all students
    if (
        re.search(r"\b(show|display|list|get|view)\b", q)
        and re.search(r"\ball\b", q)
        and re.search(r"\bstudents?\b", q)
    ):
        return (
            "SELECT * FROM students",
            (),
            None
        )

    return (
        None,
        None,
        "I couldn't understand that question. "
        "Please try one of the examples below."
    )

# ==================================================
# 6. PAGE HEADER
# ==================================================
st.markdown(
    '<div class="main-title">✨ SQL in Plain English</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">'
    'Convert everyday English questions into SQL queries '
    'and view the results instantly.'
    '</div>',
    unsafe_allow_html=True
)

st.write("")
st.write("### 💬 Ask Your Question")

# IMPORTANT:
# Set the input value BEFORE creating the text_input widget.
if "question" not in st.session_state:
    st.session_state["question"] = ""

if "selected_example" in st.session_state:
    st.session_state["question"] = st.session_state.pop(
        "selected_example"
    )

question = st.text_input(
    "Type your question",
    placeholder="e.g. Show students who scored above 80 marks",
    key="question"
)

# ==================================================
# 7. CONVERT BUTTON AND DISPLAY RESULTS
# ==================================================
if st.button("✨ Convert to SQL", key="convert_button"):
    sql, params, error = convert_to_sql(question)

    if error:
        st.warning(error)

    else:
        st.success("Question understood successfully!")

        st.markdown("### 🧾 Generated SQL Query")
        st.code(sql, language="sql")

        try:
            result = pd.read_sql_query(
                sql,
                connection,
                params=params
            )

            st.markdown("### 📊 Query Result")

            if result.empty:
                st.info("No matching students found.")

            else:
                if "total_students" in result.columns:
                    st.metric(
                        "Total Students",
                        int(result.iloc[0]["total_students"])
                    )
                else:
                    st.caption(
                        f"Found {len(result)} result(s)."
                    )

                st.dataframe(
                    result,
                    use_container_width=True,
                    hide_index=True
                )

        except Exception as exc:
            st.error(f"SQL execution error: {exc}")

# ==================================================
# 8. EXAMPLE QUESTIONS
# ==================================================
st.divider()
st.markdown("### 💡 Try These Questions")

examples = [
    "Show all students",
    "Show students who scored above 80 marks",
    "Show students with marks below 80",
    "How many students are there?",
    "Show the highest marks",
    "Show names of students",
    "Show students from AIML department",
    "Sort by marks descending"
]

# Each example has a unique button key.
# Selection is stored separately and applied before
# the text input is created on the next rerun.
for index, example in enumerate(examples):
    if st.button(
        f"➡️ {example}",
        key=f"example_{index}",
        use_container_width=True
    ):
        st.session_state["selected_example"] = example
        st.rerun()

# ==================================================
# 9. FOOTER
# ==================================================
st.divider()
st.caption(
    "Mini Project | Python • Pandas • SQLite • Streamlit"
)