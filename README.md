# 🤖 Pokémon-Sticky-Bot

Ein professioneller Discord Bot für automatische Sticky Messages mit moderner GUI und sicherer Authentifizierung.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3+-blue.svg)](https://discordpy.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🎯 Was macht der Bot?

**Sticky-Bot** erstellt automatische Nachrichten, die nach jeder neuen Nachricht in einem Channel wieder erscheinen. Perfekt für:
- **Server-Regeln** die immer sichtbar bleiben
- **Willkommensnachrichten** für neue Mitglieder  
- **Event-Ankündigungen** die nicht untergehen
- **Wichtige Informationen** die permanent präsent sein sollen

### ✨ Besondere Features

🎮 **Management-Kontrollzentrum** - Vollständige GUI mit 3 Tabs für Bot-Kontrolle  
🎨 **Zufällige Pokémon-Bilder** - Jede Sticky Message bekommt ein anderes Pokémon-Artwork  
⏰ **Intelligentes Timing** - Verhindert Spam durch einstellbare Verzögerungen  
🎭 **Schöne Embeds** - Rich-Text Nachrichten mit Titel, Text, Footer und mehr  
👑 **Berechtigungssystem** - Server-isolierte Verwaltung mit Bot Master & Editoren  
🔧 **GUI-Setup** - Automatischer Setup-Dialog beim ersten Start  
🏠 **Multi-Server Support** - Verwalte mehrere Discord-Server gleichzeitig  
📦 **24h Grace Period** - Sticky Messages werden bei Bot-Kick 24h archiviert und automatisch wiederhergestellt  
🛡️ **Auto-Bereinigung** - Verwaiste Berechtigungen werden automatisch erkannt und entfernt  

## 🚀 Installation Optionen

### Option 1: Eigenen Bot erstellen (Empfohlen)
Für maximale Kontrolle und Privatsphäre:

1. **Bot herunterladen** - Lade die `StickyBot-vX.X.X.zip` aus den [Releases](https://github.com/Taku1991/Sticky-Bot/releases) herunter
2. **Entpacken und starten** - Starte `StickyBot.exe` 
3. **Token eingeben** - Der GUI-Dialog führt dich durch das Setup
4. **Fertig!** - Dein eigener Sticky-Bot ist einsatzbereit

### Option 2: Bot einladen (Schneller Start)
Falls du keinen eigenen Bot erstellen möchtest:

🤖 **[Bot einladen](https://discord.com/oauth2/authorize?client_id=1291679681984331816)** 

**Hinweis:** Bei Option 2 teilst du dir den Bot mit anderen - für volle Kontrolle verwende Option 1!

## 🎮 Das Kontrollzentrum

Nach dem Start öffnet sich das **Management-Kontrollzentrum** mit 3 Tabs:

### 📊 **Bot Status Tab**
- ▶️ **Bot starten/stoppen** mit einem Klick
- 📋 **Live-Log** mit Zeitstempel aller Bot-Aktivitäten  
- 🔄 **Neustart & Token-Änderung** Buttons
- ✅ **Echtzeit-Status** (Online/Offline/Fehler)
- 📊 **Server-Verbindungsinfo** beim Start

### 📝 **Sticky Manager Tab**  
- ➕ **Neue Sticky Messages** erstellen mit Formular-Dialog
- 📋 **Übersicht aller aktiven** Sticky Messages
- ✏️ **Ein-Klick Bearbeitung** und Löschung
- 🔄 **Live-Aktualisierung** der Liste
- 🏠 **Server & Channel Namen** anstelle von IDs

### 🏠 **Server Verwaltung Tab**
- 🌐 **Alle verbundenen Server** mit Mitglieder-/Channel-Anzahl  
- 👑 **Bot Master & Editoren** Übersicht pro Server
- 🔄 **Live-Aktualisierung** beim Tab-Wechsel
- ℹ️ **Hilfe-Dialog** mit allen Discord-Commands
- 🔒 **Server-isolierte Berechtigungen** garantiert

## 📋 Discord Bot Token bekommen

Der Setup-Dialog zeigt dir die Anleitung, aber hier nochmal:

1. **Gehe zu** [Discord Developer Portal](https://discord.com/developers/applications)
2. **"New Application"** → Name eingeben (z.B. "Mein Sticky Bot")
3. **"Bot" Tab** → "Add Bot" klicken
4. **Token kopieren** (nicht die Application ID!)
5. **"Message Content Intent"** unter "Privileged Gateway Intents" aktivieren
6. **Bot einladen** mit den nötigen Berechtigungen (siehe unten)

### 🔒 Benötigte Bot-Permissions
```
Bot Permissions Value: 75776
```
- ✅ Send Messages
- ✅ Manage Messages
- ✅ Read Message History  
- ✅ Use Slash Commands
- ✅ Embed Links

## 📋 Alle Commands

### 👑 Admin Commands (Nur Botmaster)
| Command | Parameter | Was passiert |
|---------|-----------|-------------|
| `/setup_botmaster` | - | Macht dich zum Botmaster (nur einmal möglich) |
| `/add_editor` | `@benutzer` | Gibt jemandem Bot-Rechte |
| `/remove_editor` | `@benutzer` | Entzieht jemandem Bot-Rechte |
| `/transfer_master` | `@benutzer` | Überträgt Botmaster-Rolle |
| `/list_roles` | - | Zeigt alle Berechtigungen |
| `/restore_sticky_archive` | - | Zeigt archivierte Sticky Messages an und kann sie wiederherstellen |

### 📌 Sticky Messages (Botmaster + Editoren)
| Command | Parameter | Was passiert |
|---------|-----------|-------------|
| `/set_sticky` | - | Erstellt neue Sticky Message |
| `/edit_sticky` | - | Bearbeitet Sticky Message in diesem Channel |
| `/sticky_list` | - | Zeigt alle Sticky Messages |
| `/update_sticky_time` | `sekunden` | Ändert Verzögerung (mindestens 5) |
| `/remove_sticky` | - | Löscht Sticky Message aus diesem Channel |

### ℹ️ Hilfe (Alle Nutzer)
| Command | Parameter | Was passiert |
|---------|-----------|-------------|
| `/help` | - | Zeigt alle Commands mit Erklärung |

## 🎮 So verwendest du den Bot

### Schritt 1: Bot starten  
1. **Kontrollzentrum öffnen** - Starte StickyBot.exe
2. **Bot starten** - Klicke auf "▶️ BOT STARTEN" im Bot Status Tab
3. **Status prüfen** - Warte auf "✅ Bot online" Meldung

### Schritt 2: Botmaster werden
Wechsle zu Discord und verwende:
```
/setup_botmaster
```
*Du bist jetzt der Botmaster und kannst alles verwalten*

### Schritt 3: Erste Sticky Message erstellen

**Option A: Discord Command**
```
/set_sticky
```

**Option B: GUI (Empfohlen)**
1. **Sticky Manager Tab** öffnen im Kontrollzentrum
2. **"➕ Neue Sticky Message"** klicken
3. **Server & Channel** auswählen
4. **Formular ausfüllen** und erstellen

Formular-Felder:
- **Titel** - Überschrift der Nachricht
- **Nachricht** - Haupttext  
- **Verzögerung** - Sekunden bis die Nachricht erscheint (mindestens 5)
- **Zusätzliche Infos** *(optional)* - Extra Informationen
- **Footer** *(optional)* - Text unten in der Nachricht

### Schritt 4: Fertig!
Sobald jemand in dem Channel schreibt, erscheint nach der eingestellten Zeit deine Sticky Message mit einem zufälligen Pokémon-Bild! 

## 💡 Beispiele

### Server-Regeln Sticky
```
Titel: 📜 Server Regeln
Nachricht: Bitte verhalte dich respektvoll und halte dich an unsere Regeln!
Verzögerung: 30
Zusätzliche Infos: Vollständige Regeln findest du in #regeln
Footer: Bei Fragen → @Moderatoren
```

### Willkommensnachricht  
```
Titel: 👋 Willkommen!
Nachricht: Schön, dass du da bist! Stelle dich gerne vor.
Verzögerung: 10
Zusätzliche Infos: Rolle dir eine Farbe in #rollen
Footer: Viel Spaß auf dem Server! 🎉
```

### Event-Channel
```
Titel: 🎮 Gaming-Abend
Nachricht: Jeden Freitag um 20:00 Uhr spielen wir zusammen!
Verzögerung: 60
Zusätzliche Infos: Anmeldung und Details in diesem Channel
```

## ⚙️ Wie funktioniert es?

### Automatisches System
1. **Jemand schreibt** in einem Channel mit Sticky Message
2. **Bot wartet** die eingestellte Zeit (z.B. 30 Sekunden)
3. **Alte Sticky Message** wird gelöscht (falls vorhanden)
4. **Neue Sticky Message** erscheint mit zufälligem Pokémon-Bild

### Spam-Schutz
- Mindestens **30 Sekunden Pause** zwischen Sticky Messages
- **Mindestens 5 Sekunden** Verzögerung einstellbar
- **Intelligente Erkennung** verhindert Doppel-Posts

### Pokémon-Bilder
- **1025 verschiedene Pokémon** verfügbar
- **Shiny-Versionen** werden bevorzugt
- **Hochqualitative Artwork** von der offiziellen PokéAPI
- **Automatische Auswahl** - jede Sticky Message bekommt ein anderes Bild

### Sicherheit & Isolation
- **Server-getrennte Berechtigungen** - Bot Master von Server A kann nicht Server B verwalten
- **Sichere Datenstruktur** - Jeder Server hat eigene Bot Master & Editoren
- **Discord-Integration** - Commands funktionieren nur auf dem ausführenden Server
- **Thread-sichere GUI** - Keine Konflikte zwischen Discord-Bot und Benutzeroberfläche

## 🔐 Sicherheitsfeatures

StickyBot verwendet **modernste Verschlüsselungstechnologien** um alle Bot-Daten sicher zu speichern:

### 🛡️ **AES-256 Verschlüsselung**
- **Automatisch aktiv** - Keine manuelle Konfiguration nötig
- **Hardware-spezifisch** - Daten sind nur auf diesem Computer lesbar
- **Bot-Token-basiert** - Ohne deinen Bot-Token keine Entschlüsselung möglich

### 🔒 **Was wird geschützt:**
- ✅ **Bot-Rollen** (`admin`, `editor`, `viewer`) 
- ✅ **Sticky Messages** (Titel, Nachrichten, Konfiguration)
- ✅ **🆕 Archivierte Sticky Messages** (24h Grace Period Daten)
- ✅ **Benutzer-IDs** und **Server-IDs**
- ✅ **Alle Bot-Konfigurationsdaten**

### 🔄 **Automatische Migration:**
- Beim **ersten Start** werden alte JSON-Dateien automatisch verschlüsselt
- **Neue Dateien:** `bot_roles.json.enc`, `sticky_messages.json.enc`, `archived_sticky_messages.json.enc`
- **Fallback-System** falls Verschlüsselung fehlschlägt
- **Keine Datenverluste** durch das Update

### 🛡️ **Technische Details:**
- **Algorithmus:** AES-256 mit Fernet (militärischer Standard)
- **Key-Derivation:** PBKDF2 mit 100.000 Iterationen
- **Hardware-Binding:** MAC-Adresse + Prozessor + System-Infos
- **Bibliothek:** `cryptography` (Industriestandard)

**Ergebnis:** Deine Bot-Daten sind **maximal geschützt** vor unbefugtem Zugriff! 🔐

### GUI-Features
- **Kontrollzentrum mit 3 Tabs** für übersichtliche Verwaltung
- **Live-Updates** - Status und Listen aktualisieren sich automatisch
- **Token-Verwaltung** - Sichere Ein-Zeit-Einrichtung mit Show/Hide
- **Multi-Server-Support** - Verwalte alle deine Server an einem Ort
- **Hintergrundbild-Support** - Automatische Erkennung von Bot-Icons

## 🚀 Zukünftige Features

Wir arbeiten kontinuierlich an neuen Features für StickyBot:

### 🗄️ **SQLite Datenbank Integration**
- **Ersetzt JSON-Dateien** durch professionelle Datenbank
- **Bessere Performance** bei vielen Sticky Messages
- **Advanced Queries** für komplexe Verwaltung
- **Backup & Export** Funktionen
- **Verschlüsselung bleibt** - aber in der Datenbank

### 🌍 **Mehrsprachiger Support**
- **Deutsch** ✅ (aktuell)
- **Englisch** 🔄 (in Entwicklung)
- **Französisch** 📋 (geplant)
- **Spanisch** 📋 (geplant)
- **Japanisch** 📋 (geplant)
- **Automatische Spracherkennung** basierend auf Server-Locale

### 🌐 **Web-Hosting & Cloud-Service**
- **Online Dashboard** - Bot über Website verwalten
- **24/7 Hosting** - Kein lokales Ausführen mehr nötig
- **Shared Instance** - Bot einladen ohne eigenen Token
- **Premium Features** - Erweiterte Funktionen für Unterstützer
- **Mobile App** - Verwaltung per Smartphone

### 📊 **Erweiterte Features (Roadmap)**
- **Statistiken & Analytics** - Wie oft werden Sticky Messages angezeigt
- **Custom Bilder** - Eigene Bilder statt nur Pokémon
- **Scheduled Messages** - Zeitgesteuerte Sticky Messages
- **Webhook Integration** - Verbindung zu anderen Services
- **Role-based Sticky** - Verschiedene Messages für verschiedene Rollen
- **A/B Testing** - Verschiedene Sticky Variants testen



**💡 Feature-Requests?** Schreib uns auf [Discord](https://discord.gg/pokemonhideout) oder erstelle ein [GitHub Issue](https://github.com/Taku1991/Sticky-Bot/issues)! 

## 🛡️ Robustheit & Datenschutz

### 📦 **24h Grace Period System**
StickyBot ist **extrem robust** gegen temporäre Probleme:

#### 🚨 **Was passiert bei Bot-Kick oder Problemen?**
- **📦 Automatische Archivierung** - Alle Sticky Messages werden 24h sicher gespeichert
- **🔄 Auto-Wiederherstellung** - Bei Bot-Wiedereinladung werden alle Messages automatisch wiederhergestellt  
- **📢 Benachrichtigung** - Du wirst über erfolgreiche Wiederherstellung informiert
- **🧹 Intelligente Bereinigung** - Nach 24h werden Archive automatisch gelöscht

#### 💡 **Beispiel-Szenario:**
```
1️⃣ Bot wird versehentlich gekickt
   ├─ 📦 3 Sticky Messages automatisch archiviert
   ├─ ⏰ 24h Timer startet
   └─ 💾 Daten sicher gespeichert

2️⃣ Bot wird nach 2h wieder eingeladen  
   ├─ 🔍 Archiv automatisch erkannt
   ├─ ✅ Alle 3 Messages wiederhergestellt
   ├─ 📢 Erfolgsmeldung im Channel
   └─ 🎉 Alles funktioniert wie vorher!

3️⃣ Alternative: Manuell mit `/restore_sticky_archive`
   ├─ 📊 Übersicht aller archivierten Messages
   ├─ ⏰ Verbleibende Zeit angezeigt
   └─ 🔄 Ein-Klick Wiederherstellung
```

### 🛡️ **Automatische Bereinigung**
- **👋 Member verlässt Server** - Bot-Berechtigungen automatisch entfernt
- **⚠️ Verwaiste Bot Masters** - Werden erkannt und `/setup_botmaster` wird wieder möglich
- **🧹 Periodische Bereinigung** - Abgelaufene Archive alle 6h automatisch gelöscht
- **🔄 Server-Isolation** - Probleme auf einem Server betreffen andere nicht

## ❓ Häufige Fragen

**Q: Brauche ich das Kontrollzentrum oder reichen Discord Commands?**  
A: Beides funktioniert! Das GUI ist benutzerfreundlicher, Commands sind schneller für Experten.

**Q: Kann ein Bot Master von Server A Server B verwalten?**  
A: Nein! Jeder Server hat eigene, isolierte Berechtigungen.

**Q: Muss ich jedes Mal das Token eingeben?**  
A: Nein! Das Setup läuft nur beim ersten Start. Danach wird der Token automatisch geladen.

**Q: Wie viele Sticky Messages kann ich haben?**  
A: Unbegrenzt! Eine pro Channel, aber beliebig viele Channels.

**Q: Was ist der Unterschied zwischen eigenem Bot und Bot einladen?**  
A: Eigener Bot = volle Kontrolle, eigene Daten. Geteilter Bot = schneller Start, aber gemeinsame Nutzung.

**Q: Kann ich das Pokémon-Bild ausschalten?**  
A: Nein, das ist ein festes Feature des Bots.

**Q: Was passiert, wenn ich das Kontrollzentrum schließe?**  
A: Der Bot stoppt. Für Dauerbetrieb lass das Fenster offen.

**Q: 🆕 Was passiert wenn der Bot gekickt wird oder ich den Bot Master verliere?**  
A: **Kein Problem!** Der Bot archiviert alle Sticky Messages 24h automatisch. Bei Wiedereinladung werden sie automatisch wiederhergestellt. Bei verlorenen Bot Mastern wird `/setup_botmaster` wieder verfügbar.

**Q: 🆕 Wie kann ich archivierte Sticky Messages sehen?**  
A: Verwende `/restore_sticky_archive` als Bot Master. Du siehst alle archivierten Messages mit verbleibender Zeit und kannst sie mit einem Klick wiederherstellen.

**Q: 🆕 Wie lange bleiben archivierte Daten gespeichert?**  
A: Genau 24 Stunden ab Bot-Kick. Danach werden sie automatisch und permanent gelöscht um Speicher zu sparen.

### Bot Master Problem
- **"Du bist nicht Bot Master"** - Verwende `/setup_botmaster` falls noch kein Master existiert
- **Commands funktionieren nicht** - Prüfe mit `/list_roles` deine Berechtigung
- **Alter Bot Master** - Verwende `/transfer_master` für Übertragung
- **🆕 Bot Master verlassen** - Andere können wieder `/setup_botmaster` verwenden, verwaiste Berechtigungen werden automatisch bereinigt

### Sticky Messages
- **Erscheint nicht** - Warte Verzögerung ab, prüfe "Manage Messages" Permission  
- **Wird nicht gelöscht** - Bot braucht "Manage Messages" Berechtigung
- **Falsches Bild** - Pokémon werden zufällig ausgewählt, das ist normal
- **🆕 Nach Bot-Kick weg** - Verwende `/restore_sticky_archive` zur Wiederherstellung oder lade Bot erneut ein für Auto-Restore

### 🆕 Archiv & Wiederherstellung
- **Archiv leer** - Entweder keine Messages waren vorhanden oder 24h sind abgelaufen
- **Wiederherstellung schlägt fehl** - Prüfe ob du Bot Master bist und Channels noch existieren
- **Automatik funktioniert nicht** - Prüfe Bot-Berechtigungen oder verwende `/restore_sticky_archive` manuell

## 📂 Ordner-Struktur

Nach dem Download und Entpacken:
```
StickyBot-vX.X.X/
├── StickyBot.exe                            # Hauptprogramm mit GUI-Kontrollzentrum
├── data/                                    # Bot-Daten (wird automatisch erstellt)
│   ├── sticky_messages.json.enc            # 🔐 Alle aktiven Sticky Messages (AES-256)
│   ├── archived_sticky_messages.json.enc   # 🔐 24h Archiv bei Bot-Kick (AES-256)
│   └── bot_roles.json.enc                  # 🔐 Bot Master & Editoren (AES-256)
└── README.md                               # Diese Anleitung
```

**💡 Wichtig:** Alle Dateien mit `.enc` sind **AES-256 verschlüsselt** und nur mit deinem Bot-Token lesbar!

## 📞 Support

- **Discord Server**: [discord.gg/pokemonhideout](https://discord.gg/pokemonhideout) - Für schnelle Hilfe und Community
- **GitHub Issues**: [Bug Reports & Feature Requests](https://github.com/Taku1991/Sticky-Bot/issues)
- **Hilfe im Discord**: `/help` zeigt alle Commands
- **Neueste Version**: [Releases](https://github.com/Taku1991/Sticky-Bot/releases)
- **Bot einladen**: [BOT_INVITE_LINK_PLACEHOLDER] *(wird nach Hosting hinzugefügt)*

---

**Made with ❤️ and ⚡ - Viel Spaß mit deinem Sticky-Bot! 🎉** 

## 🛠️ Verwaltung

### GUI-Verwaltung (Empfohlen)
1. **Sticky Manager Tab** - Alle Sticky Messages verwalten
2. **Server Verwaltung Tab** - Berechtigungen einsehen  
3. **Bot Status Tab** - Bot steuern und Logs einsehen

### Discord Commands
```
/add_editor @benutzername        # Editor hinzufügen
/list_roles                      # Alle Berechtigungen anzeigen
/sticky_list                     # Alle Sticky Messages
/edit_sticky                     # Bearbeiten (im aktuellen Channel)  
/update_sticky_time 15           # Verzögerung auf 15 Sekunden ändern
/remove_sticky                   # Löschen (aus aktuellem Channel)
/transfer_master @neuer_bot      # Botmaster-Rolle übertragen
/restore_sticky_archive          # 🆕 Archivierte Messages anzeigen/wiederherstellen
```

## 🔧 Problemlösung

### Kontrollzentrum
- **GUI öffnet nicht** - Prüfe ob Python/tkinter verfügbar ist, sonst Konsolen-Fallback
- **Bot startet nicht** - Überprüfe Token im Bot Status Tab
- **Tabs funktionieren nicht** - Fenster vergrößern falls Buttons abgeschnitten
- **Server werden nicht angezeigt** - Bot muss gestartet und mit Discord verbunden sein

### Bot Master Problem
- **"Du bist nicht Bot Master"** - Verwende `/setup_botmaster` falls noch kein Master existiert
- **Commands funktionieren nicht** - Prüfe mit `/list_roles` deine Berechtigung
- **Alter Bot Master** - Verwende `/transfer_master` für Übertragung
- **🆕 Bot Master verlassen** - Andere können wieder `/setup_botmaster` verwenden, verwaiste Berechtigungen werden automatisch bereinigt

### Setup-Dialog
- **Dialog erscheint nicht** - Lösche .env Datei und starte neu
- **Token ungültig** - Prüfe Copy-Paste Fehler, verwende "Show Token" Button
- **Bot reagiert nicht** - Überprüfe Bot-Permissions im Discord Developer Portal

### Sticky Messages
- **Erscheint nicht** - Warte Verzögerung ab, prüfe "Manage Messages" Permission  
- **Wird nicht gelöscht** - Bot braucht "Manage Messages" Berechtigung
- **Falsches Bild** - Pokémon werden zufällig ausgewählt, das ist normal
- **🆕 Nach Bot-Kick weg** - Verwende `/restore_sticky_archive` zur Wiederherstellung oder lade Bot erneut ein für Auto-Restore

### 🆕 Archiv & Wiederherstellung
- **Archiv leer** - Entweder keine Messages waren vorhanden oder 24h sind abgelaufen
- **Wiederherstellung schlägt fehl** - Prüfe ob du Bot Master bist und Channels noch existieren
- **Automatik funktioniert nicht** - Prüfe Bot-Berechtigungen oder verwende `/restore_sticky_archive` manuell