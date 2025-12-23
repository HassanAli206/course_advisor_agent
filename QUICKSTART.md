# 🚀 Quick Start Guide

## Complete Setup in 10 Minutes

### Step 1: Create Folder Structure (1 min)

```bash
cd AGENT

# Create missing folders
mkdir models
mkdir src
mkdir output
```

### Step 2: Create All Python Files (3 min)

Copy the code from the artifacts into these files:

1. **requirements.txt** - Dependencies list
2. **src/__init__.py** - Package init (can be empty)
3. **src/data_loader.py** - Data loading module
4. **src/risk_predictor.py** - ML risk prediction
5. **src/optimizer.py** - Optimization engine
6. **src/multi_semester_planner.py** - Multi-semester planning
7. **src/evaluator.py** - Baseline evaluation
8. **src/explanation_generator.py** - Explanation generation
9. **advisor_cli.py** - CLI interface
10. **README.md** - Project documentation

### Step 3: Install Dependencies (2 min)

```bash
pip install -r requirements.txt
```

If you get errors, try:
```bash
pip install pandas numpy scikit-learn networkx pulp matplotlib seaborn tabulate ipywidgets jupyter
```

### Step 4: Test Data Loading (1 min)

```bash
python -c "from src.data_loader import DataLoader; loader = DataLoader(); loader.load_all(); print('✅ Data loaded!')"
```

### Step 5: Train Model (2 min)

```bash
python -c "
from src.data_loader import DataLoader
from src.risk_predictor import CourseFailurePredictor

loader = DataLoader()
loader.load_all()

model = CourseFailurePredictor()
model.train(loader.students, loader.student_courses, loader.courses, loader.prereq_graph)
model.save()
print('✅ Model trained!')
"
```

### Step 6: Run CLI (1 min)

```bash
python advisor_cli.py
```

**OR** Open Jupyter:

```bash
jupyter notebook
# Then open academic_advisor.ipynb
```

---

## ✅ Verification Checklist

After setup, you should have:

```
AGENT/
├── data/
│   ├── ✅ courses.csv
│   ├── ✅ prerequisites.csv
│   ├── ✅ students.csv
│   ├── ✅ student_courses.csv
│   └── ✅ curriculum_rules.csv
├── models/
│   └── ✅ risk_predictor.pkl (created after training)
├── src/
│   ├── ✅ __init__.py
│   ├── ✅ data_loader.py
│   ├── ✅ risk_predictor.py
│   ├── ✅ optimizer.py
│   ├── ✅ multi_semester_planner.py
│   ├── ✅ evaluator.py
│   └── ✅ explanation_generator.py
├── ✅ advisor_cli.py
├── ✅ requirements.txt
└── ✅ README.md
```

---

## 🎯 First Test Run

### Option A: CLI

```bash
python advisor_cli.py
```

1. Select student #1
2. Choose option 2 (Generate Recommendation)
3. View results!

### Option B: Python Script

Create `test.py`:

```python
from src.data_loader import DataLoader
from src.risk_predictor import CourseFailurePredictor
from src.optimizer import CourseOptimizer
from src.explanation_generator import ExplanationGenerator

# Load everything
loader = DataLoader()
loader.load_all()

# Load model
risk_model = CourseFailurePredictor()
risk_model.load()

# Get student
student_profile = loader.get_student_profile("CS2025-001")

# Get eligible courses
next_sem = student_profile['student']['current_semester'] + 1
eligible = loader.get_eligible_courses(
    student_profile['completed_courses'],
    next_sem,
    student_profile['backlogs']
)

# Predict risks
risks = risk_model.predict_batch(eligible, student_profile, 
                                 loader.prereq_graph, next_sem)

# Optimize
optimizer = CourseOptimizer(loader.get_rules_dict())
recommended, metadata = optimizer.recommend(
    eligible, student_profile, risks
)

# Explain
explainer = ExplanationGenerator()
report = explainer.generate_full_report(
    recommended, student_profile, metadata
)

print(report)
```

Run it:
```bash
python test.py
```

---

## 🐛 Common Issues & Fixes

### Issue 1: Import errors

```
ModuleNotFoundError: No module named 'src'
```

**Fix:**
```bash
# Make sure you're in AGENT directory
pwd  # Should show /path/to/AGENT

# Try:
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python advisor_cli.py
```

### Issue 2: PuLP not finding solver

```
PuLP: Error: Not a valid PULP_CBC_CMD command
```

**Fix:**
```bash
pip install pulp --upgrade
```

Or use different solver in code:
```python
model.solve(PULP_CBC_CMD(msg=0))
# Change to:
model.solve()  # Uses default solver
```

### Issue 3: CSV files not found

```
FileNotFoundError: data/courses.csv
```

**Fix:**
```bash
# Check you're in right directory
ls data/  # Should show all CSV files

# If not, make sure folder structure is correct
```

---

## 📊 Quick Demo Script

Want to quickly show all features? Run this:

```python
# demo.py
from src.data_loader import DataLoader
from src.risk_predictor import CourseFailurePredictor
from src.optimizer import CourseOptimizer
from src.multi_semester_planner import MultiSemesterPlanner
from src.evaluator import AdvisorEvaluator
from src.explanation_generator import ExplanationGenerator

print("🎓 Academic Advisor Demo\n")

# 1. Load
print("1️⃣ Loading data...")
loader = DataLoader()
loader.load_all()

# 2. Train model
print("2️⃣ Training ML model...")
model = CourseFailurePredictor()
try:
    model.load()
    print("   (Loaded existing model)")
except:
    model.train(loader.students, loader.student_courses, 
                loader.courses, loader.prereq_graph)
    model.save()

# 3. Get recommendation
print("3️⃣ Generating recommendation...")
student_id = loader.students.iloc[0]['student_id']
profile = loader.get_student_profile(student_id)
next_sem = profile['student']['current_semester'] + 1

eligible = loader.get_eligible_courses(
    profile['completed_courses'], next_sem, profile['backlogs']
)
risks = model.predict_batch(eligible, profile, loader.prereq_graph, next_sem)

optimizer = CourseOptimizer(loader.get_rules_dict())
recommended, metadata = optimizer.recommend(eligible, profile, risks)

# 4. Show results
print(f"4️⃣ Results for {student_id}:")
print(f"   Credits: {metadata['total_credits']}")
print(f"   Courses: {len(recommended)}")
print(f"   Avg Risk: {metadata['avg_risk']:.1%}")

# 5. Compare baselines
print("5️⃣ Comparing with baselines...")
evaluator = AdvisorEvaluator(loader.courses, loader.get_rules_dict())
comparison = evaluator.compare_methods(
    eligible, recommended['course_code'].tolist(),
    profile, metadata['max_credits'], risks
)
print("\nComparison:")
print(comparison[['total_credits', 'quality_score']])

# 6. Multi-semester plan
print("\n6️⃣ Multi-semester plan:")
planner = MultiSemesterPlanner(loader.courses, loader.prereq_graph, 
                               loader.get_rules_dict())
future = planner.plan_graduation_path(profile, profile['completed_courses'], 3)
for plan in future:
    print(f"   Sem {plan['semester']}: {len(plan['courses'])} courses, {plan['total_credits']} credits")

print("\n✅ Demo complete!")
```

Run:
```bash
python demo.py
```

---

## 🎯 Next Steps

1. ✅ Verify setup works
2. ✅ Run demo script
3. ✅ Try CLI interface
4. ✅ Open Jupyter notebook
5. 📝 Customize for your data
6. 🎓 Present to your professor!

---

## 💡 Tips

- **Start with CLI** - Easiest to understand flow
- **Use notebook for development** - Better for experimentation
- **Check output/ folder** - Auto-generated reports are there
- **Modify one student at a time** - Test incrementally
- **Read code comments** - Everything is explained

---

## 📞 Need Help?

1. Check error message carefully
2. Verify all files exist
3. Try demo.py to isolate issue
4. Check that data CSV files are valid
5. Ensure Python 3.8+ is installed

---

**Ready to run? Start with:**

```bash
python advisor_cli.py
```

**Good luck! 🚀**