# Apollo Tyres Research and Development Project

This repository contains the Apollo Tyres Simulation Software, consisting of a React + TypeScript frontend, a Python backend, and Abaqus input files required to run tyre simulation workflows.

## Repository Structure

```text
Apollo-Tyres-Research-and-Development-Project/
│
├── Apollo-Tyres-Simulation-Software/   # React + TypeScript + Tailwind CSS frontend
├── server/                             # Python backend
└── abaqus_input/                       # Abaqus input (.inp) and related files
```

---

## Prerequisites

Ensure the following software is installed before setting up the project:

* Python 3.12
* Node.js v22.18.0
* PostgreSQL
* Abaqus Student Version
* Git

---

## Backend Setup

1. Navigate to the backend directory.

```bash
cd server
```

2. Create and activate a virtual environment (recommended).

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install the required Python packages.

```bash
pip install -r requirements.txt
```

---

## Database Setup

Create a PostgreSQL database named:

```text
apollo_tyres
```

Then initialize the database:

```bash
cd server
python -m database.py
```

---

## Running the Backend

```bash
cd server
python -m main.py
```

The backend will be available at:

* **Backend:** http://localhost:8000
* **API Documentation:** http://localhost:8000/docs

---

## Frontend Setup

Navigate to the frontend directory:

```bash
cd Apollo-Tyres-Simulation-Software
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will be available at:

* **Frontend:** http://localhost:5173

---

## Abaqus Setup

* Install **Abaqus Student Version**.
* Ensure Abaqus is properly installed and accessible from the backend.
* Place the required simulation input files inside the `abaqus_input` directory.

---

## Running the Complete Application

1. Start PostgreSQL.
2. Initialize the database (first-time setup).

```bash
cd server
python -m database.py
```

3. Start the backend.

```bash
cd server
python -m main.py
```

4. Start the frontend.

```bash
cd Apollo-Tyres-Simulation-Software
npm run dev
```

5. Open your browser and navigate to:

```
http://localhost:5173
```

---

## Project URLs

| Service           | URL                        |
| ----------------- | -------------------------- |
| Frontend          | http://localhost:5173      |
| Backend           | http://localhost:8000      |
| API Documentation | http://localhost:8000/docs |

---

## Notes

* Ensure PostgreSQL is running before starting the backend.
* Install all dependencies from `requirements.txt` before running the server.
* Abaqus Student Version must be installed for simulation execution.
* Verify that the required Abaqus input files are available in the `abaqus_input` directory before running simulations.
