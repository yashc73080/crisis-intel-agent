# crisis-intel-agent

```bash
cd backend
python coordinator/main.py
```

If using decoupled (for risk analysis)
```bash
python services/event_processor.py
```

Delete all Firestore data (for testing)
```bash
python clear_firestore.py
```