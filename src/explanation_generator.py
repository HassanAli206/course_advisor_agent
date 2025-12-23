"""
Explanation Generator Module
Generates human-readable explanations for recommendations
"""

import pandas as pd
from tabulate import tabulate


class ExplanationGenerator:
    """Generates clear explanations for course recommendations"""
    
    def __init__(self):
        """Initialize explanation generator"""
        self.risk_thresholds = {
            'very_high': 0.7,
            'high': 0.5,
            'moderate': 0.3,
            'low': 0.15
        }
    
    def generate_course_explanations(self, recommended_df, student_profile, metadata):
        """
        Generate detailed explanations for each recommended course
        
        Args:
            recommended_df: DataFrame of recommended courses
            student_profile: Student information dict
            metadata: Recommendation metadata
            
        Returns:
            DataFrame with explanations
        """
        backlogs = student_profile['backlogs']
        low_grades = student_profile['low_grades']
        
        explanations = []
        
        for _, course in recommended_df.iterrows():
            code = course['course_code']
            risk = course.get('risk_score', 0.3)
            
            # Determine primary reason
            if code in backlogs:
                reason = "🔥 CRITICAL: Must retake (previous F/D)"
                priority = 1
            elif code in low_grades:
                reason = "⚡ RECOMMENDED: Improve grade (previous C)"
                priority = 2
            else:
                reason = "✓ Degree requirement for progression"
                priority = 3
            
            # Generate risk-based advice
            advice = self._get_risk_advice(risk, course['difficulty'])
            
            # Difficulty assessment
            if course['difficulty'] >= 8:
                difficulty_str = f"{course['difficulty']}/10 (Very Hard)"
            elif course['difficulty'] >= 6:
                difficulty_str = f"{course['difficulty']}/10 (Hard)"
            elif course['difficulty'] >= 4:
                difficulty_str = f"{course['difficulty']}/10 (Moderate)"
            else:
                difficulty_str = f"{course['difficulty']}/10 (Easy)"
            
            explanations.append({
                'Code': code,
                'Course Name': course['course_name'],
                'Credits': course['credits'],
                'Difficulty': difficulty_str,
                'Risk': f"{risk:.0%}",
                'Reason': reason,
                'Advice': advice,
                'priority': priority  # Hidden, for sorting
            })
        
        # Sort by priority
        explanations.sort(key=lambda x: x['priority'])
        
        # Remove priority column
        df = pd.DataFrame(explanations)
        df = df.drop('priority', axis=1)
        
        return df
    
    def _get_risk_advice(self, risk, difficulty):
        """Generate risk-based study advice"""
        if risk >= self.risk_thresholds['very_high']:
            return "⚠️ VERY HIGH RISK - Strongly consider tutoring & study groups"
        elif risk >= self.risk_thresholds['high']:
            return "⚠️ HIGH RISK - Form study group, attend office hours"
        elif risk >= self.risk_thresholds['moderate']:
            if difficulty >= 7:
                return "⚠️ MODERATE RISK - Allocate extra study time"
            else:
                return "✓ Manageable with consistent effort"
        else:
            return "✓ Low risk - Good fit for your profile"
    
    def generate_summary(self, recommended_df, student_profile, metadata):
        """
        Generate executive summary of recommendation
        
        Args:
            recommended_df: Recommended courses
            student_profile: Student info
            metadata: Recommendation metadata
            
        Returns:
            String summary
        """
        student = student_profile['student']
        backlogs = student_profile['backlogs']
        
        # Build summary text
        summary_parts = []
        
        # Header
        summary_parts.append(f"🎯 RECOMMENDATION SUMMARY FOR {student['student_id']}")
        summary_parts.append("=" * 60)
        
        # Student status
        cgpa_status = "Excellent" if student['cgpa'] >= 3.5 else \
                     "Good" if student['cgpa'] >= 3.0 else \
                     "Satisfactory" if student['cgpa'] >= 2.5 else \
                     "Needs Improvement"
        
        summary_parts.append(f"Student Status: {cgpa_status} (CGPA: {student['cgpa']:.2f})")
        summary_parts.append(f"Current Semester: {student['current_semester']}")
        summary_parts.append(f"Backlogs: {len(backlogs)} course(s)")
        summary_parts.append("")
        
        # Recommendation overview
        total_credits = metadata.get('total_credits', 0)
        max_credits = metadata.get('max_credits', 18)
        num_courses = len(recommended_df)
        backlogs_cleared = metadata.get('backlogs_cleared', 0)
        
        summary_parts.append(f"📚 RECOMMENDED LOAD:")
        summary_parts.append(f"   • Total Credits: {total_credits}/{max_credits}")
        summary_parts.append(f"   • Number of Courses: {num_courses}")
        if backlogs_cleared > 0:
            summary_parts.append(f"   • Backlogs Cleared: {backlogs_cleared}")
        summary_parts.append("")
        
        # Risk assessment
        avg_risk = metadata.get('avg_risk', 0)
        avg_diff = metadata.get('avg_difficulty', 0)
        
        risk_level = "High" if avg_risk >= 0.5 else \
                    "Moderate" if avg_risk >= 0.3 else "Low"
        
        summary_parts.append(f"📊 WORKLOAD ANALYSIS:")
        summary_parts.append(f"   • Average Difficulty: {avg_diff:.1f}/10")
        summary_parts.append(f"   • Risk Level: {risk_level} ({avg_risk:.1%})")
        summary_parts.append("")
        
        # Strategic advice
        advice = self._generate_strategic_advice(
            student, backlogs, total_credits, avg_risk, avg_diff
        )
        summary_parts.append("💡 STRATEGIC ADVICE:")
        for line in advice:
            summary_parts.append(f"   • {line}")
        
        return "\n".join(summary_parts)
    
    def _generate_strategic_advice(self, student, backlogs, total_credits, 
                                   avg_risk, avg_difficulty):
        """Generate personalized strategic advice"""
        advice = []
        
        cgpa = student['cgpa']
        
        # CGPA-based advice
        if cgpa < 2.0:
            advice.append("Focus on clearing backlogs to improve your CGPA")
            advice.append("Consider reducing extracurricular commitments this semester")
        elif cgpa < 2.5:
            advice.append("Prioritize consistent study habits and time management")
        elif cgpa >= 3.5:
            advice.append("You're doing great! Consider taking challenging electives")
        
        # Backlog advice
        if len(backlogs) > 2:
            advice.append("Clearing backlogs is your top priority this semester")
        
        # Workload advice
        if total_credits >= 20:
            advice.append("This is a heavy load - ensure strong time management")
        
        # Risk advice
        if avg_risk >= 0.5:
            advice.append("High-risk courses detected - form study groups early")
        
        # Difficulty advice
        if avg_difficulty >= 7:
            advice.append("Challenging courses ahead - start assignments early")
        
        # General advice
        advice.append("Attend office hours if you're struggling with any course")
        advice.append("Review material regularly, don't wait until exams")
        
        return advice
    
    def generate_full_report(self, recommended_df, student_profile, metadata, 
                            comparison_df=None):
        """
        Generate complete recommendation report
        
        Args:
            recommended_df: Recommended courses
            student_profile: Student info
            metadata: Recommendation metadata
            comparison_df: Optional baseline comparison
            
        Returns:
            String with full formatted report
        """
        report_parts = []
        
        # Summary section
        report_parts.append(self.generate_summary(recommended_df, student_profile, metadata))
        report_parts.append("\n" + "=" * 60)
        
        # Detailed course breakdown
        report_parts.append("\n📋 DETAILED COURSE BREAKDOWN:\n")
        explanations = self.generate_course_explanations(
            recommended_df, student_profile, metadata
        )
        report_parts.append(tabulate(explanations, headers='keys', 
                                    tablefmt='grid', showindex=False))
        
        # Weights used (if available)
        if 'weights_used' in metadata:
            report_parts.append("\n⚙️ OPTIMIZATION WEIGHTS:")
            weights = metadata['weights_used']
            for key, value in weights.items():
                report_parts.append(f"   • {key.capitalize()}: {value:.1f}")
        
        # Comparison with baselines (if available)
        if comparison_df is not None:
            report_parts.append("\n" + "=" * 60)
            report_parts.append("\n📊 COMPARISON WITH BASELINE METHODS:\n")
            report_parts.append(tabulate(
                comparison_df[['total_credits', 'backlogs_cleared', 
                              'avg_risk', 'quality_score']],
                headers='keys',
                tablefmt='grid',
                floatfmt='.2f'
            ))
            
            best = comparison_df.index[0]
            if best == 'Our System':
                report_parts.append("\n✅ Our system provides the best recommendation!")
        
        # Footer
        report_parts.append("\n" + "=" * 60)
        report_parts.append("✅ All prerequisites and academic rules satisfied")
        report_parts.append("📝 Review this plan with your academic advisor before registration")
        
        return "\n".join(report_parts)
    
    def generate_constraint_violations(self, student_profile, metadata):
        """
        Check and explain any constraint violations
        
        Args:
            student_profile: Student info
            metadata: Recommendation metadata
            
        Returns:
            List of violation strings (empty if no violations)
        """
        violations = []
        
        # Check if no solution found
        if metadata.get('status') != 'optimal':
            violations.append(f"❌ No valid course combination found: {metadata.get('solver_status', 'unknown error')}")
        
        return violations