import streamlit as st
import pandas as pd
from collections import defaultdict
import re

# --- Load CDS data ---
CDS_PATH = "https://raw.githubusercontent.com/dataenthusiast7776/datadorm/refs/heads/main/common_data_set_master.csv"
df = pd.read_csv(CDS_PATH)

# Dictionary of trigger words (from previous step)
trigger_words = {
    "academic_calendar": ["calendar", "schedule", "grading period"],
    "total_undergrad_enrollment": ["undergrad", "undergrads", "undergraduates", "number of students", "how many students"],
    "undergraduate_percentage": ["undergrad", "undergrads", "undergraduates","undergraduate focus", "undergrad focus", "percent undergrad", "percent undergraduate", "how many undergrad"],
    "white_percent": ["demographic","demographics", "race", "pwi", "white", "diversity", "diverse"],
    "asian_percent": ["demographic", "demographics", "race", "asian", "indian", "diverse", "diversity"],
    "hispanic_percent": ["demographic", "demographics", "race", "hispanic", "latino", "latina", "latinx", "diverse", "diversity", "first gen"],
    "black_percent": ["demographic", "demographics", "race", "pwi", "black", "diversity", "colored", "hbcu", "diverse"],
    "international_percent": ["demographic", "demographics", "diverse", "diversity", "countries", "country", "international", "intl", "nonresident", "visa", "foreign"],
    "pell_grant_percent": ["fgli", "low income", "pell grant", "fafsa", "financial aid"],
    "pell_grant_number": ["fgli", "low income", "pell grant", "fafsa", "financial aid"],
    "retention_rate": ["retention", "come back", "graduation", "academic", "support"],
    "male_acceptance_rate": ["acceptance rate", "admit rate", "chances", "odds", "rejection rate", "probability"],
    "female_acceptance_rate": ["acceptance rate", "admit rate", "chances", "odds", "rejection rate", "probability"],
    "male_yield_rate": ["yield", "yield rate", "male yield rate"],
    "female_yield_rate": ["yield", "yield rate", "female yield rate"],
    "overall_acceptance_rate": ["selective", "get in", "get into", "acceptance rate", "admit rate", "chances", "odds", "rejection rate", "probability"],
    "overall_yield_rate": ["yield", "popularity", "cross-admit", "prestige", "prestigious"],
    "waitlist_offered": ["waitlist", "waitlisted", "wait list", "wait listed"],
    "waitlist_accepted": ["offered place on waitlist", "accepted waitlist", "accepted a spot on waitlist", "waitlist acceptance", "waitlist accepted", "waitlisted", "wait list accepted"],
    "waitlist_admitted": ["got off the waitlist", "waitlist admitted", "admitted from waitlist", "accepted from waitlist", "waitlist acceptance", "waitlisted", "wait list admitted"],
    "foreign_language_requirement": ["language", "foreign language", "spanish", "german", "french", "latin"],
    "demonstrated_interest": ["demonstrated interest", "track interest", "webinars", "show interest"],
    "very_important_factors": ["how important", "most important", "course rigor", "test scores"],
    "test_policy": ["test policy", "test optional", "test-optional", " TO ", "test blind", "test scores", "SAT", "ACT", "submit scores"],
    "percent_SAT": ["submitted SAT", "SAT preference", "SAT or ACT", "test preference"],
    "percent_ACT": ["submitted ACT", "ACT preference", "SAT or ACT", "test preference"],
    "sat_composite_25th": ["SAT percentile", "SAT score", "25th percentile"],
    "sat_composite_50th": ["average SAT", "SAT percentile", "SAT score", "median"],
    "sat_composite_75th": ["SAT percentile", "SAT score", "75th percentile"],
    "sat_reading_25th": ["SAT Reading", "Reading score", "SAT R", "25th percentile"],
    "sat_reading_50th": ["SAT Reading", "Reading score", "SAT R", "median", "SAT percentile"],
    "sat_reading_75th": ["SAT Reading", "Reading score", "SAT R", "75th percentile", "top quartile", "SAT percentile"],
    "sat_math_25th": ["SAT Math", "Math score", "SAT M", "25th percentile", "lower quartile", "SAT percentile"],
    "sat_math_50th": ["average SAT Math", "SAT Math percentile", "SAT Math score", "median", "SAT M", "50th percentile"],
    "sat_math_75th": ["SAT Math", "Math score", "SAT M", "75th percentile", "upper quartile", "SAT percentile"],
    "act_composite_25th": ["ACT percentile", "ACT score", "25th percentile", "ACT composite", "ACT"],
    "act_composite_50th": ["average ACT", "ACT percentile", "ACT score", "median", "ACT composite", "ACT"],
    "act_composite_75th": ["ACT percentile", "ACT score", "75th percentile", "ACT composite", "ACT"],
    "sat_reading_700_800": ["SAT reading 700 to 800", "SAT reading high scores", "SAT reading top scores", "SAT reading 700+", "SAT reading 700-800"],
    "sat_math_700_800": ["SAT math 700 to 800", "SAT math high scores", "SAT math top scores", "SAT math 700+", "SAT math 700-800"],
    "sat_reading_600_699": ["SAT reading 600 to 699", "SAT reading mid scores", "SAT reading 600-699", "SAT reading 600+", "SAT reading scores"],
    "sat_math_600_699": ["SAT math 600 to 699", "SAT math mid scores", "SAT math 600-699", "SAT math 600+", "SAT math scores"],
    "percent_top_10": ["class rank", "top 10%", "course rigor", "top ten percent", "top 10 percent"],
    "top_25_percent": ["class rank", "top 25%", "top twenty-five percent", "course rigor"],
    "top_50_percent": ["class rank", "top 50%", "top fifty percent", "course rigor"],
    "percent_gpa_4": ["GPA", "4.0 GPA", "perfect GPA", "grade point average", "GPA distribution"],
    "percent_gpa_375_399": ["GPA", "3.75 to 3.99 GPA", "high GPA range", "grade point average", "GPA distribution"],
    "percent_gpa_350_374": ["GPA", "3.50 to 3.74 GPA", "mid-high GPA range", "grade point average", "GPA distribution"],
    "deferred_admission": ["gap", "gap year", "deferral", "deferred admission", "defer admission", "defer"],
    "early_decision_info": [" ED ", "early decision", "binding"],
    "early_action": [" EA ", " REA ", "early action", " SCEA "],
    "transfer_acceptance_rate_men": ["transfer", "transfer acceptance rate", "transfer admit rate", "transfer admission", "transfer acceptance"],
    "transfer_yield_rate_men": ["transfer yield rate", "transfer yield rate men", "transfer admission"],
    "transfer_acceptance_rate_women": ["transfer", "transfer acceptance rate", "transfer admit rate", "transfer admission", "transfer acceptance"],
    "transfer_yield_rate_women": ["transfer yield rate", "transfer yield rate women", "transfer admission"],
    "transfer_yield_rate_overall": ["transfer yield rate", "transfer admission"],
    "transfer_acceptance_rate_overall": ["transfer", "transfer acceptance rate", "transfer admit rate", "transfer admission", "transfer acceptance"],
    "study_abroad": ["study abroad", "study away", "exchange student", "travel"],
    "honors_program": ["honors", "honors program", "honors college"],
    "tuition_private": ["tuition", "cost"],
    "tuition_in_state": ["tuition", "cost", "in-state"],
    "tuition_out_state": ["tuition", "cost", "out-of-state", "out of state"],
    "required_fees": ["fees", "required fees", "mandatory fees", "extra costs"],
    "room_and_board": ["room and board", "housing cost", "meal plan", "living expenses"],
    "cost_of_attendance_private": ["cost of attendance", "cost", "total cost", "full cost", "total expenses"],
    "need_based_total": ["financial aid", "need-based aid", "need based aid", "financial need"],
    "non_need_based_total": ["non-need based aid", "merit aid", "scholarship", "non need-based aid", "merit scholarship"],
    "need_based_avg": ["need-based aid", "need based aid", "average need-based aid", "average need based aid", "average financial aid", "average need aid"],
    "non_need_based_avg": ["non need based aid", "non-need based aid", "average non-need based aid", "average merit aid", "average scholarship", "average merit scholarship"],
    "num_on_aid": ["number on aid", "students on aid", "students receiving aid", "count on aid"],
    "percent_on_aid": ["percent on aid", "percentage on aid", "students on aid percentage", "percentage receiving aid"],
    "need_met_percent": ["need met", "percentage of need met", "meets need", "meets financial need"],
    "avg_financial_aid": ["average financial aid", "average aid", "financial aid amount", "avg aid"],
    "international_aid": ["international", "intl", "f1", "visa", "financial aid international", "cost international", "international student aid", "aid for international students"],
    "international_students_on_aid": ["international students aid", "intl students with aid", "international aid awarded", "first-year international aid", "international aid", "number of international students with aid"],
    "international_aid_average": ["average international aid", "intl aid average", "mean aid for international students", "average financial aid international", "avg aid for intl students"],
    "student_faculty_ratio": ["student-faculty ratio", "undergrad focus", "undergraduate focus", "faculty ratio", "students per faculty", "class size", "teacher ratio"],
    "school_type": ["type of school"],
    "US_News_ranking": ["ranking", "prestige", "prestigious", "top school", "rankings", "well-known", "ivy", "rank",],
    "school_fit": ["fit", "campus culture", "style", "type of students", "students like"],
    "ED_acceptance_rate": ["early decision", " ED ", "early decision boost", "early acceptance rate", "binding"],


    

    
    
}

# Column descriptions for better output
column_descriptions = {
    "academic_calendar": "academic calendar or schedule",
    "total_undergrad_enrollment": "total number of undergraduate students enrolled",
    "undergraduate_percentage": "percentage of students who are undergraduates",
    "white_percent": "percentage of first-time first-year freshmen who were White",
    "asian_percent": "percentage of first-time first-year freshmen who were Asian or Indian",
    "hispanic_percent": "percentage of first-time first-year freshmen who were Hispanic/Latino",
    "black_percent": "percentage of first-time first-year freshmen who were Black or African American",
    "international_percent": "percentage of first-time first-year freshmen who were international or nonresident aliens",
    "pell_grant_percent": "percentage of students receiving Pell Grants (low income or FAFSA recipients)",
    "pell_grant_number": "number of students receiving Pell Grants",
    "retention_rate": "retention rate of students returning for the next academic year",
    "male_acceptance_rate": "acceptance rate for male applicants",
    "female_acceptance_rate": "acceptance rate for female applicants",
    "male_yield_rate": "percentage of male students who chose to enroll after being admitted",
    "female_yield_rate": "percentage of female students who chose to enroll after being admitted",
    "overall_acceptance_rate": "total percentage of applicants who were admitted to the college",
    "overall_yield_rate": "percentage of all admitted students who chose to enroll",
    "waitlist_offered": "number of students who were offered a place on the waitlist",
    "waitlist_accepted": "number of students who accepted a spot on the waitlist",
    "waitlist_admitted": "number of students who were admitted from the waitlist",
    "foreign_language_requirement": "number of recommended years of foreign language the college recommends or requires",
    "demonstrated_interest": "policy on whether or not demonstrated interest will be factored into admissions decisions",
    "very_important_factors": "most important academic and personal factors in the college's admissions decisions",
    "test_policy": "college's standardized test policy",
    "percent_SAT": "percentage of enrolled students who submitted SAT scores over ACT scores",
    "percent_SAT": "percentage of enrolled students who submitted ACT scores over SAT scores",
    "sat_composite_25th": "25th percentile composite SAT score of admitted students",
    "sat_composite_50th": "50th percentile (median) composite SAT score of admitted students",
    "sat_composite_75th": "75th percentile composite SAT score of admitted students",
    "sat_reading_25th": "25th percentile SAT Reading score of admitted students",
    "sat_reading_50th": "50th percentile (median) SAT Reading score of admitted students",
    "sat_reading_75th": "75th percentile SAT Reading score of admitted students",
    "sat_math_25th": "25th percentile SAT Math score of admitted students",
    "sat_math_50th": "50th percentile (median) SAT Math score of admitted students",
    "sat_math_75th": "75th percentile SAT Math score of admitted students",
    "act_composite_25th": "25th percentile ACT composite score of admitted students",
    "act_composite_50th": "median (50th percentile) ACT composite score of admitted students",
    "act_composite_75th": "75th percentile ACT composite score of admitted students",
    "sat_reading_700_800": "percentage of admitted students scoring between 700 and 800 on the SAT Reading section",
    "sat_math_700_800": "percentage of admitted students scoring between 700 and 800 on the SAT Math section",
    "sat_reading_600_699": "percentage of students scoring between 600 and 699 on the SAT Reading section",
    "sat_math_600_699": "percentage of students scoring between 600 and 699 on the SAT Math section",
    "percent_top_10": "percentage of admitted students ranked in the top 10 percent of their high school class",
    "top_25_percent": "percentage of admitted students ranked in the top 25 percent of their high school class",
    "top_50_percent": "percentage of admitted students ranked in the top 50 percent of their high school class",
    "percent_gpa_4": "percentage of admitted students with a 4.0 unweighted GPA",
    "percent_gpa_375_399": "percentage of admitted students with an unweighted GPA between 3.75 and 3.99",
    "percent_gpa_350_374": "percentage of admitted students with an unweighted GPA between 3.50 and 3.74",
    "deferred_admission": "policy of granting deferred admission to students who choose to take a gap year",
    "early_decision_info": "Information about whether or not the school offers an early decision progrsm",
    "early_action": "Information about whether the school offers early action or restrictive early action",
    "transfer_acceptance_rate_men": "acceptance rate for male transfer applicants",
    "transfer_yield_rate_men": "percentage of male transfer applicants who chose to enroll after being admitted",
    "transfer_acceptance_rate_women": "acceptance rate for female transfer applicants",
    "transfer_yield_rate_women": "percentage of female transfer applicants who chose to enroll after being admitted",
    "transfer_yield_rate_overall": "percentage of transfer applicants who chose to enroll after being admitted",
    "transfer_acceptance_rate_overall": "acceptance rate for transfer applicants overall",
    "study_abroad": "study abroad program offerings",
    "honors_program": "honors program or special opportunities for honors students",
    "tuition_private": "annual tuition cost for this private institution",
    "tuition_in_state": "annual tuition cost for in-state students",
    "tuition_out_state": "annual tuition cost for out-of-state students",
    "required_fees": "additional mandatory fees students must pay apart from tuition",
    "room_and_board": "estimated cost for housing and meals for students living on campus",
    "cost_of_attendance_private": "total estimated annual cost of attendance including tuition, fees, room, and board",
    "need_based_total": "total amount of need-based financial aid awarded by the college per year",
    "non_need_based_total": "total amount of non-need-based financial aid (such as merit scholarships) awarded by the college per year",
    "need_based_avg": "average amount of need-based financial aid awarded to undergraduates per year",
    "non_need_based_avg": "average amount of non-need-based financial aid awarded to undergraduates per year",
    "num_on_aid": "number of first-year students receiving financial aid",
    "percent_on_aid": "percentage of first-year students receiving financial aid",
    "need_met_percent": "average percentage of financial need met for students awarded aid",
    "avg_financial_aid": "average amount of financial aid awarded to undergraduate students",
    "international_aid": "international students' eligibility for institutional financial aid",
    "international_students_on_aid": "number of first-year international students awarded any institutional aid",
    "international_aid_average": "Average amount of institutional aid awarded to international students",
    "student_faculty_ratio": "Average number of undergraduates per faculty member",
    "school_type": "Type of college that this institution falls under",
    "US_News_ranking": "latest US News ranking of this institution out of all same-type institutions in the USA",
    "school_fit": "Adjectives that describe the general vibe and typical student at this school",
    "ED_acceptance_rate": "percentage of applicants who applied through a binding early decision program that were accepted",
    
}


def is_trigger_present(query_words, trigger, query_text):
    trigger_lower = trigger.lower()
    trigger_tokens = trigger_lower.split()

    # Boost if exact phrase exists in query text
    if trigger_lower in query_text.lower():
        return len(trigger_tokens) + 2  # extra boost

    # Phrase match fallback
    if len(trigger_tokens) > 1 and set(trigger_tokens).issubset(query_words):
        return len(trigger_tokens)

    # Single word generic check
    generic_words = {"rate", "the", "and", "of", "for", "to"}
    if len(trigger_tokens) == 1:
        if trigger_tokens[0] in generic_words:
            return 0
        return 1 if trigger_tokens[0] in query_words else 0

    return 0

def detect_query_type(query_text):
    text = query_text.lower()

    if any(word in text for word in ["which", "compare", "more", "less", "versus", "vs", "difference", "better than", "worse than"]):
        return "Comparison"
    if any(word in text for word in ["top", "most", "highest", "lowest", "rank", "best", "worst"]):
        return "Rank"
    return "General"


def extract_colleges_from_query(query_text, college_names, max_results=10):
    """
    Extract college names from the query_text by matching against known college_names.
    Returns a list of matched colleges (case insensitive).
    """
    query_text_lower = query_text.lower()
    matched = []

    for college in college_names:
        # Match if college name or abbreviation appears in query text (case insensitive)
        # Using word boundaries to avoid partial matches inside other words
        pattern = r'\b' + re.escape(college.lower()) + r'\b'
        if re.search(pattern, query_text_lower):
            matched.append(college)
            if len(matched) >= max_results:
                break

    return matched


# --- Query Parsing ---

def parse_query(college_list, query_text, top_n=5):
    filter_requested = query_text.lower().strip().startswith("which colleges")
    query_words = set(re.findall(r'\b\w+\b', query_text.lower()))
    column_scores = defaultdict(int)

    is_transfer_query = "transfer" in query_words

    for col, triggers in trigger_words.items():
        if "transfer" in col.lower() and not is_transfer_query:
            continue

        for trig in triggers:
            score = is_trigger_present(query_words, trig, query_text)
            column_scores[col] += score

    # Only keep columns with score > 0
    filtered = [(col, score) for col, score in column_scores.items() if score > 0]

    if not filtered:
        return None, "Sorry, I couldn't find relevant data for your query. You may need to be more specific or more broad.", "General", filter_requested

    # Sort and deduplicate by top scores
    filtered.sort(key=lambda x: x[1], reverse=True)
    seen = set()
    matched_columns = []

    for col, _ in filtered:
        if col not in seen:
            matched_columns.append(col)
            seen.add(col)
            if len(matched_columns) >= top_n:
                break

    query_type = detect_query_type(query_text)
    return matched_columns, None, query_type, filter_requested


def try_parse_number(val):
    if isinstance(val, str):
        val = val.replace('%', '').replace(',', '').strip()
    try:
        return float(val)
    except:
        return None

def generate_comparison_summary(colleges, metric_col):
    inverse_logic_metrics = {
        "US_News_ranking"
    }

    metric_name = column_descriptions.get(metric_col, metric_col.replace('_', ' '))
    values = []
    for college in colleges:
        row = df[df['college'].str.lower() == college.lower()]
        if row.empty or pd.isna(row.iloc[0][metric_col]):
            values.append((college, None))
        else:
            val = row.iloc[0][metric_col]
            values.append((college, val))

    available = []
    for c, v in values:
        try:
            num_val = float(v)
            available.append((c, num_val))
        except (ValueError, TypeError):
            continue

    if len(available) < 2:
        return f"Unfortunately, at least one of the schools doesn't release {metric_name}."

    first_val = available[0][1]
    if all(abs(v - first_val) < 1e-6 for _, v in available):
        formatted_val = format_value_for_display(metric_col, first_val)
        return f"All selected colleges have approximately the same {metric_name}: `{formatted_val}`."

    if len(available) == 2:
        (college1, val1), (college2, val2) = available
        val1_fmt = format_value_for_display(metric_col, val1)
        val2_fmt = format_value_for_display(metric_col, val2)

        if metric_col in inverse_logic_metrics:
            if val1 < val2:
                return f"**{college1}** is ranked higher (`{val1_fmt}`) than **{college2}** (`{val2_fmt}`)."
            elif val1 > val2:
                return f"**{college2}** is ranked higher (`{val2_fmt}`) than **{college1}** (`{val1_fmt}`)."
            else:
                return f"**{college1}** and **{college2}** are tied in ranking (`{val1_fmt}`)."
        else:
            if val1 > val2:
                return f"**{college1}** has a higher {metric_name} (`{val1_fmt}`) than **{college2}** (`{val2_fmt}`)."
            elif val1 < val2:
                return f"**{college1}** has a lower {metric_name} (`{val1_fmt}`) than **{college2}** (`{val2_fmt}`)."
            else:
                return f"**{college1}** and **{college2}** have the same {metric_name} (`{val1_fmt}`)."

    max_college, max_val = max(available, key=lambda x: x[1])
    min_college, min_val = min(available, key=lambda x: x[1])

    max_display = format_value_for_display(metric_col, max_val)
    min_display = format_value_for_display(metric_col, min_val)

    others = [c for c, v in available if c != max_college and c != min_college]
    if metric_col in inverse_logic_metrics:
        summary = (
            f"**{min_college}** is ranked highest (`{min_display}`), "
            f"while **{max_college}** is ranked lowest (`{max_display}`)."
        )
    else:
        summary = (
            f"**{max_college}** has the highest {metric_name} at `{max_display}`, "
            f"while **{min_college}** has the lowest at `{min_display}`."
        )

    if others:
        others_str = ", ".join(f"**{c}**" for c in others)
        summary += f" The other colleges ({others_str}) fall in between."

    return summary


def generate_qualitative_comparison(colleges, metric_col='school_fit'):
    # Extract adjectives for each college
    adjectives_map = {}
    for college in colleges:
        row = df[df['college'].str.lower() == college.lower()]
        if row.empty or pd.isna(row.iloc[0][metric_col]):
            adjectives_map[college] = set()
        else:
            # Assume adjectives are comma-separated
            adjectives = row.iloc[0][metric_col]
            # Clean and split into a set of lowercase adjectives
            adjectives_set = set(a.strip().lower() for a in adjectives.split(','))
            adjectives_map[college] = adjectives_set

    # If any school has no data
    if any(len(adjs) == 0 for adjs in adjectives_map.values()):
        return f"At least one selected school doesn't have {metric_col} data available."

    # Find common adjectives across all schools
    common_adjectives = set.intersection(*adjectives_map.values())

    # Find unique adjectives for each school (those not in common)
    unique_adjectives = {college: adjs - common_adjectives for college, adjs in adjectives_map.items()}

    # Format the summary
    summary_parts = []
    if common_adjectives:
        summary_parts.append(
            f"All selected schools share the following qualities: {', '.join(sorted(common_adjectives))}."
        )
    else:
        summary_parts.append("The selected schools do not share any common qualities.")

    for college, uniques in unique_adjectives.items():
        if uniques:
            summary_parts.append(
                f"**{college}** is distinct for being {', '.join(sorted(uniques))}."
            )
        else:
            summary_parts.append(
                f"**{college}** does not have unique qualities compared to the others."
            )

    return " ".join(summary_parts)


def generate_ranking_output(colleges, matched_columns):
    if isinstance(matched_columns, str):
        matched_columns = [matched_columns]

    results = []
    for col in matched_columns[:2]:  # limit to 2 columns max
        rows = []
        for college in colleges:
            row = df[df['college'].str.lower() == college.lower()]
            if not row.empty:
                val = row.iloc[0][col]
                if val not in [None, "none", "None"] and not pd.isna(val):
                    try:
                        rows.append((college, float(val)))
                    except:
                        continue
        if not rows:
            continue

        # If ranking by US_News_ranking, lower value is better -> sort ascending
        if col == "US_News_ranking":
            sorted_rows = sorted(rows, key=lambda x: x[1])
        else:
            # For other metrics, higher is better -> sort descending
            sorted_rows = sorted(rows, key=lambda x: x[1], reverse=True)

        output_lines = [f"🔢 Ranking by {column_descriptions.get(col, col)}:"]
        for idx, (college, val) in enumerate(sorted_rows, start=1):
            line = f"**#{idx}**. {college}: `{format_value_for_display(col, val)}`"
            output_lines.append(line)

        results.append("\n".join(output_lines))  # Join lines for this column's ranking

    return "\n\n".join(results) if results else "No numeric data available to rank."


def format_value_for_display(column_name, value):
    if value is None or (isinstance(value, str) and value.strip().lower() == "none") or pd.isna(value):
        return "N/A"

    # Handle percentage-based columns
    if any(kw in column_name.lower() for kw in ["rate", "percentage", "percent"]):
        try:
            val = float(value)
            if val <= 0.01:
                val *= 100  # Convert from 0.XX to XX%
            return f"{val:.1f}%"
        except:
            return str(value)

    # Handle large numbers with commas
    if isinstance(value, (int, float)):
        if abs(value) >= 1000:
            return f"{value:,.0f}"
        else:
            return f"{value:.2f}"

    # Handle boolean-like strings
    val_str = str(value).strip().lower()
    if val_str in ["yes", "true", "✓"]:
        return "✅ Yes"
    elif val_str in ["no", "false", "✗"]:
        return "❌ No"

    return str(value)


def generate_filter_output(matched_col, colleges):
    col = matched_col  # only 1 column usually
    description = column_descriptions.get(col, col)
    subset_df = df[df['college'].str.lower().isin([c.lower() for c in colleges])]
    filtered_df = subset_df[subset_df[col].astype(str).str.lower().isin(['yes', 'true', '1'])]

    if filtered_df.empty:
        return f"No colleges in the provided list meet the criteria for **{description}**."

    lines = [f"**Colleges where {description.lower()} is true:**"]
    for college in filtered_df['college']:
        lines.append(f"- {college}")
    return "\n".join(lines)


def is_numeric_column(metric_col):
    # Quick check if column is numeric by testing first few non-null values
    sample_values = df[metric_col].dropna().head(10).tolist()
    for val in sample_values:
        try:
            float(val)
        except (ValueError, TypeError):
            return False
    return True

def get_college_data(colleges, query_text):
    matched_columns, error, query_type, filter_requested = parse_query(colleges, query_text)
    if error:
        return error

    if filter_requested and matched_columns:
        return generate_filter_output(matched_columns[0], colleges)

    if query_type == "Comparison" and len(colleges) >= 2 and matched_columns:
        comparison_summaries = []
        for metric_col in matched_columns:
            if metric_col != 'college_fit':
                summary = generate_comparison_summary(colleges, metric_col)
            else:
                summary = generate_qualitative_comparison(colleges, metric_col)
            comparison_summaries.append(summary)
        return "\n\n".join(comparison_summaries)

    elif query_type == "Rank" and matched_columns:
        if not colleges:
            colleges = df["college"].dropna().unique().tolist()
        return generate_ranking_output(colleges, matched_columns)

    # General info for each college
    output_blocks = []
    for college in colleges:
        row = df[df['college'].str.lower() == college.lower()]
        if row.empty:
            output_blocks.append(f"⚠️ Could not find data for **{college}**.")
            continue

        lines = [f"**{college}**"]
        for col in matched_columns:
            if col in row.columns:
                val = row.iloc[0][col]
                description = column_descriptions.get(col, col)

                if val is None or (isinstance(val, str) and val.strip().lower() == "none") or pd.isna(val):
                    lines.append(
                        f'- {description}: <span style="color: red;">Unfortunately, this college doesn\'t release this information.</span>'
                    )
                else:
                    formatted_val = format_value_for_display(col, val)
                    lines.append(f"- {description}: `{formatted_val}`")
            else:
                lines.append(f"- Column `{col}` not found.")

        # 🔗 Add source URL if available
        url = row.iloc[0].get("url", None)
        if pd.notna(url) and url not in [None, "", "none"]:
            lines.append(f"[🔗 Source]({url})")

        output_blocks.append("\n".join(lines))

    return "\n\n".join(output_blocks)


def remove_duplicate_college_lines(text):
    lines = text.strip().split('\n')
    seen = set()
    cleaned = []
    for line in lines:
        # Normalize line (remove extra spaces, lowercase)
        norm_line = re.sub(r'\s+', ' ', line.strip().lower())
        if norm_line in seen:
            continue
        seen.add(norm_line)
        cleaned.append(line)
    return "\n".join(cleaned)

def format_bot_message_for_ui(raw_msg):
    # Split on college name lines — assuming each college name is on its own line
    # This simple split assumes college names are lines without "-"
    blocks = []
    current_block = []
    for line in raw_msg.splitlines():
        if line.strip() and not line.strip().startswith("-"):
            # New college name line
            if current_block:
                blocks.append(current_block)
            current_block = [line.strip()]
        else:
            current_block.append(line.strip())
    if current_block:
        blocks.append(current_block)

    # Format each block
    formatted_blocks = []
    for block in blocks:
        college_name = block[0]
        data_lines = block[1:]
        # Wrap college name in <strong> or <h3> for bigger font and color
        college_html = f'<div class="college-block"><div class="college-name">{college_name}</div>'
        # Format data lines as <ul><li>...</li></ul> with larger font size on <ul>
        if data_lines:
            items = ''.join(f'<li>{line[2:] if line.startswith("- ") else line}</li>' for line in data_lines)
            college_html += f'<ul style="font-size:28px;">{items}</ul>'
        college_html += '</div><br>'
        formatted_blocks.append(college_html)

    return '\n'.join(formatted_blocks)

def highlight_values(text):
    # Match numbers (including percentages or decimals)
    return re.sub(r'(\d[\d,\.]*%?)', r'<span style="color: red; font-weight: bold;">\1</span>', text)

def render_bot_message(college, data_lines):
    html = f"""
    <div style="
        background: #f0f4f8; 
        border-radius: 8px; 
        padding: 15px; 
        margin-bottom: 1rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    ">
        <h3 style="margin: 0 0 10px 0; color: #0b3d91;">{college}</h3>
        <ul style="margin: 0; padding-left: 20px; color: #333;">
    """

    for line in data_lines:
        html += f"<li style='margin-bottom: 12px;'>{line}</li>"

    html += "</ul></div>"
    return html



# --- Page config ---
st.set_page_config(page_title="DataDorm", layout="centered")

# --- App Title ---
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🏫 DataDorm</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>All your admissions data under one roof.</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    """
    <p style='text-align: center; color: white; font-size: 16px;'>
    Welcome to <strong>DataDorm</strong>! A free, open-source search engine for college admission data backed by official Common Data Sets, this tool will give you all the data you need without having to scour the Internet! 
    <br><br>
    Our <strong>Query</strong> feature allows you to directly input a natural language search for college admission metrics across various colleges. Our <strong>Graph</strong> feature allows you to build your own graph to visualize relationships between metrics. 
    <br><br>
    We are constantly adding colleges to our database! If you find a college that is missing, do tell us by filling out <a href="#" style='color: #90CAF9;'>this</a> form.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="text-align: center; margin-top: 30px;">
        <a href="https://match-my-app.streamlit.app/" target="_blank" style="
            display: inline-block;
            font-size: 20px;
            padding: 18px 36px;
            background-color: #e53935;
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            text-decoration: none;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease-in-out;
        ">
            🔗 Explore MatchMyApp
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; color: white; font-size: 15px; margin-top: 20px;'>
        Want to find past applicant profiles similar to you who got into top schools? 
    </p>
    """,
    unsafe_allow_html=True
)

tab1, tab2 = st.tabs(["🔍 Query Engine", "📊 Graph Builder"])

with tab1:
    # --- Chat history session state ---
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # --- Input fields on top ---
    # --- Input fields on top ---
    colleges = sorted(df['college'].dropna().unique())

    # Add query type dropdown
    query_type = st.selectbox(
        "Type of Query",
        options=["Data Retrieval and Comparison", "Rank"]
    )

    selected_colleges = []
    query = ""

    # Conditionally show inputs based on query_type
    if query_type in ["Data Retrieval and Comparison"]:
        
        selected_colleges = st.multiselect(
            "Select College(s)",
            options=colleges,
            help="Type to search and select one or more colleges"
        )
        query = st.text_input(
            "Query",
            placeholder="e.g. What is the acceptance rate?",
            label_visibility="collapsed"
        )
    elif query_type == "Rank":
        # For ranking, show a metric input box instead of college selector
        query = st.text_input(
            "What metric would you like to rank by?",
            placeholder="e.g. acceptance rate, retention rate",
            label_visibility="collapsed"
        )

    submit = st.button("Find Data!")

    # Now on submit, you have:
    # - query_type (str)
    # - selected_colleges (list, may be empty for rank)
    # - query (string, the query or metric)

    if submit:
        if query_type in ["Data Retrieval and Comparison"]:
            if not selected_colleges:
                st.error("Please select at least one college.")
            elif not query.strip():
                st.error("Please enter a query.")
            else:
                # call your get_college_data or comparison function here
                result = get_college_data(selected_colleges, query)
                st.write(result)

        elif query_type == "Rank":
            if not query.strip():
                st.error("Please enter a metric to rank by.")
            else:
                # Instead of passing 'query' directly as column name, parse it first
                matched_columns, error, query_type_inner, _ = parse_query(colleges, query)
                if error:
                    st.error(error)
                elif not matched_columns:
                    st.error("No matching metric found to rank by.")
                else:
                    # Use the matched column name here, NOT the full query string
                    result = generate_ranking_output(colleges, matched_columns)
                    if result.startswith("🔢 Ranking by"):
                        st.markdown(result.replace("\n", "<br>"), unsafe_allow_html=True)
                        
                    else:
                        st.write(result)


# --- Chat CSS styling ---
st.markdown("""
    <style>
    .chat-box {
        background-color: #111;
        color: white;
        height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #333;
        font-family: monospace;
        margin-top: 2rem;
    }
    .user-msg {
        color: #00ffff;
        margin-bottom: 1rem;
    }
    .bot-msg {
        color: #90ee90;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.user-msg {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 16px;
    margin-bottom: 6px;
    color: #ffffff;
}
.bot-msg {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 16px;
    margin-bottom: 18px;
    background-color: #000000;
    padding: 12px 20px;
    border-radius: 8px;
    color: #66CCCC
    line-height: 1.5;
    white-space: normal;
}
.bot-msg strong {
    font-size: 18px;
    color: #0b3d91;
}
.bot-msg ul {
    padding-left: 20px;
    margin-top: 8px;
    margin-bottom: 0;
}
.bot-msg li {
    margin-bottom: 6px;
}
.bot-msg code {
    background-color: #a4b4c4;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: Consolas, monospace;
    font-weight: 600;
    color: #d6336c;
}
</style>
""", unsafe_allow_html=True)

if st.session_state.chat_history:
    for msg in st.session_state.chat_history:
        st.markdown(f'<div class="user-msg">🧑 You: {msg["user"]}</div>', unsafe_allow_html=True)

        raw_bot_msg = msg["bot"]
        cleaned_bot_msg = remove_duplicate_college_lines(raw_bot_msg)

        # Remove markdown characters like ** and backticks `
        cleaned_bot_msg = cleaned_bot_msg.replace('**', '').replace('`', '')

        # Use the new function to format the message into HTML blocks per college
        formatted_bot_msg = format_bot_message_for_ui(cleaned_bot_msg)
        highlighted_bot_msg = highlight_values(formatted_bot_msg)

        st.markdown(f'<div class="bot-msg">🤖 DormBot: {highlighted_bot_msg}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="color:gray;">No messages yet. Ask something about a college...</div>', unsafe_allow_html=True)
