"""
Generate rich synthetic hospital records and seed the SQLite database.
Matches Slide 3, 9, 10, 14, 15, 16 test cases.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "hospital.db"
JSON_PATH = DATA_DIR / "synthetic_hospital_data.json"

PATIENTS = [
    {
        "patient_id": "P-1042",
        "full_name": "Eleanor Vance",
        "dob": "1968-05-14",
        "gender": "Female",
        "phone_number": "+1-555-0142",
        "home_address": "742 Evergreen Terrace, Springfield",
        "national_id": "987-65-4321",
        "insurance_id": "INS-CARD-8812",
        "department": "Cardiology",
        "ward": "Ward 3",
        "bed_number": "3B",
        "diagnosis": "Hypertension, stage 2; Mild aortic stenosis",
        "allergies": "Penicillin, Sulfa drugs",
        "active_medications": "Lisinopril 20mg daily, Amlodipine 5mg daily",
        "vital_signs": "BP 142/88 mmHg, HR 74 bpm, SpO2 98%",
        "billing_balance": "$1,450.00",
        "appointment_status": "Admitted - Inpatient",
        "attending_doctor_id": "DR_302",
        "assigned_nurse_id": "RN_201",
        "clinical_notes": [
            {
                "note_id": "CN-1042-1",
                "category": "full_medical_record",
                "title": "Cardiology Inpatient Progress Note",
                "content": "Patient admitted with stage 2 hypertension and dyspnea on exertion. Echocardiogram reveals mild aortic valve thickening without hemodynamically critical obstruction. Recommended ACE inhibitor dose titration. Avoid beta-blockers due to mild reactive airway history.",
                "date": "2026-11-18"
            },
            {
                "note_id": "CN-1042-2",
                "category": "full_medical_record",
                "title": "Echocardiogram Imaging Findings",
                "content": "Left ventricular ejection fraction estimated at 55-60%. Mild concentric LVH. No mural thrombus or pericardial effusion.",
                "date": "2026-11-17"
            }
        ]
    },
    {
        "patient_id": "P-2210",
        "full_name": "Marcus Sterling",
        "dob": "1975-11-22",
        "gender": "Male",
        "phone_number": "+1-555-0221",
        "home_address": "12 Baker Street, Springfield",
        "national_id": "456-78-1234",
        "insurance_id": "INS-CARD-9921",
        "department": "Cardiology",
        "ward": "Ward 3",
        "bed_number": "3C",
        "diagnosis": "Paroxysmal Atrial Fibrillation",
        "allergies": "Aspirin",
        "active_medications": "Metoprolol Succinate 50mg daily, Apixaban 5mg BID",
        "vital_signs": "BP 128/82 mmHg, HR 82 bpm (irregular), SpO2 97%",
        "billing_balance": "$820.00",
        "appointment_status": "Admitted - Inpatient",
        "attending_doctor_id": "DR_302",
        "assigned_nurse_id": "RN_201",
        "clinical_notes": [
            {
                "note_id": "CN-2210-1",
                "category": "full_medical_record",
                "title": "Electrophysiology Consult Note",
                "content": "Patient presents with palpitations lasting 4 hours. 12-lead ECG confirmed atrial fibrillation with rapid ventricular response. Spontaneous cardioversion occurred 2 hours post rate-control initiation.",
                "date": "2026-11-15"
            }
        ]
    },
    {
        "patient_id": "P-3307",
        "full_name": "Sophia Thorne",
        "dob": "1983-02-09",
        "gender": "Female",
        "phone_number": "+1-555-0330",
        "home_address": "88 Elm Street, Oakville",
        "national_id": "234-56-7890",
        "insurance_id": "INS-ONCO-4410",
        "department": "Oncology",
        "ward": "ICU",
        "bed_number": "ICU-4",
        "diagnosis": "Acute Myeloid Leukemia (AML) in induction phase",
        "allergies": "No known drug allergies (NKDA)",
        "active_medications": "Cytarabine, Daunorubicin, Ondansetron 8mg IV",
        "vital_signs": "BP 110/68 mmHg, HR 92 bpm, Temp 38.2 C, SpO2 96%",
        "billing_balance": "$14,200.00",
        "appointment_status": "Admitted - ICU Chemotherapy",
        "attending_doctor_id": "DR_401",
        "assigned_nurse_id": "RN_204",
        "clinical_notes": [
            {
                "note_id": "CN-3307-1",
                "category": "full_medical_record",
                "title": "Hematology-Oncology Bone Marrow Biopsy Report",
                "content": "Bone marrow aspirate demonstrates 42% myeloblasts with Auer rods visible. Cytogenetics pending. High risk for neutropenic fever.",
                "date": "2026-11-10"
            },
            {
                "note_id": "CN-3307-2",
                "category": "full_medical_record",
                "title": "Oncology-Cardiology Active Referral Evaluation",
                "content": "Cardiotoxicity screening requested due to anthracycline regimen. Baseline LVEF normal. Cleared for cycle 1 with weekly cardiac biomarkers.",
                "date": "2026-11-16"
            }
        ]
    },
    {
        "patient_id": "P-4180",
        "full_name": "Daniel Hayes",
        "dob": "1991-09-30",
        "gender": "Male",
        "phone_number": "+1-555-0418",
        "home_address": "500 Lakeview Avenue, Springfield",
        "national_id": "345-67-8901",
        "insurance_id": "INS-ORTH-1123",
        "department": "Orthopedics",
        "ward": "Ward 5",
        "bed_number": "5A",
        "diagnosis": "Closed distal tibial shaft fracture, post-ORIF",
        "allergies": "Codeine",
        "active_medications": "Acetaminophen 1000mg q6h, Enoxaparin 40mg SC daily",
        "vital_signs": "BP 122/76 mmHg, HR 68 bpm, SpO2 99%",
        "billing_balance": "$3,600.00",
        "appointment_status": "Post-operative Recovery",
        "attending_doctor_id": "DR_305",
        "assigned_nurse_id": "RN_205",
        "clinical_notes": [
            {
                "note_id": "CN-4180-1",
                "category": "full_medical_record",
                "title": "Orthopedic Operative Summary",
                "content": "Open reduction internal fixation of right distal tibia completed with an intramedullary nail and interlocking screws. Excellent mechanical alignment restored. Weight-bearing protected for 6 weeks.",
                "date": "2026-10-20"
            }
        ]
    },
    {
        "patient_id": "P-5592",
        "full_name": "Grace Hopper-Smith",
        "dob": "1954-12-09",
        "gender": "Female",
        "phone_number": "+1-555-0559",
        "home_address": "33 Computing Way, Technopolis",
        "national_id": "111-22-3333",
        "insurance_id": "INS-CARD-5500",
        "department": "Cardiology",
        "ward": "Ward 3",
        "bed_number": "3D",
        "diagnosis": "Congestive Heart Failure (NYHA Class III), Ischemic Cardiomyopathy",
        "allergies": "ACE Inhibitors (causes angioedema)",
        "active_medications": "Sacubitril/Valsartan 24/26mg BID, Furosemide 40mg daily, Spironolactone 25mg daily",
        "vital_signs": "BP 118/72 mmHg, HR 66 bpm, SpO2 95% on room air",
        "billing_balance": "$2,100.00",
        "appointment_status": "Admitted - Inpatient",
        "attending_doctor_id": "DR_302",
        "assigned_nurse_id": "RN_201",
        "clinical_notes": [
            {
                "note_id": "CN-5592-1",
                "category": "full_medical_record",
                "title": "Heart Failure Clinic Assessment",
                "content": "B-type natriuretic peptide (BNP) elevated at 820 pg/mL. JVP elevated 4cm above sternal notch. Responding adequately to IV loop diuretics.",
                "date": "2026-11-18"
            }
        ]
    }
]

# Care teams linking doctors to patients
CARE_TEAMS = [
    {"doctor_id": "DR_302", "patient_id": "P-1042"},
    {"doctor_id": "DR_302", "patient_id": "P-2210"},
    {"doctor_id": "DR_302", "patient_id": "P-5592"},
    {"doctor_id": "DR_401", "patient_id": "P-3307"},
    {"doctor_id": "DR_305", "patient_id": "P-4180"}
]

# Active and expired referrals
# DR_302 has an ACTIVE referral for P-3307 (Oncology -> Cardiology consult)
# DR_302 has an EXPIRED referral for P-4180 (Orthopedics pre-op clearance expired on 2026-10-31)
REFERRALS = [
    {
        "referral_id": "REF-2026-001",
        "patient_id": "P-3307",
        "from_doctor_id": "DR_401",
        "to_doctor_id": "DR_302",
        "department": "Cardiology",
        "reason": "Cardiotoxicity clearance for anthracycline chemotherapy",
        "valid_from": "2026-11-01T00:00:00Z",
        "valid_until": "2026-12-01T23:59:59Z",  # Active!
        "status": "ACTIVE"
    },
    {
        "referral_id": "REF-2026-002",
        "patient_id": "P-4180",
        "from_doctor_id": "DR_305",
        "to_doctor_id": "DR_302",
        "department": "Cardiology",
        "reason": "Pre-operative cardiac risk stratification for ORIF surgery",
        "valid_from": "2026-10-15T00:00:00Z",
        "valid_until": "2026-10-31T23:59:59Z",  # EXPIRED! (Tests Slide 15 requirement)
        "status": "EXPIRED"
    }
]

# Predefined Hospital Personas for Demo & Tests
PERSONAS = [
    {
        "user_id": "CMO_501",
        "name": "Dr. Arthur Campbell",
        "role": "Chief Medical Officer",
        "level": 5,
        "department": "Executive / Clinical Quality",
        "assigned_ward": "ALL",
        "assigned_patients": ["ALL"],
        "description": "Hospital CMO with clinical audit oversight across all wards."
    },
    {
        "user_id": "DH_401",
        "name": "Dr. Helena Vance",
        "role": "Department Head",
        "level": 4,
        "department": "Cardiology",
        "assigned_ward": "Ward 3",
        "assigned_patients": ["P-1042", "P-2210", "P-5592"],
        "description": "Head of Cardiology overseeing all Cardiology ward patients."
    },
    {
        "user_id": "DR_302",
        "name": "Dr. Rohit Sharma",
        "role": "Treating Doctor",
        "level": 3,
        "department": "Cardiology",
        "assigned_ward": "Ward 3",
        "assigned_patients": ["P-1042", "P-2210", "P-5592"],
        "description": "Attending Cardiologist for P-1042, P-2210, and active referral P-3307."
    },
    {
        "user_id": "RN_201",
        "name": "Nurse Sarah Connor",
        "role": "Nurse",
        "level": 2,
        "department": "Cardiology",
        "assigned_ward": "Ward 3",
        "assigned_patients": ["P-1042", "P-2210", "P-5592"],
        "description": "Ward 3 bedside nurse. Allowed general clinical details, personal IDs masked."
    },
    {
        "user_id": "FD_101",
        "name": "Alex Jenkins",
        "role": "Front Desk / Billing Staff",
        "level": 1,
        "department": "Patient Administration",
        "assigned_ward": "Admissions Desk",
        "assigned_patients": ["TASK_BASED"],
        "description": "Front desk clerk. Allowed appointment and billing details only."
    },
    {
        "user_id": "SYS_999",
        "name": "Root System Admin",
        "role": "System Administrator",
        "level": 0,
        "department": "IT Operations",
        "assigned_ward": "Data Center",
        "assigned_patients": [],
        "description": "Control panel manager. Zero access to patient clinical or identifier data."
    }
]


def init_db():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE patients (
        patient_id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        dob TEXT NOT NULL,
        gender TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        home_address TEXT NOT NULL,
        national_id TEXT NOT NULL,
        insurance_id TEXT NOT NULL,
        department TEXT NOT NULL,
        ward TEXT NOT NULL,
        bed_number TEXT NOT NULL,
        diagnosis TEXT NOT NULL,
        allergies TEXT NOT NULL,
        active_medications TEXT NOT NULL,
        vital_signs TEXT NOT NULL,
        billing_balance TEXT NOT NULL,
        appointment_status TEXT NOT NULL,
        attending_doctor_id TEXT NOT NULL,
        assigned_nurse_id TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE clinical_notes (
        note_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        date TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    );
    """)

    cur.execute("""
    CREATE TABLE care_teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id TEXT NOT NULL,
        patient_id TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE referrals (
        referral_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        from_doctor_id TEXT NOT NULL,
        to_doctor_id TEXT NOT NULL,
        department TEXT NOT NULL,
        reason TEXT NOT NULL,
        valid_from TEXT NOT NULL,
        valid_until TEXT NOT NULL,
        status TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE personas (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        level INTEGER NOT NULL,
        department TEXT NOT NULL,
        assigned_ward TEXT NOT NULL,
        assigned_patients TEXT NOT NULL,
        description TEXT NOT NULL
    );
    """)

    # Populate Patients
    for p in PATIENTS:
        cur.execute("""
        INSERT INTO patients VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            p["patient_id"], p["full_name"], p["dob"], p["gender"],
            p["phone_number"], p["home_address"], p["national_id"], p["insurance_id"],
            p["department"], p["ward"], p["bed_number"], p["diagnosis"],
            p["allergies"], p["active_medications"], p["vital_signs"],
            p["billing_balance"], p["appointment_status"], p["attending_doctor_id"],
            p["assigned_nurse_id"]
        ))
        for note in p.get("clinical_notes", []):
            cur.execute("""
            INSERT INTO clinical_notes VALUES (?,?,?,?,?,?)
            """, (
                note["note_id"], p["patient_id"], note["category"],
                note["title"], note["content"], note["date"]
            ))

    # Populate Care Teams
    for ct in CARE_TEAMS:
        cur.execute("INSERT INTO care_teams (doctor_id, patient_id) VALUES (?,?)", (ct["doctor_id"], ct["patient_id"]))

    # Populate Referrals
    for ref in REFERRALS:
        cur.execute("""
        INSERT INTO referrals VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            ref["referral_id"], ref["patient_id"], ref["from_doctor_id"], ref["to_doctor_id"],
            ref["department"], ref["reason"], ref["valid_from"], ref["valid_until"], ref["status"]
        ))

    # Populate Personas
    for per in PERSONAS:
        cur.execute("""
        INSERT INTO personas VALUES (?,?,?,?,?,?,?,?)
        """, (
            per["user_id"], per["name"], per["role"], per["level"],
            per["department"], per["assigned_ward"], json.dumps(per["assigned_patients"]),
            per["description"]
        ))

    conn.commit()
    conn.close()

    # Save JSON data dump for easy inspection
    full_data = {
        "patients": PATIENTS,
        "care_teams": CARE_TEAMS,
        "referrals": REFERRALS,
        "personas": PERSONAS
    }
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=2)

    print(f"Initialized SQLite hospital DB at {DB_PATH}")
    print(f"Generated JSON dataset at {JSON_PATH}")


if __name__ == "__main__":
    init_db()
