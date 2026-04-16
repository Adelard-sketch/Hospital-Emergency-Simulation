"""
Flask backend for Emergency Department Simulation
FULLY INTEGRATED with your Kaggle dataset
Run with: python app.py
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import numpy as np
import pandas as pd
import simpy
from scipy import stats as scipy_stats
import json
import os

app = Flask(__name__)
CORS(app)

#data loading and processing

# Try to find the CSV file
DATA_PATH = None
possible_paths = [
    "emergency-service-triage-application/data.csv",
    "data.csv",
    "../emergency-service-triage-application/data.csv"
]

for path in possible_paths:
    if os.path.exists(path):
        DATA_PATH = path
        break

if DATA_PATH is None:
    print("\nERROR: CSV data file not found!")
    print("Expected location: emergency-service-triage-application/data.csv")
    print("Please ensure the data file exists before running the simulation.\n")
    import sys
    sys.exit(1)

USE_REAL_DATA = True
print(f"Loading data from: {DATA_PATH}")

# Load and process data (exactly like your notebook)
df = pd.read_csv(DATA_PATH, sep=";", encoding="latin1")

# Rename columns (from your notebook)
df.rename(columns={
    "Group": "ed_type",
    "Sex": "sex",
    "Age": "age",
    "Patients number per hour": "patients_per_hour",
    "Arrival mode": "arrival_mode",
    "Injury": "injury",
    "Chief_complain": "chief_complaint",
    "Mental": "mental",
    "Pain": "pain",
    "NRS_pain": "nrs_pain",
    "SBP": "sbp",
    "DBP": "dbp",
    "HR": "hr",
    "RR": "rr",
    "BT": "bt",
    "Saturation": "spo2",
    "KTAS_RN": "ktas_nurse",
    "Diagnosis in ED": "diagnosis",
    "Disposition": "disposition",
    "KTAS_expert": "ktas",
    "Error_group": "error_group",
    "Length of stay_min": "los_min",
    "KTAS duration_min": "triage_duration_min",
    "mistriage": "mistriage"
}, inplace=True)

# Fix triage duration
df["triage_duration_min"] = (
    df["triage_duration_min"]
    .astype(str)
    .str.replace(",", ".", regex=False)
    .astype(float)
)

# Convert to numeric
df["los_min"] = pd.to_numeric(df["los_min"], errors="coerce")
df["patients_per_hour"] = pd.to_numeric(df["patients_per_hour"], errors="coerce")

int_cols = ["ed_type", "sex", "age", "arrival_mode", "injury", "mental", "pain",
            "ktas_nurse", "disposition", "ktas", "error_group", "mistriage"]
for col in int_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Clean vitals
vital_cols = ["sbp", "dbp", "hr", "rr", "bt", "spo2"]
for col in vital_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df.drop(columns=["spo2"], inplace=True, errors='ignore')
df["nrs_pain"] = df["nrs_pain"].fillna(0)

for col in ["sbp", "dbp", "hr", "rr", "bt"]:
    if col in df.columns:
        df[col] = df[col].fillna(df[col].median())

df["diagnosis"] = df["diagnosis"].fillna("Unknown")

# Filter LOS
df_clean = df[(df["los_min"] > 0) & (df["los_min"] <= 1440)].copy()
print(f"Data cleaned: {len(df_clean)} records")

# Map KTAS to SATS
ktas_to_sats = {1: "Red", 2: "Orange", 3: "Yellow", 4: "Green", 5: "Green"}
df_clean["sats"] = df_clean["ktas"].map(ktas_to_sats)
df_clean.loc[df_clean["disposition"] == 6, "sats"] = "Blue"

# Calculate acuity mix
ACUITY_MIX = {
    "Red": (df_clean["sats"] == "Red").mean(),
    "Orange": (df_clean["sats"] == "Orange").mean(),
    "Yellow": (df_clean["sats"] == "Yellow").mean(),
    "Green": (df_clean["sats"] == "Green").mean(),
    "Blue": (df_clean["sats"] == "Blue").mean()
}
total_prob = sum(ACUITY_MIX.values())
ACUITY_MIX = {k: v / total_prob for k, v in ACUITY_MIX.items()}

# Calculate arrival rates
rate_mean = df_clean["patients_per_hour"].mean()
hours = np.arange(24)
pdf_curve = scipy_stats.norm.pdf(hours, loc=17, scale=4)
scale_factor = rate_mean / pdf_curve.mean()
HOURLY_ARRIVAL_RATES = np.clip(pdf_curve * scale_factor, a_min=0.5, a_max=None).round(2)

# Triage time
TRIAGE_TIME_MEAN = df_clean["triage_duration_min"].mean()

# Fit service time distributions
TREATMENT_FRACTION = 0.20
DISTRIBUTIONS_TO_TEST = [scipy_stats.expon, scipy_stats.gamma, scipy_stats.lognorm]
FITTED_SERVICE_DISTRIBUTIONS = {}

for sats in ["Red", "Orange", "Yellow", "Green", "Blue"]:
    if sats == "Blue":
        data = df_clean[df_clean["disposition"] == 6]["los_min"].dropna().values
    else:
        data = df_clean[df_clean["sats"] == sats]["los_min"].dropna().values * TREATMENT_FRACTION
    
    if len(data) < 5:
        FITTED_SERVICE_DISTRIBUTIONS[sats] = ("expon", (0, 5.0))
        continue
    
    best_dist = "lognorm"
    best_p = -1
    best_params = None
    
    for dist in DISTRIBUTIONS_TO_TEST:
        try:
            params = dist.fit(data)
            d_stat, p_val = scipy_stats.kstest(data, dist.name, args=params)
            if p_val > best_p:
                best_p = p_val
                best_dist = dist.name
                best_params = params
        except:
            continue
    
    if best_params is None:
        best_params = scipy_stats.lognorm.fit(data)
    
    FITTED_SERVICE_DISTRIBUTIONS[sats] = (best_dist, best_params)

print(f"\nData processing complete!")
print(f"Total patients in dataset: {len(df_clean)}")
print(f"Acuity mix: Red={ACUITY_MIX['Red']:.1%}, Orange={ACUITY_MIX['Orange']:.1%}, Yellow={ACUITY_MIX['Yellow']:.1%}, Green={ACUITY_MIX['Green']:.1%}, Blue={ACUITY_MIX['Blue']:.1%}")
print(f"Mean arrival rate: {rate_mean:.2f} patients/hour")
print(f"Mean triage time: {TRIAGE_TIME_MEAN:.2f} minutes\n")

#simulation parameters

SATS_PRIORITY = {"Red": 1, "Orange": 2, "Yellow": 3, "Green": 4, "Blue": 5}
LWBS_PATIENCE_TRIAGE = {"Red": 2, "Orange": 10, "Yellow": 30, "Green": 60, "Blue": 999}
LWBS_PATIENCE_BAY = {"Red": 15, "Orange": 60, "Yellow": 120, "Green": 240, "Blue": 999}

STAFFING = {
    "weekday": {"triage_nurses": 3, "treatment_bays": 12},
    "weekend": {"triage_nurses": 2, "treatment_bays": 8},
}

ADMIT_PROB = {"Red": 0.70, "Orange": 0.45, "Yellow": 0.20, "Green": 0.05}


#patient class

class Patient:
    _ctr = 0
    
    def __init__(self, acuity, t):
        Patient._ctr += 1
        self.id = Patient._ctr
        self.acuity = acuity
        self.priority = SATS_PRIORITY[acuity]
        self.arrival = t
        self.triage_start = None
        self.doctor_start = None
        self.doctor_end = None
        self.departure = None
        self.lwbs = False
        self.outcome = None


#simulation function

def sample_service_time(acuity, rng):
    """Sample service time from fitted distribution"""
    dist_name, params = FITTED_SERVICE_DISTRIBUTIONS[acuity]
    dist = getattr(scipy_stats, dist_name)
    return max(1.0, float(dist.rvs(*params, random_state=int(rng.integers(0, 1e9)))))


def run_simulation(staffing_level, policy, duration_hours, seed):
    """Run one simulation replication"""
    Patient._ctr = 0
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    staff = STAFFING[staffing_level]
    
    nurses = simpy.PreemptiveResource(env, capacity=staff["triage_nurses"])
    bays = simpy.PriorityResource(env, capacity=staff["treatment_bays"])
    ft_bays = simpy.PriorityResource(env, capacity=max(1, staff["treatment_bays"] // 3))
    
    patient_log = []
    
    def select_bay(p):
        if policy == "fast_track" and p.acuity == "Green":
            return ft_bays
        if policy == "split_flow" and p.acuity in ("Yellow", "Green"):
            return ft_bays
        return bays
    
    def patient_flow(p):
        """Patient journey through ED"""
        # Triage
        triage_req = nurses.request(priority=p.priority, preempt=True)
        patience = LWBS_PATIENCE_TRIAGE[p.acuity]
        
        result = yield triage_req | env.timeout(patience)
        
        if triage_req in result:
            p.triage_start = env.now
            try:
                yield env.timeout(max(1, rng.exponential(TRIAGE_TIME_MEAN)))
            except simpy.Interrupt:
                # Patient was preempted during triage
                p.lwbs = True
                p.departure = env.now
                patient_log.append(p)
                return
            finally:
                if triage_req.triggered:
                    nurses.release(triage_req)
        else:
            p.lwbs = True
            p.departure = env.now
            patient_log.append(p)
            return
        
        # Treatment
        bay = select_bay(p)
        bay_req = bay.request(priority=p.priority)
        patience = LWBS_PATIENCE_BAY[p.acuity]
        
        result = yield bay_req | env.timeout(patience)
        
        if bay_req in result:
            p.doctor_start = env.now
            service_time = sample_service_time(p.acuity, rng)
            yield env.timeout(service_time)
            p.doctor_end = env.now
            bay.release(bay_req)
            
            # Outcome
            if p.acuity == "Blue":
                p.outcome = "deceased"
            elif p.acuity in ADMIT_PROB and rng.random() < ADMIT_PROB[p.acuity]:
                p.outcome = "admitted"
            else:
                p.outcome = "discharged"
            
            p.departure = env.now
        else:
            p.lwbs = True
            p.departure = env.now
        
        patient_log.append(p)
    
    def arrival_generator():
        """Generate patient arrivals"""
        t = 0
        while t < duration_hours * 60:
            hour = int(t // 60) % 24
            rate = HOURLY_ARRIVAL_RATES[hour]
            
            if rate > 0:
                interarrival = rng.exponential(60 / rate)
            else:
                interarrival = 60
            
            yield env.timeout(interarrival)
            t = env.now
            
            if t >= duration_hours * 60:
                break
            
            # Sample acuity
            acuity = rng.choice(
                list(ACUITY_MIX.keys()),
                p=list(ACUITY_MIX.values())
            )
            
            p = Patient(acuity, t)
            env.process(patient_flow(p))
    
    env.process(arrival_generator())
    env.run(until=duration_hours * 60)
    
    return patient_log


def calculate_metrics(patient_log):
    """Calculate performance metrics from patient log"""
    total_patients = len(patient_log)
    
    if total_patients == 0:
        return {
            "total_patients": 0,
            "avg_wait_time": 0,
            "lwbs_rate": 0,
            "avg_los": 0
        }
    
    # Wait times (triage queue)
    wait_times = []
    for p in patient_log:
        if p.triage_start is not None and p.arrival is not None:
            wait_times.append(p.triage_start - p.arrival)
    avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0
    
    # LWBS rate
    lwbs_count = sum(1 for p in patient_log if p.lwbs)
    lwbs_rate = (lwbs_count / total_patients * 100) if total_patients > 0 else 0
    
    # Length of stay
    los_times = []
    for p in patient_log:
        if p.departure is not None and p.arrival is not None:
            los_times.append(p.departure - p.arrival)
    avg_los = sum(los_times) / len(los_times) if los_times else 0
    
    # Acuity distribution
    acuity_counts = {}
    for p in patient_log:
        acuity_counts[p.acuity] = acuity_counts.get(p.acuity, 0) + 1
    
    # Wait times by acuity
    wait_by_acuity = {}
    for p in patient_log:
        if p.triage_start is not None and p.arrival is not None:
            wait = p.triage_start - p.arrival
            if p.acuity not in wait_by_acuity:
                wait_by_acuity[p.acuity] = []
            wait_by_acuity[p.acuity].append(wait)
    
    avg_wait_by_acuity = {
        acuity: sum(times) / len(times) if times else 0
        for acuity, times in wait_by_acuity.items()
    }
    
    return {
        "total_patients": total_patients,
        "avg_wait_time": round(avg_wait, 2),
        "lwbs_rate": round(lwbs_rate, 2),
        "avg_los": round(avg_los, 2),
        "acuity_distribution": acuity_counts,
        "wait_times_by_acuity": {k: round(v, 2) for k, v in avg_wait_by_acuity.items()}
    }


#flask routes

@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')


@app.route('/animation')
def animation():
    """Serve the live animation view"""
    return render_template('animation.html')


@app.route('/api/simulate', methods=['POST'])
def simulate():
    """Run simulation with given parameters"""
    try:
        data = request.json
        
        staffing = data.get('staffing', 'weekday')
        policy = data.get('policy', 'baseline')
        duration = int(data.get('duration', 24))
        seed = int(data.get('seed', 42))
        
        # Run simulation
        patient_log = run_simulation(staffing, policy, duration, seed)
        
        # Calculate metrics
        metrics = calculate_metrics(patient_log)
        
        # Add metadata
        result = {
            "metadata": {
                "staffing": staffing,
                "policy": policy,
                "duration": duration,
                "seed": seed
            },
            "metrics": metrics,
            "hourly_arrivals": HOURLY_ARRIVAL_RATES.tolist()
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/parameters', methods=['GET'])
def get_parameters():
    """Get simulation parameters"""
    return jsonify({
        "data_source": "csv_data",
        "data_file": DATA_PATH,
        "dataset_size": len(df_clean),
        "acuity_mix": ACUITY_MIX,
        "hourly_arrivals": HOURLY_ARRIVAL_RATES.tolist(),
        "staffing": STAFFING,
        "triage_time_mean": TRIAGE_TIME_MEAN,
        "service_distributions": {
            k: {"distribution": v[0], "params": [float(p) for p in v[1]]}
            for k, v in FITTED_SERVICE_DISTRIBUTIONS.items()
        }
    })


@app.route('/api/data-info', methods=['GET'])
def get_data_info():
    """Get information about the loaded dataset"""
    stats = {
        "status": "loaded",
        "file": DATA_PATH,
        "total_records": len(df),
        "clean_records": len(df_clean),
        "removed_outliers": len(df) - len(df_clean),
        "acuity_counts": df_clean["sats"].value_counts().to_dict(),
        "mean_los": float(df_clean["los_min"].mean()),
        "median_los": float(df_clean["los_min"].median()),
        "mean_triage_time": float(df_clean["triage_duration_min"].mean()),
        "mean_arrival_rate": float(df_clean["patients_per_hour"].mean())
    }
    
    return jsonify(stats)


if __name__ == '__main__':
    print("\nED Simulation Server: http://localhost:5000\n")
    app.run(debug=True, port=5000, use_reloader=True)
