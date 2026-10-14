package com.example.quizmaster.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;

import com.example.quizmaster.constants.SessionStatus;

import java.time.LocalDateTime;

@Entity
@Table(name = "game_sessions")
public class GameSession {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id; // Internal ID for API calls (Host uses this)

    @Column(nullable = false, unique = true, length = 6)
    private String gamePin; // The 6-digit code players use to join

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private SessionStatus status = SessionStatus.WAITING_FOR_PLAYERS;

    // Who started this session?
    @Column(nullable = false)
    private String hostId; // From jwt.getSubject()

    // Which quiz are they playing?
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "quiz_id", nullable = false)
    private Quiz quiz;

    @Column(nullable = false)
    private int currentQuestionIndex = 0; // Starts at 0 (1st question)

    private LocalDateTime currentQuestionStartTime;

    @CreationTimestamp
    private LocalDateTime createdAt;

    // Getters, Setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getGamePin() {
        return gamePin;
    }

    public void setGamePin(String gamePin) {
        this.gamePin = gamePin;
    }

    public SessionStatus getStatus() {
        return status;
    }

    public void setStatus(SessionStatus status) {
        this.status = status;
    }

    public String getHostId() {
        return hostId;
    }

    public void setHostId(String hostId) {
        this.hostId = hostId;
    }

    public Quiz getQuiz() {
        return quiz;
    }

    public void setQuiz(Quiz quiz) {
        this.quiz = quiz;
    }

    public int getCurrentQuestionIndex() {
        return currentQuestionIndex;
    }

    public void setCurrentQuestionIndex(int currentQuestionIndex) {
        this.currentQuestionIndex = currentQuestionIndex;
    }

    public LocalDateTime getCurrentQuestionStartTime() {
        return currentQuestionStartTime;
    }

    public void setCurrentQuestionStartTime(LocalDateTime currentQuestionStartTime) {
        this.currentQuestionStartTime = currentQuestionStartTime;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
