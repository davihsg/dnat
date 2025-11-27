# Example Datasets

This directory contains example CSV files that can be used for testing asset registration in the DNAT Marketplace.

## Files

### 1. `computer_theory_grades.csv`
A dataset containing university grades for a Computer Theory course.

**Columns:**
- `student_id`: Unique identifier for each student
- `student_name`: Student's full name
- `midterm_score`: Score on midterm exam (0-100)
- `final_score`: Score on final exam (0-100)
- `project_score`: Score on project assignment (0-100)
- `total_grade`: Calculated average grade
- `grade_letter`: Letter grade (A, B, C, D, F)

**Entries:** 20 students

**Use Case:** Example dataset for testing dataset registration and access control.

### 2. `exercise_frequency.csv`
A dataset tracking exercise frequency across different activities.

**Columns:**
- `participant_id`: Unique identifier for each participant
- `participant_name`: Participant's full name
- `week`: Week number
- `soccer_sessions`: Number of soccer sessions
- `gym_sessions`: Number of gym sessions
- `running_sessions`: Number of running sessions
- `yoga_sessions`: Number of yoga sessions
- `cycling_sessions`: Number of cycling sessions
- `total_sessions`: Total exercise sessions for the week

**Entries:** 20 participants

**Use Case:** Example dataset for testing dataset registration with different data structure.

## Usage

1. Navigate to the Register Asset page in the DNAT Marketplace
2. Select "Dataset (CSV format)" as the asset type
3. Upload one of these CSV files
4. Fill in the manifest information:
   - **Name**: e.g., "Computer Theory Grades Dataset" or "Exercise Frequency Dataset"
   - **Description**: Describe the dataset content
   - **Version**: e.g., "1.0.0"
   - **Author**: Your name or organization
5. Set a price in ETH
6. Submit the registration

## Notes

- These are example datasets for testing purposes
- The data is synthetic and for demonstration only
- Both files are valid CSV format and can be used to test the registration flow

