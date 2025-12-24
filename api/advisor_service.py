import sys
import os
import pandas as pd
from api.input_parser import parse_user_input

# allow api to access src/
sys.path.append(os.path.abspath("."))

from src.data_loader import DataLoader
from src.optimizer import CourseOptimizer
from src.explanation_generator import ExplanationGenerator
from src.risk_predictor import CourseFailurePredictor


# load data once (NOT on every request)
data_loader = DataLoader("data")
data_loader.load_all()

risk_model = CourseFailurePredictor()
risk_model.load("models/risk_predictor.pkl")

rules = data_loader.get_rules_dict()
optimizer = CourseOptimizer(rules)

explainer = ExplanationGenerator()

def to_python(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, dict):
        return {k: to_python(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_python(v) for v in obj]
    return obj

def get_advice(student_id, message):
    """
    Main advisor logic:
    takes student_id → returns course recommendations
    """

    # 1️⃣ Get student profile
    parsed = parse_user_input(message)
    student_profile = data_loader.get_student_profile(student_id)
    # override with real user input
    if parsed["semester"] is not None:
        student_profile["student"]["current_semester"] = parsed["semester"]

    if parsed["cgpa"] is not None:
        student_profile["student"]["cgpa"] = parsed["cgpa"]

    # 2️⃣ Determine next semester
    current_sem = student_profile["student"]["current_semester"]
    next_semester = current_sem + 1

    # 3️⃣ Get eligible courses
    eligible_courses = data_loader.get_eligible_courses(
        completed_courses=student_profile["completed_courses"],
        next_semester=next_semester,
        backlogs=student_profile["backlogs"]
    )

    if eligible_courses.empty:
        return {
            "status": "no_courses",
            "message": "No eligible courses found"
        }

    # 4️⃣ Predict risk for each eligible course
    risk_scores = risk_model.predict_batch(
        courses_df=eligible_courses,
        student_profile=student_profile,
        prereq_graph=data_loader.prereq_graph,
        next_semester=next_semester
    )

    # 5️⃣ Optimize course selection
    recommended_df, metadata = optimizer.recommend(
        eligible_df=eligible_courses,
        student_profile=student_profile,
        risk_scores=risk_scores
    )

    if recommended_df.empty:
        return {
            "status": "no_solution",
            "message": "Could not generate optimal recommendation"
        }

    # 6️⃣ Generate explanations
    explanations = explainer.generate_course_explanations(
        recommended_df,
        student_profile,
        metadata
    )

    clean_risk_scores = {
    k: float(v) if hasattr(v, "item") else v
    for k, v in risk_scores.items()
}

    clean_metadata = to_python(metadata)

    clean_recommendations = to_python(
        recommended_df.to_dict(orient="records")
    )
    if isinstance(recommended_df, pd.DataFrame):
    # 7️⃣ Return final response
        return {
            "status": "success",
            "student_id": student_id,
            "next_semester": int(next_semester),
            "recommendations": clean_recommendations,
            "risk_scores": clean_risk_scores,
            "metadata": clean_metadata,
            "explanations": explanations
        }
    return {"error": "No recommendation generated"}