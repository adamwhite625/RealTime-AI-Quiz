package com.example.quizmaster.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.quizmaster.entity.GameSession;
import com.example.quizmaster.entity.Player;

public interface PlayerRepository extends JpaRepository<Player, Long> {
    boolean existsByGameSessionAndNickname(GameSession session, String nickname);

    List<Player> findByGameSessionId(String sessionId);

    List<Player> findTop5ByGameSessionIdOrderByScoreDesc(String sessionId);
}
