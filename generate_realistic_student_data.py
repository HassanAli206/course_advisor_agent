"""
Helper Script to Generate Realistic Student Data
Run this to create enhanced student_courses.csv with full semester history
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Grade to GPA mapping
GRADE_TO_GPA = {
    'A': 4.0, 'A-': 3.7,
    'B+': 3.3, 'B': 3.0, 'B-': 2.7,
    'C+': 2.3, 'C': 2.0, 'C-': 1.7,
    'D+': 1.3, 'D': 1.0,
    'F': 0.0
}

# Grade distribution weights (realistic for CS students)
GRADE_WEIGHTS = {
    'excellent': {'A': 0.40, 'A-': 0.30, 'B+': 0.20, 'B': 0.08, 'B-': 0.02},
    'good': {'A': 0.20, 'A-': 0.25, 'B+': 0.25, 'B': 0.20, 'B-': 0.07, 'C+': 0.03},
    'average': {'B+': 0.15, 'B': 0.30, 'B-': 0.25, 'C+': 0.15, 'C': 0.10, 'C-': 0.05},
    'struggling': {'B-': 0.10, 'C+': 0.15, 'C': 0.25, 'C-': 0.20, 'D': 0.15, 'F': 0.15}
}

def select_grade(performance_level, course_difficulty):
    """Select a grade based on student performance and course difficulty"""
    weights = GRADE_WEIGHTS[performance_level].copy()
    
    # Adjust for course difficulty
    if course_difficulty >= 8:
        # Hard course: shift grades down
        if performance_level in ['excellent', 'good']:
            # Reduce A grades, increase B grades
            if 'A' in weights:
                weights['A'] *= 0.6
                weights['B'] = weights.get('B', 0) + 0.15
    
    grades = list(weights.keys())
    probs = list(weights.values())
    
    # Normalize probabilities
    total = sum(probs)
    probs = [p/total for p in probs]
    
    return np.random.choice(grades, p=probs)

def determine_performance_level(cgpa):
    """Determine student performance level based on CGPA"""
    if cgpa >= 3.5:
        return 'excellent'
    elif cgpa >= 3.0:
        return 'good'
    elif cgpa >= 2.5:
        return 'average'
    else:
        return 'struggling'

def generate_student_history(student_id, current_semester, target_cgpa, courses_df):
    """Generate realistic course history for a student"""
    
    # Determine performance level
    performance_level = determine_performance_level(target_cgpa)
    
    history = []
    total_grade_points = 0
    total_credits = 0
    
    # Generate history semester by semester
    for sem in range(1, current_semester + 1):
        # Get courses for this semester
        sem_courses = courses_df[courses_df['semester_offered'] == sem]

        
        # Determine credit load for this semester
        if sem == 1:
            # First semester: usually full load
            target_credits = 14 + np.random.randint(0, 3)
        else:
            # Later semesters: varies by performance
            if performance_level == 'excellent':
                target_credits = 17 + np.random.randint(0, 4)
            elif performance_level == 'good':
                target_credits = 16 + np.random.randint(0, 3)
            elif performance_level == 'average':
                target_credits = 15 + np.random.randint(0, 3)
            else:
                target_credits = 14 + np.random.randint(0, 2)
        
        # Select courses for this semester
        sem_credits = 0
        for _, course in sem_courses.iterrows():
            if sem_credits + course['credits'] <= target_credits:
                grade = select_grade(performance_level, course['difficulty'])
                
                # Rare chance of failure for struggling students
                if performance_level == 'struggling' and np.random.random() < 0.15:
                    grade = 'F' if np.random.random() < 0.6 else 'D'
                
                history.append({
                    'student_id': student_id,
                    'course_code': course['course_code'],
                    'grade': grade,
                    'semester_taken': sem,
                    'credits': course['credits'],
                    'is_retake': False
                })
                
                # Calculate running GPA
                if grade != 'W':  # Withdrawal doesn't count
                    grade_points = GRADE_TO_GPA[grade] * course['credits']
                    total_grade_points += grade_points
                    total_credits += course['credits']
                
                sem_credits += course['credits']
            
            if sem_credits >= target_credits:
                break
    
    # Add some retakes for failed courses
    for record in history:
        if record['grade'] in ['F', 'D'] and np.random.random() < 0.7:
            # Student retook this course
            new_grade = select_grade(performance_level, 5)  # Assumed difficulty
            if new_grade in ['F', 'D']:
                # Make sure retake is better
                new_grade = 'C' if np.random.random() < 0.7 else 'C+'
            
            # Find when they retook it
            retake_semester = min(record['semester_taken'] + 1, current_semester)
            
            history.append({
                'student_id': student_id,
                'course_code': record['course_code'],
                'grade': new_grade,
                'semester_taken': retake_semester,
                'credits': record['credits'],
                'is_retake': True
            })
            
            # Update GPA calculation (replace old grade)
            total_grade_points -= GRADE_TO_GPA[record['grade']] * record['credits']
            total_grade_points += GRADE_TO_GPA[new_grade] * record['credits']
    
    # Calculate final CGPA
    calculated_cgpa = total_grade_points / total_credits if total_credits > 0 else 0.0
    
    # Adjust slightly to match target
    gpa_diff = target_cgpa - calculated_cgpa
    if abs(gpa_diff) > 0.3:
        # Adjust a few grades
        adjustment_needed = int(abs(gpa_diff) * 3)
        for _ in range(adjustment_needed):
            if history:
                idx = np.random.randint(0, len(history))
                if gpa_diff > 0:
                    # Need to increase GPA
                    if history[idx]['grade'] == 'B':
                        history[idx]['grade'] = 'A-'
                    elif history[idx]['grade'] == 'C':
                        history[idx]['grade'] = 'B'
                else:
                    # Need to decrease GPA
                    if history[idx]['grade'] == 'A':
                        history[idx]['grade'] = 'B+'
                    elif history[idx]['grade'] == 'B':
                        history[idx]['grade'] = 'C+'
    
    return pd.DataFrame(history)

def main():
    """Generate realistic student data"""
    
    print("📊 Generating Realistic Student Data...\n")
    
    # Load existing courses
    courses_df = pd.read_csv("data/courses.csv")
    courses_df.columns = courses_df.columns.str.strip().str.lower()
    
    # Load existing students or create new ones
    try:
        students_df = pd.read_csv("data/students.csv")
        students_df.columns = students_df.columns.str.strip().str.lower()
    except:
        print("❌ students.csv not found. Please create it first.")
        return
    
    # Generate history for each student
    all_history = []
    
    for _, student in students_df.iterrows():
        student_id = student['student_id']
        current_sem = student['current_semester']
        cgpa = student['cgpa']
        
        print(f"Generating history for {student_id} (CGPA: {cgpa:.2f}, Semester: {current_sem})")
        
        student_history = generate_student_history(
            student_id, current_sem, cgpa, courses_df
        )
        
        all_history.append(student_history)
    
    # Combine all histories
    final_df = pd.concat(all_history, ignore_index=True)
    
    # Save to CSV
    output_path = Path("data/student_courses.csv")
    final_df.to_csv(output_path, index=False)
    
    print(f"\n✅ Generated {len(final_df)} course history records")
    print(f"💾 Saved to {output_path}")
    
    # Show summary
    print("\n📊 Summary by Student:")
    for student_id in students_df['student_id']:
        student_records = final_df[final_df['student_id'] == student_id]
        backlogs = student_records[student_records['grade'].isin(['D', 'F'])]
        
        print(f"   {student_id}: {len(student_records)} courses, {len(backlogs)} backlogs")

if __name__ == "__main__":
    main()