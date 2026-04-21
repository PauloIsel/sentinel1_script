# Setup

## 1) Create and activate a virtual environment

### Create a virtual enviroment:
```
python -m venv .venv
```

### Activate:
```
Powershell: .\.ven\Scripts\activate
Linux: source .venv/bin/activate
```

## 2) Install Python dependencies

```
pip install -r requirements.txt
```

## 3) Configure local environment variables

Copy .env.example to .env and adjust paths for your machine.

Required values:
- SNAP_HOME: path to SNAP installation root 

	(example: C:\Program Files\esa-snap)

- SNAP_MEMORY: Java heap passed to gpt 

	(example: 4G)

## 4) Run

python main.py

## Notes

- SNAP must be installed in your machine.
