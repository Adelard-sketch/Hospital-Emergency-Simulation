# Emergency Department Simulation Dashboard

## Overview

A comprehensive web-based simulation platform for analyzing Emergency Department (ED) operations using the South African Triage Scale (SATS). This application integrates discrete event simulation with real-time data visualization to support evidence-based decision-making in healthcare operations management.

## Project Description

This simulation tool models patient flow through an Emergency Department, incorporating:
- **SATS Triage System**: Five-level acuity classification (Red, Orange, Yellow, Green, Blue)
- **Multiple Policy Scenarios**: Baseline, Fast Track, and Split Flow configurations
- **Variable Staffing Models**: Weekday and weekend resource allocation patterns
- **Real Data Integration**: Calibrated using 1,055 patient records from Kaggle Emergency Service Triage dataset

## Key Features

### Simulation Capabilities
- Discrete event simulation using SimPy framework
- Stochastic arrival patterns with time-varying rates
- Fitted service time distributions (Exponential, Gamma, Lognormal)
- Preemptive resource allocation for triage nurses
- Priority-based treatment bay assignment
- Left Without Being Seen (LWBS) modeling with patience thresholds

### Interactive Dashboard
- Real-time simulation execution via web interface
- Dynamic parameter configuration (staffing, policy, duration, random seed)
- Live performance metrics visualization
- SATS acuity distribution analysis
- Hourly arrival rate patterns
- Wait time analysis by acuity level

### Performance Metrics
- **Total Patients**: Simulated arrivals over specified duration
- **Average Wait Time**: Time from arrival to triage initiation
- **LWBS Rate**: Percentage of patients leaving before treatment
- **Average Length of Stay (LOS)**: Total time in emergency department

## Technical Architecture

### Backend (Flask + SimPy)
- **Framework**: Flask 3.0+ web application
- **Simulation Engine**: SimPy 4.1+ discrete event simulation
- **Data Processing**: Pandas for data manipulation and analysis
- **Statistical Modeling**: SciPy for distribution fitting and sampling
- **API Design**: RESTful endpoints for simulation execution and parameter retrieval

### Frontend (HTML5 + JavaScript)
- **Interface**: Responsive single-page application
- **Visualization**: Custom D3-style bar charts with dynamic rendering
- **Styling**: Modern CSS with gradient design system
- **Interactivity**: Asynchronous API calls with real-time updates

### Data Pipeline
```
Kaggle Dataset → Data Cleaning → Distribution Fitting → Simulation Parameters → SimPy Model → Results → Dashboard
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Modern web browser (Chrome, Firefox, Edge, Safari)

### Setup Instructions

1. **Clone or download the repository**
   ```bash
   cd ED-Simulation-Dashboard
   ```

2. **Install required dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify data file location**
   - Ensure `emergency-service-triage-application/data.csv` exists
   - Dataset: 1,267 records (1,055 after cleaning)

4. **Launch the application**
   ```bash
   python app.py
   ```
   
   Or use the quick start script:
   ```bash
   start.bat
   ```

5. **Access the dashboard**
   - Open browser and navigate to: `http://localhost:5000`
   - Dashboard will display data source status in header badge

## Usage Guide

### Running Simulations

1. **Configure Parameters**
   - **Staffing Level**: Select weekday (3 nurses, 12 bays) or weekend (2 nurses, 8 bays)
   - **Policy**: Choose baseline, fast track (Green), or split flow (Yellow+Green)
   - **Duration**: Set simulation time horizon (1-168 hours)
   - **Random Seed**: Specify seed for reproducibility (default: 42)

2. **Execute Simulation**
   - Click "Run simulation" button
   - Monitor progress indicator
   - View results upon completion

3. **Analyze Results**
   - Review key performance indicators in metric cards
   - Examine acuity distribution across SATS categories
   - Analyze hourly arrival patterns
   - Compare wait times by acuity level

### Policy Comparison

To compare different operational policies:
1. Run simulation with baseline policy
2. Record performance metrics
3. Change policy parameter
4. Re-run simulation with same seed
5. Compare results across scenarios

## API Reference

### Endpoints

#### `POST /api/simulate`
Execute simulation with specified parameters.

**Request Body:**
```json
{
  "staffing": "weekday",
  "policy": "baseline",
  "duration": 24,
  "seed": 42
}
```

**Response:**
```json
{
  "metadata": {
    "staffing": "weekday",
    "policy": "baseline",
    "duration": 24,
    "seed": 42
  },
  "metrics": {
    "total_patients": 163,
    "avg_wait_time": 0.06,
    "lwbs_rate": 5.41,
    "avg_los": 66.59,
    "acuity_distribution": {
      "Red": 4,
      "Orange": 27,
      "Yellow": 63,
      "Green": 69,
      "Blue": 0
    },
    "wait_times_by_acuity": {
      "Red": 0.02,
      "Orange": 0.05,
      "Yellow": 0.07,
      "Green": 0.08
    }
  },
  "hourly_arrivals": [0.5, 0.5, ..., 19.16, ...]
}
```

#### `GET /api/parameters`
Retrieve simulation configuration parameters.

**Response:**
```json
{
  "data_source": "real_data",
  "dataset_size": 1055,
  "acuity_mix": {
    "Red": 0.0152,
    "Orange": 0.1488,
    "Yellow": 0.3763,
    "Green": 0.4531,
    "Blue": 0.0066
  },
  "hourly_arrivals": [0.5, 0.5, ..., 19.16, ...],
  "staffing": {
    "weekday": {"triage_nurses": 3, "treatment_bays": 12},
    "weekend": {"triage_nurses": 2, "treatment_bays": 8}
  },
  "triage_time_mean": 5.88
}
```

#### `GET /api/data-info`
Get information about loaded dataset.

**Response:**
```json
{
  "status": "loaded",
  "file": "emergency-service-triage-application/data.csv",
  "total_records": 1267,
  "clean_records": 1055,
  "removed_outliers": 212,
  "acuity_counts": {
    "Red": 16,
    "Orange": 157,
    "Yellow": 397,
    "Green": 478,
    "Blue": 7
  },
  "mean_los": 295.52,
  "median_los": 272.0,
  "mean_triage_time": 5.88,
  "mean_arrival_rate": 7.59
}
```

## Project Structure

```
Group11_Final_Project/
├── app.py                                    # Flask backend with SimPy simulation
├── templates/
│   └── index.html                            # Web dashboard interface
├── emergency-service-triage-application/
│   └── data.csv                              # Patient records dataset
├── requirements.txt                          # Python dependencies
├── start.bat                                 # Windows quick start script
├── README.md                                 # Project documentation
├── Group11_Project.ipynb                     # Jupyter notebook analysis
├── Group11_Ethics Note.pdf                   # Ethics documentation
├── Group11_Input Modeling & Data Report.pdf  # Data analysis report
├── Group11_Results & Policy Comparison Report.pdf  # Results analysis
└── Group11_Project Presentation.pptx         # Project presentation
```

## Data Source

**Dataset**: Emergency Service Triage Application  
**Source**: Kaggle (ilkeryildiz/emergency-service-triage-application)  
**Records**: 1,267 total (1,055 after cleaning)  
**Variables**: Demographics, vital signs, KTAS scores, disposition, length of stay  
**Preprocessing**: Outlier removal (LOS > 1440 min), missing value imputation, KTAS→SATS mapping

## Simulation Parameters

### Acuity Mix (from real data)
- Red (Critical): 1.5%
- Orange (Very Urgent): 14.9%
- Yellow (Urgent): 37.6%
- Green (Less Urgent): 45.3%
- Blue (Deceased): 0.7%

### Arrival Patterns
- Time-varying Poisson process
- Bell curve distribution (peak at 17:00)
- Mean rate: 7.59 patients/hour
- Peak rate: 19.16 patients/hour

### Service Time Distributions
- Red: Exponential (μ = 59.1 min)
- Orange: Lognormal (σ = 0.88, μ = 48.2 min)
- Yellow: Lognormal (σ = 0.92, μ = 39.9 min)
- Green: Lognormal (σ = 1.01, μ = 28.5 min)
- Blue: Exponential (μ = 45.0 min)

### Patience Thresholds (LWBS)
**Triage Queue:**
- Red: 2 min, Orange: 10 min, Yellow: 30 min, Green: 60 min, Blue: ∞

**Treatment Queue:**
- Red: 15 min, Orange: 60 min, Yellow: 120 min, Green: 240 min, Blue: ∞

## Troubleshooting

### Common Issues

**Issue**: Port 5000 already in use  
**Solution**: Terminate conflicting process or modify port in `app.py`

**Issue**: Module not found errors  
**Solution**: Reinstall dependencies with `pip install --upgrade -r requirements.txt`

**Issue**: Data file not found warning  
**Solution**: Verify `emergency-service-triage-application/data.csv` exists in project directory

**Issue**: Simulation taking excessive time  
**Solution**: Reduce duration parameter or check for infinite loops in patient flow logic

**Issue**: Browser not displaying dashboard  
**Solution**: Clear browser cache (Ctrl+F5) and verify Flask server is running

## Development

### Customization Options

**Modify Simulation Logic** (`app.py`):
- Adjust acuity mix probabilities
- Change arrival rate patterns
- Update service time distributions
- Modify staffing configurations
- Alter LWBS patience thresholds

**Customize Dashboard** (`templates/index.html`):
- Modify color scheme and styling
- Add new visualization components
- Adjust chart dimensions and layouts
- Implement additional metrics

### Extending Functionality

Potential enhancements:
- Multiple replication analysis with confidence intervals
- Export results to CSV/Excel formats
- Side-by-side policy comparison view
- Real-time progress indicators during simulation
- Historical results database with trend analysis
- Advanced statistical analysis (ANOVA, regression)

## Dependencies

### Core Requirements
- **Flask** (3.0+): Web application framework
- **Flask-CORS** (4.0+): Cross-origin resource sharing
- **NumPy** (1.26+): Numerical computing
- **Pandas** (2.0+): Data manipulation and analysis
- **SciPy** (1.11+): Scientific computing and statistics
- **SimPy** (4.1+): Discrete event simulation

### Installation
```bash
pip install flask flask-cors numpy pandas scipy simpy
```

Or use requirements file:
```bash
pip install -r requirements.txt
```

## Authors

**Group 11 Members:**
- Daisy Kudzai Tsenesa
- Nonzuzo Sylvia Sikhosana
- Stanley Tulani Ndlovu
- Adelard Borauzima

## License

This project is developed for academic purposes as part of a university course project.

## Acknowledgments

- Dataset provided by Kaggle user ilkeryildiz
- SimPy discrete event simulation framework
- Flask web application framework
- South African Triage Scale (SATS) methodology

## Contact

For questions or issues regarding this simulation tool, please refer to the project documentation or contact the development team through the university course platform.

---

**Version**: 1.0  
**Last Updated**: April 2026  
**Status**: Production Ready
