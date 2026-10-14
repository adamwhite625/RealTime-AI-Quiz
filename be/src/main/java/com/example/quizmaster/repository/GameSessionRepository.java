package com.example.quizmaster.repository;

import com.example.quizmaster.entity.GameSession;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.quizmaster.constants.SessionStatus;

public interface GameSessionRepository extends JpaRepository<GameSession, String> {
    boolean existsByGamePinAndStatusNot(String gamePin, SessionStatus status);

    Optional<GameSession> findByGamePin(String gamePin);
}
