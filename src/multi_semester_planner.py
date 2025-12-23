"""
Multi-Semester Planner Module
Plans course sequences across multiple semesters
(Improved & Logic-Correct Version)
"""

import pandas as pd
import numpy as np
import networkx as nx


class MultiSemesterPlanner:
    """Plans optimal graduation path across multiple semesters"""

    def __init__(self, courses_df, prereq_graph, rules_dict):
        self.courses = courses_df
        self.G = prereq_graph
        self.rules = rules_dict

        # Academic constraints
        self.total_credits = self.rules.get('total_degree_credits', 137)
        self.max_semesters = self.rules.get('max_semesters', 8)

    # ------------------------------------------------------------------
    # GRADUATION ESTIMATION (FIXED)
    # ------------------------------------------------------------------
    def estimate_graduation_semester(self, student_profile, completed_courses):
        """
        Estimate realistic graduation semester (capped at max semesters)
        """

        completed_df = self.courses[self.courses['course_code'].isin(completed_courses)]
        completed_credits = completed_df['credits'].sum()

        remaining_credits = self.total_credits - completed_credits

        # Already graduated
        if remaining_credits <= 0:
            return min(
                student_profile['student']['current_semester'],
                self.max_semesters
            )

        cgpa = student_profile['student']['cgpa']

        # Avg credit load (rule-based)
        if cgpa >= 3.0:
            avg_credits = self.rules.get('avg_credits_high_cgpa', 20)
        elif cgpa >= 2.5:
            avg_credits = self.rules.get('avg_credits_mid_cgpa', 18)
        elif cgpa >= 2.0:
            avg_credits = self.rules.get('avg_credits_low_cgpa', 16)
        else:
            avg_credits = self.rules.get('avg_credits_probation', 15)

        semesters_needed = int(np.ceil(remaining_credits / avg_credits))

        estimated = student_profile['student']['current_semester'] + semesters_needed

        # 🔴 HARD CAP (CRITICAL FIX)
        return min(estimated, self.max_semesters)

    # ------------------------------------------------------------------
    # MULTI-SEMESTER PLANNER (IMPROVED)
    # ------------------------------------------------------------------
    def plan_graduation_path(
        self,
        student_profile,
        completed_courses,
        num_semesters=4,
        risk_predictor=None
    ):
        current_sem = student_profile['student']['current_semester']
        cgpa = student_profile['student']['cgpa']

        completed_so_far = set(completed_courses)
        remaining_courses = set(self.courses['course_code']) - completed_courses

        semester_plans = []
        total_planned_credits = 0

        for offset in range(1, num_semesters + 1):
            target_sem = current_sem + offset

            if target_sem > self.max_semesters:
                break

            # Credit limit
            max_credits = (
                self.rules['max_overload_credits']
                if cgpa >= 3.0
                else self.rules['max_normal_credits']
            )

            eligible = []

            for code in list(remaining_courses):
                row = self.courses[self.courses['course_code'] == code]
                if row.empty:
                    continue
                row = row.iloc[0]

                prereqs = list(self.G.predecessors(code))
                prereq_ok = all(p in completed_so_far for p in prereqs)

                # 🔴 FIX: allow courses offered earlier to be taken later
                semester_ok = row['semester'] <= target_sem

                if prereq_ok and semester_ok:
                    eligible.append(row.to_dict())

            if not eligible:
                semester_plans.append({
                    'semester': target_sem,
                    'courses': [],
                    'course_names': [],
                    'total_credits': 0,
                    'note': 'No eligible courses'
                })
                continue

            eligible_df = pd.DataFrame(eligible)

            # Risk-aware sorting
            if risk_predictor and getattr(risk_predictor, "trained", False):
                risks = []
                for _, c in eligible_df.iterrows():
                    risk = risk_predictor.predict_risk(
                        cgpa,
                        c['difficulty'],
                        c['credits'],
                        target_sem
                    )
                    risks.append(risk)

                eligible_df['risk'] = risks

                # Prefer low-risk, high-impact courses
                eligible_df['unlock_power'] = eligible_df['course_code'].apply(
                    lambda x: len(nx.descendants(self.G, x))
                )

                eligible_df = eligible_df.sort_values(
                    ['risk', 'unlock_power', 'credits'],
                    ascending=[True, False, False]
                )
            else:
                eligible_df = eligible_df.sort_values('credits', ascending=False)

            selected_codes = []
            selected_names = []
            sem_credits = 0

            for _, c in eligible_df.iterrows():
                if sem_credits + c['credits'] <= max_credits:
                    selected_codes.append(c['course_code'])
                    selected_names.append(c['course_name'])
                    sem_credits += c['credits']

                    completed_so_far.add(c['course_code'])
                    remaining_courses.remove(c['course_code'])

            total_planned_credits += sem_credits

            semester_plans.append({
                'semester': target_sem,
                'courses': selected_codes,
                'course_names': selected_names,
                'total_credits': sem_credits,
                'num_courses': len(selected_codes)
            })

            # Stop if degree completed
            if total_planned_credits >= self.total_credits:
                break

        return semester_plans

    # ------------------------------------------------------------------
    # CRITICAL PATH (CLEANED)
    # ------------------------------------------------------------------
    def get_critical_path(self, target_course, completed_courses):
        needed = nx.ancestors(self.G, target_course) - completed_courses

        if not needed:
            return []

        subgraph = self.G.subgraph(needed | {target_course})

        try:
            ordered = list(nx.topological_sort(subgraph))
            return [c for c in ordered if c != target_course]
        except nx.NetworkXUnfeasible:
            return list(needed)

    # ------------------------------------------------------------------
    # BOTTLENECK ANALYSIS (FIXED LOGIC)
    # ------------------------------------------------------------------
    def analyze_bottlenecks(self, completed_courses):
        bottlenecks = []

        for code in completed_courses:
            blocked = nx.descendants(self.G, code) - completed_courses
            if not blocked:
                continue

            info = self.courses[self.courses['course_code'] == code].iloc[0]

            bottlenecks.append({
                'course_code': code,
                'course_name': info['course_name'],
                'blocks_count': len(blocked),
                'semester': info['semester']
            })

        if not bottlenecks:
            return pd.DataFrame()

        return pd.DataFrame(bottlenecks).sort_values(
            'blocks_count', ascending=False
        ).reset_index(drop=True)

    # ------------------------------------------------------------------
    # DEGREE PROGRESS (OK)
    # ------------------------------------------------------------------
    def calculate_progress_percentage(self, completed_courses):
        completed_df = self.courses[self.courses['course_code'].isin(completed_courses)]
        completed_credits = completed_df['credits'].sum()

        completed_by_sem = completed_df.groupby('semester')['credits'].sum()
        total_by_sem = self.courses.groupby('semester')['credits'].sum()

        return {
            'total_credits_completed': int(completed_credits),
            'total_credits_required': self.total_credits,
            'percentage_complete': round((completed_credits / self.total_credits) * 100, 1),
            'credits_remaining': self.total_credits - completed_credits,
            'courses_completed': len(completed_courses),
            'courses_total': len(self.courses),
            'semester_breakdown': {
                int(s): {
                    'completed': int(completed_by_sem.get(s, 0)),
                    'total': int(total_by_sem.get(s, 0))
                }
                for s in total_by_sem.index
            }
        }
