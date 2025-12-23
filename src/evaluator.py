"""
Evaluator Module
Evaluates recommendation quality against baselines
"""

import pandas as pd
import numpy as np
from tabulate import tabulate


class AdvisorEvaluator:
    """Evaluates and compares different recommendation strategies"""
    
    def __init__(self, courses_df, rules_dict):
        """
        Initialize evaluator
        
        Args:
            courses_df: Course catalog
            rules_dict: Academic rules
        """
        self.courses = courses_df
        self.rules = rules_dict
    
    def random_baseline(self, eligible_df, max_credits, backlogs=None):
        """
        Baseline: Random valid course selection
        
        Args:
            eligible_df: Eligible courses
            max_credits: Maximum credits allowed
            backlogs: Set of backlog courses
            
        Returns:
            List of selected course codes
        """
        if backlogs is None:
            backlogs = set()
        
        selected = []
        total_credits = 0
        
        # Shuffle courses randomly
        shuffled = eligible_df.sample(frac=1).reset_index(drop=True)
        
        # Prioritize at least one backlog if exists
        if backlogs:
            backlog_courses = shuffled[shuffled['course_code'].isin(backlogs)]
            if not backlog_courses.empty:
                first_backlog = backlog_courses.iloc[0]
                selected.append(first_backlog['course_code'])
                total_credits += first_backlog['credits']
        
        # Add random courses until credit limit
        for _, course in shuffled.iterrows():
            if course['course_code'] in selected:
                continue
            
            if total_credits + course['credits'] <= max_credits:
                selected.append(course['course_code'])
                total_credits += course['credits']
        
        return selected
    
    def greedy_credits_baseline(self, eligible_df, max_credits, backlogs=None):
        """
        Baseline: Greedily select highest credit courses
        
        Args:
            eligible_df: Eligible courses
            max_credits: Maximum credits
            backlogs: Backlog courses
            
        Returns:
            List of selected course codes
        """
        if backlogs is None:
            backlogs = set()
        
        # Sort by credits (descending)
        sorted_df = eligible_df.sort_values('credits', ascending=False).reset_index(drop=True)
        
        selected = []
        total_credits = 0
        
        # First, add backlogs
        for _, course in sorted_df.iterrows():
            if course['course_code'] in backlogs:
                if total_credits + course['credits'] <= max_credits:
                    selected.append(course['course_code'])
                    total_credits += course['credits']
        
        # Then add highest credit courses
        for _, course in sorted_df.iterrows():
            if course['course_code'] in selected:
                continue
            
            if total_credits + course['credits'] <= max_credits:
                selected.append(course['course_code'])
                total_credits += course['credits']
        
        return selected
    
    def greedy_easy_baseline(self, eligible_df, max_credits, backlogs=None):
        """
        Baseline: Select easiest courses (lowest difficulty)
        
        Args:
            eligible_df: Eligible courses
            max_credits: Maximum credits
            backlogs: Backlog courses
            
        Returns:
            List of selected course codes
        """
        if backlogs is None:
            backlogs = set()
        
        # Sort by difficulty (ascending)
        sorted_df = eligible_df.sort_values('difficulty', ascending=True).reset_index(drop=True)
        
        selected = []
        total_credits = 0
        
        for _, course in sorted_df.iterrows():
            if total_credits + course['credits'] <= max_credits:
                selected.append(course['course_code'])
                total_credits += course['credits']
        
        return selected
    
    def evaluate_recommendation(self, selected_codes, eligible_df, 
                               backlogs=None, low_grades=None, risk_scores=None):
        """
        Calculate quality metrics for a recommendation
        
        Args:
            selected_codes: List of selected course codes
            eligible_df: All eligible courses
            backlogs: Set of backlog courses
            low_grades: Set of low grade courses
            risk_scores: Dict of risk scores
            
        Returns:
            Dictionary of metrics
        """
        if backlogs is None:
            backlogs = set()
        if low_grades is None:
            low_grades = set()
        if risk_scores is None:
            risk_scores = {}
        
        if not selected_codes:
            return {
                'total_credits': 0,
                'num_courses': 0,
                'backlogs_cleared': 0,
                'low_grades_improved': 0,
                'avg_difficulty': 0,
                'avg_risk': 0,
                'workload_score': 0,
                'quality_score': 0
            }
        
        selected_df = eligible_df[eligible_df['course_code'].isin(selected_codes)]
        
        # Basic metrics
        total_credits = selected_df['credits'].sum()
        num_courses = len(selected_codes)
        backlogs_cleared = len(set(selected_codes) & backlogs)
        low_grades_improved = len(set(selected_codes) & low_grades)
        avg_difficulty = selected_df['difficulty'].mean()
        
        # Risk metric
        selected_risks = [risk_scores.get(code, 0.3) for code in selected_codes]
        avg_risk = np.mean(selected_risks) if selected_risks else 0.3
        
        # Workload score (difficulty * credits)
        workload = (selected_df['difficulty'] * selected_df['credits']).sum()
        
        # Overall quality score (higher is better)
        quality = (
            total_credits * 2.0 +           # Reward credits
            backlogs_cleared * 15.0 +       # Reward clearing backlogs
            low_grades_improved * 5.0 -     # Reward improving grades
            workload * 0.3 -                # Penalize high workload
            avg_risk * 20.0                 # Penalize high risk
        )
        
        return {
            'total_credits': int(total_credits),
            'num_courses': num_courses,
            'backlogs_cleared': backlogs_cleared,
            'low_grades_improved': low_grades_improved,
            'avg_difficulty': round(avg_difficulty, 2),
            'avg_risk': round(avg_risk, 3),
            'workload_score': round(workload, 1),
            'quality_score': round(quality, 1)
        }
    
    def compare_methods(self, eligible_df, recommended_codes, student_profile, 
                       max_credits, risk_scores=None):
        """
        Compare recommendation against multiple baselines
        
        Args:
            eligible_df: Eligible courses
            recommended_codes: Our system's recommendation
            student_profile: Student information
            max_credits: Credit limit
            risk_scores: Risk score dictionary
            
        Returns:
            DataFrame comparing all methods
        """
        backlogs = student_profile['backlogs']
        low_grades = student_profile['low_grades']
        
        # Generate baseline recommendations
        random_rec = self.random_baseline(eligible_df, max_credits, backlogs)
        greedy_credits_rec = self.greedy_credits_baseline(eligible_df, max_credits, backlogs)
        greedy_easy_rec = self.greedy_easy_baseline(eligible_df, max_credits, backlogs)
        
        # Evaluate all methods
        results = {
            'Our System': self.evaluate_recommendation(
                recommended_codes, eligible_df, backlogs, low_grades, risk_scores
            ),
            'Random Selection': self.evaluate_recommendation(
                random_rec, eligible_df, backlogs, low_grades, risk_scores
            ),
            'Greedy (Max Credits)': self.evaluate_recommendation(
                greedy_credits_rec, eligible_df, backlogs, low_grades, risk_scores
            ),
            'Greedy (Easiest)': self.evaluate_recommendation(
                greedy_easy_rec, eligible_df, backlogs, low_grades, risk_scores
            )
        }
        
        # Convert to DataFrame
        df = pd.DataFrame(results).T
        
        # Add ranking column
        df['rank'] = df['quality_score'].rank(ascending=False).astype(int)
        
        return df.sort_values('quality_score', ascending=False)
    
    def batch_evaluate(self, students_df, get_recommendation_func, 
                      student_courses_df, courses_df, prereq_graph):
        """
        Evaluate system performance across multiple students
        
        Args:
            students_df: All students
            get_recommendation_func: Function that generates recommendations
            student_courses_df: Course history
            courses_df: Course catalog
            prereq_graph: Prerequisite graph
            
        Returns:
            DataFrame with per-student results
        """
        results = []
        
        for _, student in students_df.iterrows():
            student_id = student['student_id']
            
            try:
                # Get student profile
                history = student_courses_df[
                    student_courses_df['student_id'] == student_id
                ]
                completed = set(history['course_code'])
                backlogs = set(history[history['grade'].isin(['D', 'F'])]['course_code'])
                
                student_profile = {
                    'student': student,
                    'completed_courses': completed,
                    'backlogs': backlogs
                }
                
                # Get recommendation
                recommended_df, metadata = get_recommendation_func(student_profile)
                
                results.append({
                    'student_id': student_id,
                    'cgpa': student['cgpa'],
                    'semester': student['current_semester'],
                    'backlogs_count': len(backlogs),
                    'recommended_credits': metadata.get('total_credits', 0),
                    'num_courses': len(recommended_df),
                    'avg_risk': metadata.get('avg_risk', 0),
                    'quality_score': metadata.get('objective_value', 0),
                    'status': metadata.get('status', 'unknown')
                })
            
            except Exception as e:
                results.append({
                    'student_id': student_id,
                    'cgpa': student['cgpa'],
                    'semester': student['current_semester'],
                    'status': f'error: {str(e)}'
                })
        
        return pd.DataFrame(results)
    
    def print_comparison_report(self, comparison_df):
        """
        Print a nicely formatted comparison report
        
        Args:
            comparison_df: DataFrame from compare_methods()
        """
        print("\n" + "="*70)
        print("📊 RECOMMENDATION QUALITY COMPARISON")
        print("="*70)
        
        print(tabulate(
            comparison_df,
            headers='keys',
            tablefmt='grid',
            floatfmt='.2f'
        ))
        
        # Highlight winner
        best_method = comparison_df.index[0]
        best_score = comparison_df.loc[best_method, 'quality_score']
        
        print(f"\n🏆 Best Method: {best_method} (Quality Score: {best_score:.1f})")
        
        if best_method == 'Our System':
            print("✅ Our system outperforms all baselines!")
        else:
            print(f"⚠️ Our system ranked #{comparison_df.loc['Our System', 'rank']}")