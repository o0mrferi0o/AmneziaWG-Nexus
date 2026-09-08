# Architecture
The GTK window is presentation and background task coordination only. `ConnectionManager` owns serialized state changes; `AWGService` reads network state. `security.py` validates profile placement and produces fixed `pkexec awg-quick` argv values. The application process is unprivileged.
