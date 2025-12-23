#!/usr/bin/env python3
"""
Academic Advisor CLI
Command-line interface for course recommendations
HARDENED VERSION (Feasibility-safe, Final Year Courses)
"""

import sys
from pathlib import Path
from tabulate import tabulate
import os

# Import our modules
from src.data_loader import DataLoader
from src.risk_predictor import CourseFailurePredictor
from src.optimizer import CourseOptimizer
from src.multi_semester_planner import MultiSemesterPlanner
from src.evaluator import AdvisorEvaluator
from src.explanation_generator import ExplanationGenerator


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print application header"""
    print("\n" + "="*70)
    print("🎓 INTELLIGENT ACADEMIC ADVISOR SYSTEM")
    print("   Air University - BS Computer Science")
    print("   Optimization-Based Course Recommendation with ML Risk Prediction")
    print("="*70 + "\n")


def load_system():
    """Load all system components"""
    print("📂 Loading system...")
    
    # Load data
    loader = DataLoader("data")
    loader.load_all()
    
    # Initialize components
    rules_dict = loader.get_rules_dict()
    
    # Load or train risk model
    risk_model = CourseFailurePredictor()
    model_path = Path("models/risk_predictor.pkl")
    
    if model_path.exists():
        print("📂 Loading trained risk model...")
        risk_model.load(model_path)
    else:
        print("🎓 Training new risk model...")
        risk_model.train(
            loader.students,
            loader.student_courses,
            loader.courses,
            loader.prereq_graph
        )
        risk_model.save(model_path)
    
    optimizer = CourseOptimizer(rules_dict)
    planner = MultiSemesterPlanner(loader.courses, loader.prereq_graph, rules_dict)
    evaluator = AdvisorEvaluator(loader.courses, rules_dict)
    explainer = ExplanationGenerator()
    
    print("✅ System loaded successfully!\n")
    
    return loader, risk_model, optimizer, planner, evaluator, explainer, rules_dict


def select_student(loader):
    """Interactive student selection"""
    students = loader.students
    
    print("👥 Available Students:\n")
    for i, row in students.iterrows():
        print(f"  {i+1}. {row['student_id']} - "
              f"CGPA: {row['cgpa']:.2f}, "
              f"Semester: {row['current_semester']}")
    
    while True:
        try:
            choice = input(f"\nSelect student (1-{len(students)}): ").strip()
            idx = int(choice) - 1
            
            if 0 <= idx < len(students):
                return students.iloc[idx]['student_id']
            else:
                print(f"❌ Please enter a number between 1 and {len(students)}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)


def show_student_profile(student_profile):
    """Display student profile summary"""
    print("\n" + "="*70)
    print(f"📋 STUDENT PROFILE: {student_profile['student_id']}")
    print("="*70)
    
    student = student_profile['student']
    
    print(f"\n  CGPA: {student['cgpa']:.2f}")
    print(f"  Current Semester: {student['current_semester']}")
    print(f"  Completed Courses: {len(student_profile['completed_courses'])}")
    print(f"  Backlogs (D/F): {len(student_profile['backlogs'])}")
    
    if student_profile['backlogs']:
        print(f"    → {', '.join(sorted(student_profile['backlogs']))}")
    
    if student_profile['low_grades']:
        print(f"  Low Grades (C): {len(student_profile['low_grades'])}")
        print(f"    → {', '.join(sorted(student_profile['low_grades']))}")
    
    input("\nPress Enter to continue...")


def generate_recommendation(loader, risk_model, optimizer, explainer,
                           student_profile, show_comparison=True):
    """Generate and display recommendation"""
    
    # Correct semester handling: use target semester = current + 1
    target_semester = student_profile['student']['current_semester'] + 1
    student_profile['target_semester'] = target_semester
    
    print(f"\n🔍 Finding eligible courses for Semester {target_semester}...")
    
    # Get eligible courses up to the target semester (includes previous missed courses)
    eligible_df = loader.get_eligible_courses(
        student_profile['completed_courses'],
        target_semester,
        student_profile['backlogs']
    )
    
    if eligible_df.empty:
        print("❌ No eligible courses found for next semester!")
        return None, None
    
    print(f"✅ Found {len(eligible_df)} eligible courses")
    
    # Predict risks
    print("🔮 Predicting course failure risks...")
    risk_scores = risk_model.predict_batch(
        eligible_df,
        student_profile,
        loader.prereq_graph,
        target_semester
    )
    
    # Generate recommendation
    print("⚙️ Optimizing course selection...")
    recommended_df, metadata = optimizer.recommend(
        eligible_df,
        student_profile,
        risk_scores=risk_scores
    )
    
    if recommended_df.empty:
        print(f"❌ Could not generate recommendation: {metadata.get('status', 'unknown')}")
        input("\nPress Enter to continue...")
        return None, None
    
    # Display full report
    report = explainer.generate_full_report(
        recommended_df,
        student_profile,
        metadata
    )
    
    print(report)
    
    return recommended_df, metadata


def show_multi_semester_plan(planner, student_profile, risk_model):
    """Display multi-semester graduation plan"""
    print("\n" + "="*70)
    print("🗓️ MULTI-SEMESTER GRADUATION PLAN")
    print("="*70 + "\n")
    
    # Generate plan
    future_plan = planner.plan_graduation_path(
        student_profile,
        student_profile['completed_courses'],
        num_semesters=4,
        risk_predictor=risk_model
    )
    
    # Estimate graduation
    grad_sem = planner.estimate_graduation_semester(
        student_profile,
        student_profile['completed_courses']
    )
    
    print(f"🎓 Estimated Graduation: Semester {grad_sem}\n")
    
    # Display each semester
    for plan in future_plan:
        print(f"📅 Semester {plan['semester']} - {plan['total_credits']} credits")
        print("-" * 60)
        
        if plan['courses']:
            for code in plan['courses'][:10]:  # Show up to 10 courses
                course_name = planner.courses[
                    planner.courses['course_code'] == code
                ]['course_name'].values[0]
                print(f"   • {code}: {course_name}")
            
            if len(plan['courses']) > 10:
                print(f"   ... and {len(plan['courses']) - 10} more courses")
        else:
            print(f"   {plan.get('note', 'No courses planned')}")
        
        print()
    
    # Progress bar
    progress = planner.calculate_progress_percentage(student_profile['completed_courses'])
    
    print(f"📊 Degree Progress:")
    print(f"   Credits: {progress['total_credits_completed']}/{progress['total_credits_required']}")
    print(f"   Completion: {progress['percentage_complete']:.1f}%")
    
    # Visual progress bar
    bar_length = 40
    filled = int(bar_length * progress['percentage_complete'] / 100)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f"   [{bar}] {progress['percentage_complete']:.1f}%")
    
    input("\nPress Enter to continue...")


def show_alternatives(optimizer, explainer, eligible_df, student_profile, risk_scores):
    """Show alternative recommendations"""
    print("\n" + "="*70)
    print("🔀 ALTERNATIVE RECOMMENDATIONS")
    print("="*70 + "\n")
    
    alternatives = optimizer.generate_alternatives(
        eligible_df,
        student_profile,
        risk_scores,
        num_alternatives=3
    )
    
    if not alternatives:
        print("❌ Could not generate alternatives")
        return
    
    for i, (alt_rec, alt_meta) in enumerate(alternatives, 1):
        print(f"\n{'─'*60}")
        print(f"Option {i}: {alt_meta['profile']}")
        print(f"{'─'*60}")
        print(f"Credits: {alt_meta['total_credits']}/{alt_meta['max_credits']}")
        print(f"Courses: {alt_meta['num_courses']}")
        print(f"Avg Risk: {alt_meta['avg_risk']:.1%}")
        print(f"Backlogs Cleared: {alt_meta['backlogs_cleared']}")
        print(f"\nCourses:")
        
        for _, course in alt_rec.iterrows():
            risk_icon = "⚠️" if course['risk_score'] > 0.5 else "✓"
            print(f"   {risk_icon} {course['course_code']}: {course['course_name']}")
    
    input("\nPress Enter to continue...")


def main_menu():
    """Main application loop"""
    try:
        # Load system
        loader, risk_model, optimizer, planner, evaluator, explainer, rules_dict = load_system()
        
        while True:
            clear_screen()
            print_header()
            
            # Select student
            student_id = select_student(loader)
            student_profile = loader.get_student_profile(student_id)
            
            # Main workflow
            while True:
                clear_screen()
                print_header()
                
                print(f"📋 Current Student: {student_id}\n")
                print("1. View Student Profile")
                print("2. Generate Course Recommendation")
                print("3. View Multi-Semester Plan")
                print("4. View Alternative Recommendations")
                print("5. Select Different Student")
                print("6. Exit")
                
                choice = input("\nSelect option (1-6): ").strip()
                
                if choice == '1':
                    clear_screen()
                    print_header()
                    show_student_profile(student_profile)
                
                elif choice == '2':
                    clear_screen()
                    print_header()
                    recommended_df, metadata = generate_recommendation(
                        loader, risk_model, optimizer, explainer, student_profile
                    )
                    input("\nPress Enter to continue...")
                
                elif choice == '3':
                    clear_screen()
                    print_header()
                    show_multi_semester_plan(planner, student_profile, risk_model)
                
                elif choice == '4':
                    clear_screen()
                    print_header()
                    next_semester = student_profile['student']['current_semester'] + 1
                    eligible_df = loader.get_eligible_courses(
                        student_profile['completed_courses'],
                        next_semester,
                        student_profile['backlogs']
                    )
                    risk_scores = risk_model.predict_batch(
                        eligible_df, student_profile,
                        loader.prereq_graph, next_semester
                    )
                    show_alternatives(optimizer, explainer, eligible_df, 
                                    student_profile, risk_scores)
                
                elif choice == '5':
                    break  # Back to student selection
                
                elif choice == '6':
                    print("\n👋 Thank you for using the Academic Advisor System!")
                    print("="*70 + "\n")
                    sys.exit(0)
                
                else:
                    input("\n❌ Invalid option. Press Enter to continue...")
    
    except KeyboardInterrupt:
        print("\n\n👋 Exiting... Goodbye!")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main_menu()
