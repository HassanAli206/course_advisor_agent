"""
Data Loader Module
Loads and preprocesses all CSV data files
"""

import pandas as pd
import networkx as nx
from pathlib import Path


class DataLoader:
    """Handles loading and preprocessing of all academic data"""
    
    def __init__(self, data_dir="data"):
        """
        Initialize data loader
        
        Args:
            data_dir: Path to directory containing CSV files
        """
        self.data_dir = Path(data_dir)
        self.courses = None
        self.prereqs = None
        self.students = None
        self.student_courses = None
        self.rules = None
        self.prereq_graph = None
    
    def load_all(self):
        """Load all CSV files and create prerequisite graph"""
        print("📂 Loading data files...")
        
        # Load CSVs
        self.courses = pd.read_csv(self.data_dir / "courses.csv")
        self.prereqs = pd.read_csv(self.data_dir / "prerequisites.csv")
        self.student_courses = pd.read_csv(self.data_dir / "student_courses.csv")
        self.students = pd.read_csv(self.data_dir / "students.csv")
        
        # Load rules (might have no header)
        try:
            self.rules = pd.read_csv(self.data_dir / "curriculum_rules.csv")
        except:
            self.rules = pd.read_csv(
                self.data_dir / "curriculum_rules.csv", 
                header=None,
                names=["key", "type", "value", "description"]
            )
        
        # Standardize column names (strip whitespace, lowercase)
        for df in [self.courses, self.prereqs, self.student_courses, self.students]:
            df.columns = df.columns.str.strip().str.lower()
        
        # Rename columns for consistency
        if "semester_offered" in self.courses.columns:
            self.courses.rename(columns={"semester_offered": "semester"}, inplace=True)
        
        # Type conversions
        self.courses["credits"] = self.courses["credits"].astype(int)
        self.courses["difficulty"] = self.courses["difficulty"].astype(int)
        self.courses["semester"] = self.courses["semester"].astype(int)
        
        self.students["current_semester"] = self.students["current_semester"].astype(int)
        self.students["cgpa"] = self.students["cgpa"].astype(float)
        
        # Convert rule values to numeric where possible
        if "value" in self.rules.columns:
            self.rules["value"] = pd.to_numeric(self.rules["value"], errors="ignore")
        
        # Build prerequisite graph
        self.prereq_graph = self._build_prereq_graph()
        
        print(f"✅ Data loaded successfully!")
        print(f"   • Courses: {len(self.courses)}")
        print(f"   • Students: {len(self.students)}")
        print(f"   • Prerequisites: {len(self.prereqs)}")
        
        return self
    
    def _build_prereq_graph(self):
        """Build directed graph of course prerequisites"""
        G = nx.DiGraph()
        
        # Add edges from prerequisites
        for _, row in self.prereqs.iterrows():
            G.add_edge(row["prereq_code"], row["course_code"])
        
        # Add all courses as nodes (including isolated ones)
        G.add_nodes_from(self.courses["course_code"])
        
        return G
    
    def get_rules_dict(self):
        """Convert rules DataFrame to dictionary for easy access"""
        rules_dict = {
            "max_normal_credits": 18,
            "max_overload_credits": 21,
            "min_cgpa_overload": 3.0,
            "max_backlogs": 3,
            "total_degree_credits": 137
        }
        
        # Override with actual rules from CSV if available
        if self.rules is not None and "key" in self.rules.columns:
            for _, row in self.rules.iterrows():
                if row["key"] in rules_dict:
                    rules_dict[row["key"]] = row["value"]
        
        return rules_dict
    
    def get_student_profile(self, student_id):
        """
        Get complete profile for a student
        
        Args:
            student_id: Student ID string
            
        Returns:
            Dictionary with student info, completed courses, backlogs, etc.
        """
        # Get student record
        student = self.students[self.students["student_id"] == student_id]
        if student.empty:
            raise ValueError(f"Student {student_id} not found")
        student = student.iloc[0]
        
        # Get student's course history
        history = self.student_courses[
            self.student_courses["student_id"] == student_id
        ]
        
        # Extract course sets
        completed_courses = set(history["course_code"])
        backlogs = set(history[history["grade"].isin(['D', 'F'])]["course_code"])
        low_grades = set(history[history["grade"].isin(['C', 'D'])]["course_code"])
        
        return {
            "student_id": student_id,
            "student": student,
            "history": history,
            "completed_courses": completed_courses,
            "backlogs": backlogs,
            "low_grades": low_grades
        }
    
    def get_eligible_courses(self, completed_courses, next_semester, backlogs=None):
        """
        Get courses eligible for selection
        
        Args:
            completed_courses: Set of course codes already taken
            next_semester: Target semester number
            backlogs: Set of courses that need retake
            
        Returns:
            DataFrame of eligible courses
        """
        if backlogs is None:
            backlogs = set()
        
        eligible = []
        
        for _, course in self.courses.iterrows():
            code = course["course_code"]
            
            # Skip if already passed (not a backlog)
            if code in completed_courses and code not in backlogs:
                continue
            
            # Check prerequisites
            prereqs_needed = list(self.prereq_graph.predecessors(code))
            prereq_satisfied = all(p in completed_courses for p in prereqs_needed)
            
            # Check semester alignment or backlog
            semester_ok = (course["semester"] == next_semester) or (code in backlogs)
            
            if prereq_satisfied and semester_ok:
                eligible.append(course.to_dict())
        
        return pd.DataFrame(eligible)


# Convenience function for quick loading
def load_data(data_dir="data"):
    """
    Quick function to load all data
    
    Returns:
        Tuple of (courses, prereqs, student_courses, students, rules, prereq_graph)
    """
    loader = DataLoader(data_dir)
    loader.load_all()
    
    return (
        loader.courses,
        loader.prereqs,
        loader.student_courses,
        loader.students,
        loader.rules,
        loader.prereq_graph
    )