# File Purge Docker Script

Automatisches Python-Script zum Löschen alter Dateien mit Discord-Benachrichtigungen.

## Features

✅ **Automatische Datei-Löschung** - Löscht Dateien älter als konfigurierbare Anzahl Tage  
✅ **Rekursive Verzeichnis-Prüfung** - Durchsucht alle Unterverzeichnisse  
✅ **Leere Verzeichnisse entfernen** - Löscht automatisch leere Ordner  
✅ **Discord Notifications** - Sendet Benachrichtigungen über gelöschte Dateien  
✅ **Docker Volume Support** - Funktioniert mit Docker Volumes  
✅ **Dry-Run Modus** - Testen ohne tatsächlich Dateien zu löschen  
✅ **Konfigurierbarer Timer** - Einstellen des Prüfintervalls

## Schnellstart

### 1. Repository klonen oder Dateien kopieren

```bash
git clone https://github.com/panteLx/file-purge.git
```

### 2. Konfiguration erstellen

```bash
cp .env.example .env
nano .env
```

Passen Sie die Werte in der `.env` Datei an:

```env
# Pfad zum zu überwachenden Verzeichnis (auf Ihrem Host)
PURGE_VOLUME_PATH=/pfad/zu/ihren/daten

# Maximales Alter der Dateien in Tagen
PURGE_MAX_AGE_DAYS=30

# Prüfintervall in Sekunden (3600 = 1 Stunde)
PURGE_CHECK_INTERVAL=3600

# Discord Webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Dry Run (true = keine Dateien löschen, nur simulieren)
PURGE_DRY_RUN=false
```

### 3. Discord Webhook einrichten

1. Öffnen Sie Ihren Discord Server
2. Gehe zu **Server-Einstellungen** → **Integrationen** → **Webhooks**
3. Klicken Sie auf **Neuer Webhook**
4. Geben Sie einen Namen ein (z.B. "File Purge Bot")
5. Wählen Sie den Kanal aus, in dem Benachrichtigungen erscheinen sollen
6. Kopieren Sie die **Webhook-URL**
7. Fügen Sie die URL in Ihre `.env` Datei ein

### 4. Docker Container starten

```bash
# Container bauen und starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f

# Container stoppen
docker-compose down
```

## Konfigurationsoptionen

| Variable               | Beschreibung                     | Standard | Beispiel                               |
| ---------------------- | -------------------------------- | -------- | -------------------------------------- |
| `PURGE_VOLUME_PATH`    | Host-Verzeichnis zum Überwachen  | -        | `/var/data/uploads`                    |
| `PURGE_MAX_AGE_DAYS`   | Max. Alter in Tagen vor Löschung | 30       | `7`                                    |
| `PURGE_CHECK_INTERVAL` | Prüfintervall in Sekunden        | 3600     | `86400` (24h)                          |
| `DISCORD_WEBHOOK_URL`  | Discord Webhook URL              | -        | `https://discord.com/api/webhooks/...` |
| `PURGE_DRY_RUN`        | Testmodus (keine Löschung)       | false    | `true`                                 |

## Beispiele

### Tägliche Prüfung, Dateien älter als 7 Tage löschen

```env
PURGE_VOLUME_PATH=/var/data/temp
PURGE_MAX_AGE_DAYS=7
PURGE_CHECK_INTERVAL=86400
PURGE_DRY_RUN=false
```

### Stündliche Prüfung, Dateien älter als 30 Tage (mit Dry-Run)

```env
PURGE_VOLUME_PATH=/var/data/cache
PURGE_MAX_AGE_DAYS=30
PURGE_CHECK_INTERVAL=3600
PURGE_DRY_RUN=true
```

## Logs und Monitoring

### Container Logs anzeigen

```bash
# Alle Logs
docker-compose logs

# Live-Logs (Follow-Modus)
docker-compose logs -f

# Letzte 100 Zeilen
docker-compose logs --tail=100
```

### Container Status prüfen

```bash
# Status anzeigen
docker-compose ps

# Container neu starten
docker-compose restart
```

## Discord Benachrichtigungen

Das Script sendet Discord-Nachrichten bei:

- ✅ **Start** - Wenn der Container startet
- 📊 **Purge Report** - Nach jedem Löschvorgang (wenn Dateien gelöscht wurden)
- 🛑 **Stop/Error** - Wenn der Container gestoppt wird oder ein Fehler auftritt

## Sicherheitshinweise

⚠️ **WICHTIG:**

1. **Testen Sie zuerst mit `PURGE_DRY_RUN=true`** - Überprüfen Sie die Logs, welche Dateien gelöscht würden
2. **Backup erstellen** - Erstellen Sie vor der ersten Ausführung ein Backup
3. **Richtige Zeitzone** - Das Script verwendet UTC-Zeit für Zeitstempel
4. **Dateialter** - Das Alter basiert auf der Änderungszeit (mtime) der Datei

## Troubleshooting

### Container startet nicht

```bash
# Logs prüfen
docker-compose logs

# Verzeichnis-Berechtigungen prüfen
ls -la $PURGE_VOLUME_PATH
```

### Keine Discord-Benachrichtigungen

- Webhook-URL korrekt in `.env`?
- Container neu starten: `docker-compose restart`
- Logs prüfen auf Fehler

### Dateien werden nicht gelöscht

- `PURGE_DRY_RUN` auf `false` gesetzt?
- Dateialter korrekt? (Check logs)
- Container hat Schreibrechte auf Volume?

## Entwicklung

### Lokales Testen (ohne Docker)

```bash
# Python-Umgebung einrichten
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# Umgebungsvariablen setzen
export PURGE_TARGET_DIR=/pfad/zum/testordner
export PURGE_MAX_AGE_DAYS=7
export PURGE_CHECK_INTERVAL=60
export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
export PURGE_DRY_RUN=true

# Script ausführen
python purge.py
```

## Lizenz

MIT License
