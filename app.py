
import re
import streamlit as st
import pandas as pd
from pandas.errors import EmptyDataError

st.set_page_config(
    page_title="SQL in Plain English",
    page_icon="📊",
    layout="wide"
)

# ---------- COLORFUL UI ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef2ff, #fdf2f8);
}
h1 {
    color: #4f46e5;
}
div.stButton > button {
    background-color: #4f46e5;
    color: white;
    border-radius: 10px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 SQL in Plain English")
st.write("Ask questions about your data using everyday English.")

# ---------- SAMPLE DATA ----------
sample_data = pd.DataFrame({
    "name": ["Rahul", "Priya", "Amit", "Sneha"],
    "marks": [85, 92, 78, 95],
    "department": ["CSE", "AIML", "CSE", "AIML"]
})

# ---------- CSV UPLOAD ----------
uploaded_file = st.file_uploader(
    "📁 Upload your CSV file",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        if uploaded_file.size == 0:
            st.warning("The CSV is empty. Using sample data.")
            result = sample_data.copy()
        else:
            result = pd.read_csv(uploaded_file)
            if result.empty or len(result.columns) == 0:
                st.warning("No usable data found. Using sample data.")
                result = sample_data.copy()
    except EmptyDataError:
        st.warning("The CSV has no column headers. Using sample data.")
        result = sample_data.copy()
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        result = sample_data.copy()
else:
    result = sample_data.copy()

if len(result.columns) == 0:
    st.error("No columns are available.")
    st.stop()

st.subheader("📋 Dataset Preview")
st.dataframe(result, use_container_width=True)

# ---------- ENGLISH TO SQL ----------
def english_to_sql(question, df):
    q = question.lower().strip()
    q = re.sub(r"[?!.,]+$", "", q)
    q = re.sub(r"\s+", " ", q)

    # Match columns without depending on capitalization
    columns = {str(c).lower(): c for c in df.columns}

    def find_column(*names):
        for name in names:
            if name in columns:
                return columns[name]
        return None

    name_col = find_column("name", "student_name", "student name")
    marks_col = find_column("marks", "mark", "score", "scores")
    dept_col = find_column(
        "department", "dept", "branch"
    )

    table = "students"

    # Count records
    if any(x in q for x in [
        "how many students", "count students",
        "total students", "number of students",
        "count all", "total records", "how many records"
    ]):
        return f"SELECT COUNT(*) FROM {table};", "count"

    # Find highest marks
    if any(x in q for x in [
        "highest marks", "top scorer",
        "top student", "maximum marks",
        "highest score", "best marks"
    ]):
        if marks_col is None:
            return None, "Your data needs a marks or score column."
        return (
            f"SELECT * FROM {table} ORDER BY "
            f'"{marks_col}" DESC LIMIT 1;',
            "highest"
        )

    # Find lowest marks
    if any(x in q for x in [
        "lowest marks", "lowest score",
        "minimum marks", "minimum score"
    ]):
        if marks_col is None:
            return None, "Your data needs a marks or score column."
        return (
            f'SELECT * FROM {table} ORDER BY "{marks_col}" ASC LIMIT 1;',
            "lowest"
        )

    # Filter by marks or scores
    if marks_col and any(x in q for x in [
        "mark", "score", "scored", "marks", "scoring"
    ]):
        match = re.search(
            r"(?:greater than|more than|above|over|"
            r"less than|below|under|equal to|at least|"
            r"at most)\s+(\d+(?:\.\d+)?)",
            q
        )

        if match:
            number = float(match.group(1))
            phrase = match.group(0)

            if phrase.startswith(("greater", "more", "above", "over")):
                operator = ">"
                mask = pd.to_numeric(
                    df[marks_col], errors="coerce"
                ) > number
            elif phrase.startswith(("less", "below", "under")):
                operator = "<"
                mask = pd.to_numeric(
                    df[marks_col], errors="coerce"
                ) < number
            elif phrase.startswith("equal"):
                operator = "="
                mask = pd.to_numeric(
                    df[marks_col], errors="coerce"
                ) == number
            elif phrase.startswith("at least"):
                operator = ">="
                mask = pd.to_numeric(
                    df[marks_col], errors="coerce"
                ) >= number
            else:
                operator = "<="
                mask = pd.to_numeric(
                    df[marks_col], errors="coerce"
                ) <= number

            sql = (
                f'SELECT * FROM {table} WHERE '
                f'"{marks_col}" {operator} {number:g};'
            )
            return sql, df[mask]

    # Filter by department or branch
    if dept_col and any(x in q for x in [
        "department", "branch", "dept"
    ]):
        for value in df[dept_col].dropna().unique():
            value = str(value)
            if value.lower() in q:
                safe_value = value.replace("'", "''")
                sql = (
                    f'SELECT * FROM {table} WHERE '
                    f'"{dept_col}" = \'{safe_value}\';'
                )
                return sql, df[
                    df[dept_col].astype(str).str.lower()
                    == value.lower()
                ]

    # Show only names
    if name_col and any(x in q for x in [
        "show names", "list names", "student names",
        "display names", "only names"
    ]):
        return f'SELECT "{name_col}" FROM {table};', df[[name_col]]

    # Sort marks
    if marks_col and any(x in q for x in [
        "sort by marks", "order by marks",
        "marks descending", "rank students",
        "sort marks", "arrange by marks"
    ]):
        descending = not any(x in q for x in [
            "ascending", "lowest first", "smallest first"
        ])
        direction = "DESC" if descending else "ASC"
        sorted_df = df.sort_values(
            by=marks_col, ascending=not descending
        )
        sql = (
            f'SELECT * FROM {table} ORDER BY '
            f'"{marks_col}" {direction};'
        )
        return sql, sorted_df

    # Show all rows
    if any(x in q for x in [
        "show all", "all students", "display all",
        "show students", "list students",
        "show records", "display records",
        "all records", "everything"
    ]):
        return f"SELECT * FROM {table};", df

    return None, (
        "I couldn't understand that question. "
        "Try one of the example questions below."
    )

# ---------- QUESTION INPUT ----------
st.subheader("💬 Ask in Plain English")

question = st.text_input(
    "Type your question",
    placeholder="Example: Show students who scored above 80 marks"
)

st.caption("Example: Show all students | Count students | Highest marks")

if st.button("✨ Convert to SQL"):
    if not question.strip():
        st.warning("Please enter a question first.")
    else:
        sql, output = english_to_sql(question, result)

        if sql is None:
            st.info(output)
        else:
            st.markdown("### 🔍 Generated SQL Query")
            st.code(sql, language="sql")

            st.markdown("### 📖 Explanation")
            st.write(
                "This query retrieves the records requested "
                "by your question from the students dataset."
            )

            st.markdown("### 📊 Query Result")

            if output == "count":
                st.metric("Total records", len(result))
            elif isinstance(output, pd.DataFrame):
                st.dataframe(output, use_container_width=True)
            elif output == "highest":
                st.dataframe(
                    result.nlargest(
                        1, next(
                            c for c in result.columns
                            if str(c).lower() in [
                                "marks", "mark", "score", "scores"
                            ]
                        )
                    ),
                    use_container_width=True
                )
            elif output == "lowest":
                st.dataframe(
                    result.nsmallest(
                        1, next(
                            c for c in result.columns
                            if str(c).lower() in [
                                "marks", "mark", "score", "scores"
                            ]
                        )
                    ),
                    use_container_width=True
                )

# ---------- EXAMPLE QUESTIONS ----------
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

for example in examples:
    st.markdown(f"- {example}")

st.caption("Mini Project | Python • Pandas • Streamlit")
