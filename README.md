# Intelligent Academic Advisor System

## 🎓 Overview

An **AI-powered academic advising system** for Air University's BS Computer Science program. Uses **machine learning** for risk prediction and **mathematical optimization** for course selection.

### Key Features

✅ **ML-Based Risk Prediction** - Predicts likelihood of failing courses  
✅ **Optimization-Based Selection** - PuLP linear programming for optimal recommendations  
✅ **Multi-Semester Planning** - Plans graduation path 4 semesters ahead  
✅ **Baseline Comparison** - Evaluates against random/greedy algorithms  
✅ **Explainable AI** - Clear explanations for every recommendation  
✅ **Interactive CLI** - User-friendly command-line interface  

---

## 📁 Project Structure

```
AGENT/
├── data/                          # Academic data (CSV files)
│   ├── courses.csv
│   ├── prerequisites.csv
│   ├── students.csv
│   ├── student_courses.csv
│   └── curriculum_rules.csv
├── models/                        # Trained ML models
│   └── risk_predictor.pkl
├── src/                           # Source code modules
│   ├── __init__.py
│   ├── data_loader.py            # Data loading & preprocessing
│   ├── risk_predictor.py         # ML failure prediction
│   ├── optimizer.py              # PuLP optimization
│   ├── multi_semester_planner.py # Graduation planning
│   ├── evaluator.py              # Baseline comparison
│   └── explanation_generator.py  # Human-readable explanations
├── output/                        # Generated recommendations
├── academic_advisor.ipynb         # Main Jupyter notebook
├── advisor_cli.py                 # Command-line interface
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

---

## 🚀 Installation

### 1. Clone or Download Project

```bash
cd AGENT
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# Activate:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 💻 Usage

### Option 1: Jupyter Notebook (Recommended for Development)

```bash
jupyter notebook academic_advisor.ipynb
```

Run cells sequentially to:
- Load data
- Train risk model
- Generate recommendations
- View comparisons
- Export results

### Option 2: Command-Line Interface

```bash
python advisor_cli.py
```

Interactive menu to:
1. Select student
2. Generate recommendations
3. View multi-semester plans
4. Compare alternatives

---

## 📊 How It Works

### 1. **Data Loading**
- Loads courses, students, prerequisites from CSV
- Builds prerequisite dependency graph using NetworkX

### 2. **Risk Prediction (ML)**
- Trains Gradient Boosting model on historical grades
- Features: CGPA, course difficulty, credits, prerequisite performance
- Predicts failure probability (0-1) for each course

### 3. **Optimization (PuLP)**
- Formulates course selection as linear programming problem
- **Objective:** Maximize progress, clear backlogs, minimize risk
- **Constraints:** Credit limits, prerequisites, retake limits
- **Adaptive Weights:** Automatically adjusts based on student CGPA/situation

### 4. **Multi-Semester Planning**
- Plans 4 semesters ahead using greedy algorithm
- Estimates graduation semester
- Identifies bottleneck courses blocking progress

### 5. **Evaluation**
- Compares against baselines: Random, Greedy (Credits), Greedy (Easy)
- Calculates quality metrics: credits, backlogs cleared, risk, workload
- Proves system superiority with quantitative evidence

### 6. **Explanation**
- Generates human-readable explanations for each course
- Risk-based study advice (form study groups, tutoring, etc.)
- Strategic semester planning advice

---

## 🎯 Key Algorithms

### Risk Prediction Model

```python
Features:
- student_cgpa
- course_difficulty
- course_credits  
- semester_number
- has_prereq_failure
- avg_prereq_grade

Model: Gradient Boosting Regressor
Output: Risk score (0-1)
```

### Optimization Objective Function

```
Maximize:
  w_progress × credits_earned
  + w_retake × backlogs_cleared
  - w_difficulty × course_difficulty
  - w_risk × predicted_risk

Subject to:
  total_credits ≤ max_credits (18 or 21)
  prerequisites satisfied
  retakes_per_semester ≤ 3
```

### Adaptive Weights

Automatically adjusts based on:
- **CGPA < 2.0:** Focus heavily on retakes (w_retake = 50)
- **CGPA ≥ 3.5:** Optimize for progress (w_progress = 15)
- **Many backlogs:** Critical retake priority (w_retake = 60)
- **Final year:** Push to graduation (w_progress = 20)

---

## 📈 Example Results

### Sample Recommendation Output

```
🎯 RECOMMENDATION SUMMARY FOR CS2025-001
============================================================
Student Status: Good (CGPA: 2.80)
Current Semester: 4
Backlogs: 1 course(s)

📚 RECOMMENDED LOAD:
   • Total Credits: 18/18
   • Number of Courses: 6
   • Backlogs Cleared: 1

📊 WORKLOAD ANALYSIS:
   • Average Difficulty: 5.2/10
   • Risk Level: Moderate (32%)

💡 STRATEGIC ADVICE:
   • Clearing backlogs is your top priority this semester
   • Prioritize consistent study habits and time management
   • High-risk courses detected - form study groups early
```

### Baseline Comparison

```
Method              Credits  Backlogs  Risk    Quality
─────────────────────────────────────────────────────
Our System             18       1      0.32     47.5  ✓ BEST
Random Selection       15       0      0.38     35.2
Greedy (Max Credits)   18       0      0.41     42.1
Greedy (Easiest)       16       1      0.25     41.8
```

---

## 🧪 Testing

### Test Different Students

In notebook Cell 6, change:
```python
selected_student_id = "CS2025-002"  # Try different IDs
```

### Add More Students

Add rows to `data/students.csv` and `data/student_courses.csv`

### Modify Optimization Weights

In `src/optimizer.py`, adjust `calculate_adaptive_weights()`

---

## 🎓 Academic Rigor

### What Makes This a Strong AI Project?

1. **Multiple AI Techniques**
   - Machine Learning (Gradient Boosting)
   - Optimization (Linear Programming)
   - Planning (Multi-semester lookahead)
   - Evaluation (Baseline comparison)

2. **Quantitative Validation**
   - Compares against 3 baseline methods
   - Calculates quality metrics
   - Proves superiority with data

3. **Real-World Application**
   - Solves actual student problem
   - Follows university rules
   - Explainable recommendations

4. **Software Engineering**
   - Modular architecture
   - Reusable components
   - Clean code structure
   - Comprehensive documentation

---

## 🔧 Customization

### Add New Academic Rules

Edit `data/curriculum_rules.csv`:
```csv
max_normal_credits,constraint,18,Maximum credits per semester
min_cgpa_overload,constraint,3.0,Minimum CGPA for overload
```

### Modify Risk Thresholds

In `src/explanation_generator.py`:
```python
self.risk_thresholds = {
    'very_high': 0.7,  # Adjust these
    'high': 0.5,
    'moderate': 0.3,
    'low': 0.15
}
```

### Change Optimization Priorities

In `src/optimizer.py`, modify weights in `calculate_adaptive_weights()`

---

## 📝 Report Generation

Recommendations are auto-exported to `output/` folder:

```
output/
├── recommendation_CS2025-001_sem5.csv
└── report_CS2025-001_sem5.txt
```

Use these for:
- Academic advisor meetings
- Project demonstrations
- Documentation

---

## 🐛 Troubleshooting

### Issue: "No module named 'src'"

**Solution:**
```bash
# Make sure you're in project root directory
cd AGENT
python advisor_cli.py
```

### Issue: "Model file not found"

**Solution:** Run notebook Cell 4 to train model first, or:
```bash
python -c "from src.data_loader import *; from src.risk_predictor import *; loader = DataLoader(); loader.load_all(); model = CourseFailurePredictor(); model.train(loader.students, loader.student_courses, loader.courses, loader.prereq_graph); model.save()"
```

### Issue: PuLP solver not working

**Solution:**
```bash
pip install pulp --upgrade
```

---

## 📚 Dependencies

Core libraries:
- **pandas** - Data manipulation
- **numpy** - Numerical computing
- **scikit-learn** - Machine learning
- **PuLP** - Linear programming
- **networkx** - Graph analysis
- **matplotlib** - Visualization
- **tabulate** - Terminal tables

---

## 🎯 Future Enhancements

Potential improvements:
- [ ] Deep learning for risk prediction
- [ ] Course schedule conflict detection
- [ ] Professor rating integration
- [ ] Web interface (Flask/Django)
- [ ] Real-time university portal integration
- [ ] Collaborative filtering for recommendations
- [ ] A/B testing framework

---

## 👨‍💻 Author

Your Name  
BS Computer Science  
Air University  

**Project:** Semester Project - Artificial Intelligence Course  
**Supervisor:** [Advisor Name]  
**Year:** 2024-2025

---

## 📄 License

Academic project for educational purposes.  
Air University © 2024-2025

---

## 🙏 Acknowledgments

- Air University for curriculum data
- PuLP library developers
- scikit-learn community
- Python data science ecosystem

---

## 📞 Support

For questions or issues:
1. Check this README
2. Review code comments
3. Test with provided sample data
4. Contact project author

---

**Made with 💙 for better academic advising**