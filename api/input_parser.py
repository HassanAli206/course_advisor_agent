import re

def parse_user_input(message: str):
    """
    Extract cgpa and semester from user message
    """

    semester = None
    cgpa = None

    # semester patterns
    sem_match = re.search(r'(semester|sem)\s*(\d+)', message, re.I)
    if sem_match:
        semester = int(sem_match.group(2))

    # cgpa patterns
    cgpa_match = re.search(r'cgpa\s*(is)?\s*(\d+(\.\d+)?)', message, re.I)
    if cgpa_match:
        cgpa = float(cgpa_match.group(2))

    return {
        "semester": semester,
        "cgpa": cgpa
    }