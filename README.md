# Optimising Service Meshes

This repository contains the research code and implementation for a thesis on optimizing service mesh configurations using machine learning approaches. The project explores both supervised learning and reinforcement learning techniques to automatically tune service mesh parameters for improved performance.

## Overview

Service meshes like Istio provide powerful capabilities for managing microservices communication, but optimal configuration remains challenging. This research investigates automated approaches to optimize service mesh configurations based on performance metrics and workload characteristics.

## Repository Structure

```
├── data_collection_scripts/     # Scripts for collecting performance data
│   ├── collector.py            # Main data collection script
│   └── locustfile.py          # Load testing configuration
│
├── eda_scripts/               # Exploratory Data Analysis
│   ├── eda.ipynb             # Primary EDA notebook
│   ├── eda2.ipynb            # Additional analysis
│   ├── enriched_dataset.py   # Data preprocessing utilities
│   ├── istio_performance_analysis.ipynb
│   ├── ml.ipynb              # Machine learning exploration
│   ├── model.ipynb           # Model development
│   └── xgboost.ipynb         # XGBoost implementation
│
├── supervised_learning/       # Supervised ML approach
│   ├── apply_config.py       # Configuration application script
│   ├── collect_metrics.py    # Metrics collection
│   ├── locustfile.py         # Load testing
│   ├── predict_config.py     # Configuration prediction
│   └── models/               # Trained models
│       ├── http1_model.pkl
│       ├── http2_model.pkl
│       └── timeout_model.pkl
│
├── reinforcement_learning/    # RL approach
│   ├── apply_config.py       # Configuration application
│   ├── collect_metrics.py    # Metrics collection
│   ├── istio_env.py          # RL environment definition
│   ├── locustfile.py         # Load testing
│   ├── reward_logger.py      # Reward tracking
│   ├── run_rl_agent.py       # Agent execution
│   ├── train_ppo.py          # PPO training script
│   ├── visualize.ipynb       # Results visualization
│   └── model/                # RL model artifacts
│       ├── ppo_istio.zip
│       ├── testing_rl_trace.csv
│       └── training_rl_trace.csv
│
└── kubernetes_manifest/       # Kubernetes deployment files
    ├── multi_app_demo.yaml           # Multi-service application
    ├── multi_app_istio_config.yaml   # Istio configuration
    └── prometheus.yaml               # Monitoring setup
```

## Approaches

### 1. Supervised Learning
The supervised learning approach uses historical performance data to train models that can predict optimal service mesh configurations. Key features:
- Multiple models for different configuration parameters (HTTP/1, HTTP/2, timeouts)
- Feature engineering based on workload characteristics
- Performance metric prediction and optimization

### 2. Reinforcement Learning
The reinforcement learning approach treats service mesh optimization as a sequential decision-making problem:
- Custom Istio environment implementation
- PPO (Proximal Policy Optimization) agent
- Real-time adaptation to changing workload conditions
- Reward function based on performance metrics

## Test Applications

### Multi-Service Application
Uses the Google microservices demo ([Online Boutique](https://github.com/GoogleCloudPlatform/microservices-demo)) deployed via `kubernetes_manifest/multi_app_demo.yaml` for comprehensive testing of service mesh configurations.

### Istio BookInfo Application
Utilizes the standard Istio BookInfo sample application for baseline comparisons and validation.

## Data Collection

Performance data is collected using:
- **Locust**: For load testing and workload simulation
- **Prometheus**: For metrics collection and monitoring
- **Custom collectors**: For Istio-specific configuration and performance data

## Getting Started

### Prerequisites
- Kubernetes cluster with Istio installed
- Python 3.8+

### Installation
1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Quick Start
1. Deploy the test applications using the Kubernetes manifests
2. Configure Prometheus for metrics collection
3. Run data collection scripts to gather baseline performance data
4. Train models using either supervised or reinforcement learning approaches
5. Apply optimized configurations and validate improvements


## Results

Both supervised and reinforcement learning approaches demonstrate significant improvements in service mesh performance compared to default configurations. Detailed analysis and results are available in the EDA notebooks and model output files.

