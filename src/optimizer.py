"""
Optimizer Module
Course recommendation using PuLP optimization
HARDENED VERSION (Feasibility-safe)
"""

import pandas as pd
from pulp import *
import numpy as np


# ============================================================
# Adaptive Weights
# ============================================================
def calculate_adaptive_weights(student, backlogs, semester):
    cgpa = student['cgpa']

    w_progress = 10.0
    w_retake = 30.0
    w_difficulty = 2.0
    w_risk = 5.0

    if cgpa < 2.0:
        w_retake = 50.0
        w_difficulty = 4.0
        w_progress = 5.0
        w_risk = 8.0
    elif cgpa < 2.5:
        w_retake = 40.0
        w_difficulty = 3.0
        w_progress = 8.0
        w_risk = 6.0
    elif cgpa >= 3.5:
        w_progress = 15.0
        w_retake = 20.0
        w_difficulty = 1.0
        w_risk = 2.0

    if len(backlogs) > 3:
        w_retake = 60.0
    elif len(backlogs) > 1:
        w_retake = 45.0

    if semester >= 7:
        w_progress = 20.0

    return {
        'progress': w_progress,
        'retake': w_retake,
        'difficulty': w_difficulty,
        'risk': w_risk
    }


# ============================================================
# Optimizer Class
# ============================================================
class CourseOptimizer:

    def __init__(self, rules_dict):
        self.rules = rules_dict

    def recommend(self, eligible_df, student_profile, risk_scores=None,
                  weights=None, custom_constraints=None):

        if eligible_df.empty:
            return pd.DataFrame(), {'status': 'no_eligible_courses'}

        student = student_profile['student']
        backlogs = student_profile['backlogs']
        low_grades = student_profile['low_grades']

        if weights is None:
            weights = calculate_adaptive_weights(
                student, backlogs, student['current_semester']
            )

        # ====================================================
        # CREDIT LIMIT LOGIC (SAFE)
        # ====================================================
        on_probation = student.get('on_probation', False)

        NORMAL_MIN = 15
        NORMAL_MAX = 18
        OVERLOAD_MAX = 21
        PROBATION_MAX = 15

        if on_probation or student['cgpa'] < 2.0:
            max_credits = PROBATION_MAX
            min_credits = 12
            credit_status = "⚠️ Academic Probation"

        elif student['cgpa'] >= self.rules['min_cgpa_overload']:
            max_credits = OVERLOAD_MAX
            min_credits = NORMAL_MIN
            credit_status = "✅ Overload Eligible"

        elif student['cgpa'] >= 2.5:
            max_credits = NORMAL_MAX
            min_credits = NORMAL_MIN
            credit_status = "✅ Normal Load"

        else:
            max_credits = 16
            min_credits = 13
            credit_status = "⚠️ Reduced Load"

        if 'max_credits_allowed' in student:
            max_credits = min(max_credits, student['max_credits_allowed'])

        # HARDENING: ensure feasible credit limits
        total_possible_credits = eligible_df['credits'].sum()
        min_credits = min(min_credits, total_possible_credits)
        max_credits = min(max_credits, total_possible_credits)

        if min_credits > max_credits:
            min_credits = max_credits

        # ====================================================
        # OPTIMIZATION MODEL
        # ====================================================
        model = LpProblem("Course_Recommendation", LpMaximize)

        x = {
            row['course_code']: LpVariable(f"x_{row['course_code']}", cat='Binary')
            for _, row in eligible_df.iterrows()
        }

        if risk_scores is None:
            risk_scores = {code: 0.3 for code in x.keys()}

        # ====================================================
        # OBJECTIVE FUNCTION (SCALED & SAFE)
        # ====================================================
        objective_terms = []

        for _, row in eligible_df.iterrows():
            code = row['course_code']

            progress_score = weights['progress'] * row['credits']

            retake_score = 0
            if code in backlogs:
                retake_score = weights['retake']
            elif code in low_grades:
                retake_score = weights['retake'] * 0.5

            difficulty_penalty = weights['difficulty'] * row['difficulty']
            risk_penalty = weights['risk'] * risk_scores.get(code, 0.3)

            total_score = (
                progress_score +
                retake_score -
                difficulty_penalty -
                risk_penalty
            )

            objective_terms.append(total_score * x[code])

        model += lpSum(objective_terms)

        # ====================================================
        # CONSTRAINTS (ALL SAFE)
        # ====================================================
        model += (
            lpSum(row['credits'] * x[row['course_code']]
                  for _, row in eligible_df.iterrows()) <= max_credits,
            "Max_Credits"
        )

        if min_credits > 0:
            model += (
                lpSum(row['credits'] * x[row['course_code']]
                      for _, row in eligible_df.iterrows()) >= min_credits,
                "Min_Credits"
            )

        backlog_courses = [c for c in x if c in backlogs]

        if backlog_courses and self.rules.get('max_backlogs', 0) > 0:
            model += (
                lpSum(x[c] for c in backlog_courses) <= self.rules['max_backlogs'],
                "Max_Backlogs"
            )

        # HARDENED: NO forced backlog constraint ❌
        # (Handled via objective instead)

        model += (
            lpSum(x.values()) <= 6,
            "Max_Courses"
        )

        if custom_constraints:
            for name, constraint in custom_constraints.items():
                model += constraint, name

        # ====================================================
        # SOLVE
        # ====================================================
        status = model.solve(PULP_CBC_CMD(msg=0))

        if status != LpStatusOptimal:
            return pd.DataFrame(), {
                'status': 'no_solution',
                'solver_status': LpStatus[status],
                'credit_status': credit_status
            }

        selected = [c for c in x if x[c].value() == 1]

        recommended_df = eligible_df[
            eligible_df['course_code'].isin(selected)
        ].copy()

        recommended_df['risk_score'] = recommended_df['course_code'].map(risk_scores)

        metadata = {
            'status': 'optimal',
            'weights_used': weights,
            'total_credits': int(recommended_df['credits'].sum()),
            'max_credits': max_credits,
            'min_credits': min_credits,
            'credit_status': credit_status,
            'num_courses': len(recommended_df),
            'backlogs_cleared': len(set(selected) & backlogs),
            'avg_difficulty': round(recommended_df['difficulty'].mean(), 2),
            'avg_risk': round(recommended_df['risk_score'].mean(), 3),
            'objective_value': value(model.objective),
            'on_probation': on_probation
        }

        return recommended_df.reset_index(drop=True), metadata
