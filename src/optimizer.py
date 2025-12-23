"""
Optimizer Module
Course recommendation using PuLP optimization
"""

import pandas as pd
from pulp import *
import numpy as np


def calculate_adaptive_weights(student, backlogs, semester):
    """
    Calculate optimization weights based on student situation
    
    Args:
        student: Student record (Series)
        backlogs: Set of backlog courses
        semester: Current semester number
        
    Returns:
        Dictionary of weights
    """
    cgpa = student['cgpa']
    
    # Base weights
    w_progress = 10.0
    w_retake = 30.0
    w_difficulty = 2.0
    w_risk = 5.0
    
    # Adapt based on CGPA
    if cgpa < 2.0:
        # Struggling: focus on retakes, avoid difficulty
        w_retake = 50.0
        w_difficulty = 4.0
        w_progress = 5.0
        w_risk = 8.0
    elif cgpa < 2.5:
        # Below average: balance retakes and progress
        w_retake = 40.0
        w_difficulty = 3.0
        w_progress = 8.0
        w_risk = 6.0
    elif cgpa >= 3.5:
        # High performer: optimize for progress
        w_progress = 15.0
        w_retake = 20.0
        w_difficulty = 1.0
        w_risk = 2.0
    
    # Adapt based on number of backlogs
    if len(backlogs) > 3:
        w_retake = 60.0  # Critical: must clear backlogs
    elif len(backlogs) > 1:
        w_retake = 45.0
    
    # Final year push
    if semester >= 7:
        w_progress = 20.0
    
    return {
        'progress': w_progress,
        'retake': w_retake,
        'difficulty': w_difficulty,
        'risk': w_risk
    }


class CourseOptimizer:
    """Optimization-based course recommendation engine"""
    
    def __init__(self, rules_dict):
        """
        Initialize optimizer
        
        Args:
            rules_dict: Dictionary of academic rules
        """
        self.rules = rules_dict
    
    def recommend(self, eligible_df, student_profile, risk_scores=None, 
                  weights=None, custom_constraints=None):
        """
        Generate optimal course recommendation
        
        Args:
            eligible_df: DataFrame of eligible courses
            student_profile: Dict with student info
            risk_scores: Dict mapping course_code to risk score
            weights: Custom weights dict (if None, will calculate adaptive)
            custom_constraints: Additional constraints (optional)
            
        Returns:
            Tuple of (recommended_df, metadata_dict)
        """
        if eligible_df.empty:
            return pd.DataFrame(), {'status': 'no_eligible_courses'}
        
        student = student_profile['student']
        backlogs = student_profile['backlogs']
        low_grades = student_profile['low_grades']
        
        # Calculate adaptive weights if not provided
        if weights is None:
            weights = calculate_adaptive_weights(
                student, backlogs, student['current_semester']
            )
        
        # Determine credit limit
        if student['cgpa'] >= self.rules['min_cgpa_overload']:
            max_credits = self.rules['max_overload_credits']
        else:
            max_credits = self.rules['max_normal_credits']
        
        # Further reduce if low CGPA
        if student['cgpa'] < 2.0:
            max_credits = min(max_credits, 15)
        elif student['cgpa'] < 2.5:
            max_credits = min(max_credits, 16)
        
        # Create optimization model
        model = LpProblem("Course_Recommendation", LpMaximize)
        
        # Decision variables: 1 if course selected, 0 otherwise
        x = {
            row['course_code']: LpVariable(row['course_code'], cat='Binary')
            for _, row in eligible_df.iterrows()
        }
        
        # Use provided risk scores or default
        if risk_scores is None:
            risk_scores = {code: 0.3 for code in x.keys()}
        
        # Objective function: maximize weighted score
        objective_terms = []
        
        for _, row in eligible_df.iterrows():
            code = row['course_code']
            
            # Progress component (credits earned)
            progress_score = weights['progress'] * row['credits']
            
            # Retake component (prioritize backlogs)
            retake_score = 0
            if code in backlogs:
                retake_score = weights['retake'] * 10  # High priority
            elif code in low_grades:
                retake_score = weights['retake'] * 3   # Medium priority
            
            # Difficulty penalty
            difficulty_penalty = weights['difficulty'] * row['difficulty']
            
            # Risk penalty
            risk_penalty = weights['risk'] * risk_scores.get(code, 0.3) * 10
            
            # Combined score
            total_score = (progress_score + retake_score - 
                          difficulty_penalty - risk_penalty)
            
            objective_terms.append(total_score * x[code])
        
        model += lpSum(objective_terms), "Objective"
        
        # CONSTRAINT 1: Credit limit
        model += (
            lpSum(row['credits'] * x[row['course_code']] 
                  for _, row in eligible_df.iterrows()) <= max_credits,
            "Credit_Limit"
        )
        
        # CONSTRAINT 2: Maximum retakes per semester
        backlog_courses = [code for code in x.keys() if code in backlogs]
        if backlog_courses:
            model += (
                lpSum(x[code] for code in backlog_courses) <= self.rules['max_backlogs'],
                "Max_Retakes"
            )
        
        # CONSTRAINT 3: At least one course if backlogs exist
        if backlogs and len(backlog_courses) > 0:
            model += (
                lpSum(x[code] for code in backlog_courses) >= 1,
                "Min_One_Retake"
            )
        
        # Add custom constraints if provided
        if custom_constraints:
            for name, constraint in custom_constraints.items():
                model += constraint, name
        
        # Solve optimization problem
        status = model.solve(PULP_CBC_CMD(msg=0))
        
        if status != LpStatusOptimal:
            return pd.DataFrame(), {
                'status': 'no_solution',
                'solver_status': LpStatus[status]
            }
        
        # Extract selected courses
        selected_codes = [
            code for code in x.keys() if x[code].value() == 1
        ]
        
        recommended_df = eligible_df[
            eligible_df['course_code'].isin(selected_codes)
        ].copy()
        
        # Add risk scores to output
        recommended_df['risk_score'] = recommended_df['course_code'].map(risk_scores)
        
        # Calculate metadata
        total_credits = recommended_df['credits'].sum()
        backlogs_cleared = len(set(selected_codes) & backlogs)
        avg_difficulty = recommended_df['difficulty'].mean()
        avg_risk = recommended_df['risk_score'].mean()
        
        metadata = {
            'status': 'optimal',
            'weights_used': weights,
            'total_credits': int(total_credits),
            'max_credits': max_credits,
            'num_courses': len(recommended_df),
            'backlogs_cleared': backlogs_cleared,
            'avg_difficulty': round(avg_difficulty, 2),
            'avg_risk': round(avg_risk, 3),
            'objective_value': value(model.objective)
        }
        
        return recommended_df.reset_index(drop=True), metadata
    
    def generate_alternatives(self, eligible_df, student_profile, risk_scores=None, 
                             num_alternatives=3):
        """
        Generate multiple alternative recommendations with different weight profiles
        
        Args:
            eligible_df: Eligible courses
            student_profile: Student info
            risk_scores: Risk scores dict
            num_alternatives: Number of alternatives to generate
            
        Returns:
            List of (recommended_df, metadata) tuples
        """
        student = student_profile['student']
        backlogs = student_profile['backlogs']
        
        # Base weights
        base_weights = calculate_adaptive_weights(
            student, backlogs, student['current_semester']
        )
        
        alternatives = []
        
        # Option 1: Original recommendation
        rec1, meta1 = self.recommend(eligible_df, student_profile, risk_scores, base_weights)
        if not rec1.empty:
            meta1['profile'] = 'Balanced'
            alternatives.append((rec1, meta1))
        
        # Option 2: Max progress (lighter load, easier courses)
        if len(alternatives) < num_alternatives:
            light_weights = base_weights.copy()
            light_weights['progress'] = base_weights['progress'] * 0.7
            light_weights['difficulty'] = base_weights['difficulty'] * 1.5
            light_weights['risk'] = base_weights['risk'] * 1.3
            
            rec2, meta2 = self.recommend(eligible_df, student_profile, risk_scores, light_weights)
            if not rec2.empty and not rec2.equals(rec1):
                meta2['profile'] = 'Conservative (Lower Risk)'
                alternatives.append((rec2, meta2))
        
        # Option 3: Aggressive progress (max credits)
        if len(alternatives) < num_alternatives and student['cgpa'] >= 2.5:
            aggressive_weights = base_weights.copy()
            aggressive_weights['progress'] = base_weights['progress'] * 1.5
            aggressive_weights['difficulty'] = base_weights['difficulty'] * 0.7
            
            rec3, meta3 = self.recommend(eligible_df, student_profile, risk_scores, aggressive_weights)
            if not rec3.empty and not rec3.equals(rec1):
                meta3['profile'] = 'Aggressive (Max Progress)'
                alternatives.append((rec3, meta3))
        
        return alternatives