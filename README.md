# 🎮 QuizMaster - Real-Time Multiplayer Trivia Platform

> A scalable, event-driven backend for live quiz games inspired by Kahoot!. Built with **Spring Boot**, **WebSockets (STOMP)**, and **Keycloak**.

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![Java](https://img.shields.io/badge/Java-17%2B-orange.svg)
![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.0-green.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)

## ✨ Features

- 🔐 **OAuth2 / OpenID Connect Security** with Keycloak and role-based access control  
- 🧩 **RESTful Quiz Management APIs** for creating, managing, and exploring quizzes and questions  
- ⚡ **Real-Time Multiplayer Gameplay** using WebSocket (STOMP + SockJS) for live sessions, answers, and leaderboards  
- 🧠 **Game Session Orchestration** with player join via Game PIN, timers, scoring, and host-controlled flow  
- 🗄️ **Persistent Storage** powered by PostgreSQL with JPA / Hibernate  
- 🧪 **Built-in Headless Frontend (HTML/JS)** for rapid manual and visual testing  
- 📘 **Interactive API Documentation** via Swagger UI  

---

## 🚀 Getting Started

### Prerequisites
* Docker & Docker Compose
* Java 17+ (JDK)
* Maven

### 1. Start Infrastructure
Spin up Keycloak and PostgreSQL containers:
```bash
docker-compose up -d
```
---

## 🛠 Technology Stack
**Core**
* Java 21
* Spring Boot 3

**Data**

* Spring Data JPA
* PostgreSQL
* Hibernate

**Security**

* Spring Security
* OAuth2 Resource Server
* Keycloak

**Real-time**

* Spring WebSocket
* STOMP
* SockJS

---

## ✅ Prerequisites

Make sure you have the following installed:

* Java 21+
* Maven (or use the included `./mvnw` wrapper)
* Docker (recommended for Keycloak & PostgreSQL)

---

## 🔐 Configure Keycloak

1. **Start Keycloak**

   Access the Keycloak Admin Console:

   ```
   http://localhost:8081
   ```

   Default credentials:

   ```
   Username: admin
   Password: admin
   ```

2. **Create a Realm**

   * Realm name: `quiz-realm`

3. **Create a Client**

   * Client ID: `quiz-client`
   * Client Type: **Confidential**
   * Enable:

     * Client authentication
     * Standard flow

4. **Configure Roles**

   * Create a client role: `manage-user`
   * Assign the role to the appropriate users

5. **Copy Client Secret**

   * Navigate to **Credentials** tab of `quiz-client`
   * Copy the `Client Secret`
   * Paste it into `application.properties`:

   ```properties
   keycloak.credentials.secret=YOUR_CLIENT_SECRET
   ```

---

## ▶️ Run the Backend

From the project root:

```bash
./mvnw spring-boot:run
```

The backend will start at:

```
http://localhost:8080
```

---

## 🕹 How to Play (Visual Test Helper)

This project includes a **headless frontend** (plain HTML/JS) bundled with the backend to simulate the game UI for testing purposes.

---

### Step 1: Host Dashboard

1. Open:

   ```
   http://localhost:8080/host.html
   ```

2. Paste:

   * **Quiz UUID** (from the database)
   * **JWT Token** (generated via Postman / Keycloak)

3. Click **Create Session**

4. Copy the generated **6-digit Game PIN**

---

### Step 2: Player Join

1. Open in a new tab or mobile device:

   ```
   http://localhost:8080/player.html
   ```

2. Enter:

   * Game PIN
   * Nickname

3. Click **Join**

✅ The player name will instantly appear on the Host screen via WebSocket.

---

### Step 3: Gameplay Loop

* **Host**

  * Click **Start Game** / **Next Question**
  * Monitor real-time answer count
  * Click **Stop Timer** to reveal leaderboard

* **Players**

  * View question and countdown timer
  * Select answers in real-time

---

## 📡 API Documentation

Swagger UI is available at:

```
http://localhost:8080/swagger-ui/index.html
```

Use this to explore and test all REST APIs.

---

## 🔮 Future Roadmap

* [ ] Add more APIs for quiz and session management
* [ ] Improve gameplay features (power-ups, question types, scoring rules)
* [ ] Implement reconnection & resilience logic
* [ ] Build a full-featured frontend (Web / Mobile)

---

## 📄 License

This project is provided for educational and personal development purposes.
