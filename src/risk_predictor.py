"""
Risk Predictor Module
ML-based prediction of course failure risk
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path


class CourseFailurePredictor:
    """
    Predicts the risk of failing/struggling in a course
    Uses student profile and course characteristics
    """
    
    def __init__(self):
        """Initialize the predictor with default model"""
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.trained = False
        self.feature_names = [
            'student_cgpa',
            'course_difficulty', 
            'course_credits',
            'semester_number',
            'has_prereq_failure',
            'avg_prereq_grade'
        ]
    
    def _grade_to_gpa(self, grade):
        """Convert letter grade to GPA points"""
        grade_map = {
            'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D': 1.0,
            'F': 0.0
        }
        return grade_map.get(grade, 2.0)
    
    def _grade_to_risk(self, grade):
        """Convert grade to risk score (0-1, higher = more risk)"""
        risk_map = {
            'A': 0.05, 'A-': 0.10,
            'B+': 0.15, 'B': 0.20, 'B-': 0.25,
            'C+': 0.35, 'C': 0.45, 'C-': 0.55,
            'D': 0.75,
            'F': 0.95
        }
        return risk_map.get(grade, 0.5)
    
    def generate_training_data(self, students_df, student_courses_df, courses_df, prereq_graph):
        """
        Generate training dataset from historical data
        
        Args:
            students_df: Student records
            student_courses_df: Course taking history
            courses_df: Course catalog
            prereq_graph: NetworkX graph of prerequisites
            
        Returns:
            DataFrame with features and target variable
        """
        print("🔨 Generating training data from student history...")
        
        training_data = []
        
        for _, student in students_df.iterrows():
            student_id = student["student_id"]
            student_cgpa = student["cgpa"]
            
            # Get this student's course history
            history = student_courses_df[
                student_courses_df["student_id"] == student_id
            ].copy()
            
            # Add semester_taken if not present
            if "semester_taken" not in history.columns:
                history["semester_taken"] = student["current_semester"]
            
            for _, course_record in history.iterrows():
                course_code = course_record["course_code"]
                
                # Get course info
                course_info = courses_df[courses_df["course_code"] == course_code]
                if course_info.empty:
                    continue
                course_info = course_info.iloc[0]
                
                # Calculate prerequisite-based features
                prereqs = list(prereq_graph.predecessors(course_code))
                has_prereq_failure = 0
                avg_prereq_grade = 3.0  # Default
                
                if prereqs:
                    prereq_grades = history[history["course_code"].isin(prereqs)]["grade"]
                    if not prereq_grades.empty:
                        has_prereq_failure = int(any(g in ['D', 'F'] for g in prereq_grades))
                        avg_prereq_grade = np.mean([self._grade_to_gpa(g) for g in prereq_grades])
                
                # Create feature vector
                features = {
                    'student_cgpa': student_cgpa,
                    'course_difficulty': course_info['difficulty'],
                    'course_credits': course_info['credits'],
                    'semester_number': course_record['semester_taken'],
                    'has_prereq_failure': has_prereq_failure,
                    'avg_prereq_grade': avg_prereq_grade,
                    'risk_score': self._grade_to_risk(course_record['grade'])
                }
                
                training_data.append(features)
        
        df = pd.DataFrame(training_data)
        print(f"✅ Generated {len(df)} training samples")
        
        return df
    
    def train(self, students_df, student_courses_df, courses_df, prereq_graph):
        """
        Train the risk prediction model
        
        Args:
            students_df: Student records
            student_courses_df: Course history
            courses_df: Course catalog
            prereq_graph: Prerequisite graph
        """
        # Generate training data
        df = self.generate_training_data(
            students_df, student_courses_df, courses_df, prereq_graph
        )
        
        if len(df) < 10:
            print("⚠️ Not enough training data, using heuristic model")
            self.trained = False
            return
        
        # Prepare features and target
        X = df[self.feature_names]
        y = df['risk_score']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        print("🎓 Training risk prediction model...")
        self.model.fit(X_scaled, y)
        self.trained = True
        
        # Calculate training performance
        train_pred = self.model.predict(X_scaled)
        mae = np.mean(np.abs(train_pred - y))
        
        print(f"✅ Model trained successfully!")
        print(f"   • Training MAE: {mae:.3f}")
        print(f"   • Samples: {len(df)}")
    
    def predict_risk(self, student_cgpa, course_difficulty, course_credits,
                     semester_number, has_prereq_failure=0, avg_prereq_grade=3.0):
        """
        Predict risk score for a course
        
        Args:
            student_cgpa: Student's current CGPA
            course_difficulty: Course difficulty (1-10)
            course_credits: Course credit hours
            semester_number: Target semester
            has_prereq_failure: 1 if student failed any prerequisite
            avg_prereq_grade: Average GPA in prerequisite courses
            
        Returns:
            Risk score between 0-1 (0=low risk, 1=high risk)
        """
        if not self.trained:
            # Fallback heuristic if model not trained
            risk = 0.3 + (course_difficulty / 20) - (student_cgpa / 8)
            return np.clip(risk, 0, 1)
        
        # Prepare features
        features = np.array([[
            student_cgpa,
            course_difficulty,
            course_credits,
            semester_number,
            has_prereq_failure,
            avg_prereq_grade
        ]])
        
        # Scale and predict
        features_scaled = self.scaler.transform(features)
        risk = self.model.predict(features_scaled)[0]
        
        # Clip to valid range
        return np.clip(risk, 0, 1)
    
    def predict_batch(self, courses_df, student_profile, prereq_graph, next_semester):
        """
        Predict risk for multiple courses at once
        
        Args:
            courses_df: DataFrame of courses to evaluate
            student_profile: Dict with student info
            prereq_graph: Prerequisite graph
            next_semester: Target semester number
            
        Returns:
            Dictionary mapping course_code to risk score
        """
        risk_scores = {}
        student = student_profile['student']
        history = student_profile['history']
        
        for _, course in courses_df.iterrows():
            code = course['course_code']
            
            # Check prerequisite failures
            prereqs = list(prereq_graph.predecessors(code))
            has_prereq_failure = 0
            avg_prereq_grade = 3.0
            
            if prereqs:
                prereq_records = history[history['course_code'].isin(prereqs)]
                if not prereq_records.empty:
                    has_prereq_failure = int(
                        any(g in ['D', 'F'] for g in prereq_records['grade'])
                    )
                    avg_prereq_grade = np.mean([
                        self._grade_to_gpa(g) for g in prereq_records['grade']
                    ])
            
            # Predict risk
            risk = self.predict_risk(
                student['cgpa'],
                course['difficulty'],
                course['credits'],
                next_semester,
                has_prereq_failure,
                avg_prereq_grade
            )
            
            risk_scores[code] = risk
        
        return risk_scores
    
    def save(self, filepath="models/risk_predictor.pkl"):
        """Save trained model to disk"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'trained': self.trained,
            'feature_names': self.feature_names
        }, filepath)
        
        print(f"💾 Model saved to {filepath}")
    
    def load(self, filepath="models/risk_predictor.pkl"):
        """Load trained model from disk"""
        data = joblib.load(filepath)
        
        self.model = data['model']
        self.scaler = data['scaler']
        self.trained = data['trained']
        self.feature_names = data['feature_names']
        
        print(f"📂 Model loaded from {filepath}")
        return self